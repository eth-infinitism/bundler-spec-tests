import collections
import pytest

from eth_utils import to_hex
from tests.types import UserOperation, RPCErrorCode, RPCRequest
from tests.utils import (
    assert_ok,
    fund,
    assert_rpc_error,
    get_stake_status,
    dump_mempool,
    set_reputation,
    deposit_to_undeployed_sender,
    deploy_wallet_contract,
    deploy_and_deposit,
    send_bundle_now,
    userop_hash,
)


SAME_SENDER_MEMPOOL_COUNT = 4
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 10**9
DEFAULT_MAX_FEE_PER_GAS = 5 * 10**9
MIN_PRICE_BUMP = 10


def bump_fee_by(fee, factor):
    return round((fee * (100 + factor) / 100))


def assert_error(response):
    assert_rpc_error(response, response.message, RPCErrorCode.INVALID_FIELDS)


ReplaceOpTestCase = collections.namedtuple(
    "ReplaceOpTestCase", ["rule", "bump_priority", "bump_max", "assert_func"]
)
replace_op_cases = [
    ReplaceOpTestCase("only_priority_fee_bump", MIN_PRICE_BUMP, 0, assert_error),
    ReplaceOpTestCase("only_max_fee_bump", 0, MIN_PRICE_BUMP, assert_error),
    ReplaceOpTestCase("with_same_fee", 0, 0, assert_error),
    ReplaceOpTestCase("with_less_fee", -MIN_PRICE_BUMP, -MIN_PRICE_BUMP, assert_error),
    ReplaceOpTestCase(
        "fee_bump_below_threshold", MIN_PRICE_BUMP - 1, MIN_PRICE_BUMP - 1, assert_error
    ),
    ReplaceOpTestCase(
        "fee_bump_at_threshold", MIN_PRICE_BUMP, MIN_PRICE_BUMP, assert_ok
    ),
    ReplaceOpTestCase(
        "fee_bump_above_threshold", MIN_PRICE_BUMP + 1, MIN_PRICE_BUMP + 1, assert_ok
    ),
]


@pytest.mark.parametrize("case", replace_op_cases, ids=lambda case: case.rule)
def test_bundle_replace_op(w3, manual_bundling_mode, case):
    wallet = deploy_wallet_contract(w3)
    fund(w3, wallet.address)
    calldata = wallet.encode_abi(abi_element_identifier="setState", args=[1])
    new_op = UserOperation(
        sender=wallet.address,
        nonce="0x0",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    new_priority_fee_per_gas = bump_fee_by(
        DEFAULT_MAX_PRIORITY_FEE_PER_GAS, case.bump_priority
    )
    new_max_fee_per_gas = bump_fee_by(DEFAULT_MAX_FEE_PER_GAS, case.bump_max)
    replacement_calldata = wallet.encode_abi(
        abi_element_identifier="setState", args=[2]
    )
    replacement_op = UserOperation(
        sender=wallet.address,
        nonce="0x0",
        callData=replacement_calldata,
        maxPriorityFeePerGas=hex(new_priority_fee_per_gas),
        maxFeePerGas=hex(new_max_fee_per_gas),
    )

    assert new_op.send().result
    assert dump_mempool() == [new_op]

    case.assert_func(replacement_op.send())
    assert dump_mempool() == [
        replacement_op if case.assert_func.__name__ == assert_ok.__name__ else new_op
    ]


ReputationTestCase = collections.namedtuple(
    "ReputationTestCase",
    ["ruleId", "rule_description", "stake_status", "allowed_in_mempool", "errorCode"],
)

reputations = {
    "banned": {"ops_seen": 100000, "ops_included": 1},
    "throttled": {
        "ops_seen": 120,
        "ops_included": 1,
    },  # numbers here and configuration in 'bundler.ts' are arbitrary
    "unstaked": {"ops_seen": 10, "ops_included": 1},
}

cases = [
    ReputationTestCase("GREP-010", "banned-entity-not-allowed", "banned", 0, -32504),
    ReputationTestCase(
        "GREP-020", "throttled-entity-allowed-limited-count", "throttled", 4, -32504
    ),
    ReputationTestCase(
        "UREP-010 UREP-020", "unstaked-entity-allowed-function", "unstaked", 11, -32505
    ),
]


def idfunction(case):
    # entity = re.match("TestRules(.*)", case.entity).groups()[0].lower()
    return f"{case.ruleId}-{case.rule_description}-{case.stake_status}"


@pytest.mark.skip("skipped")
@pytest.mark.usefixtures("manual_bundling_mode")
@pytest.mark.parametrize("entity", ["sender", "paymaster", "factory"])
@pytest.mark.parametrize("case", cases, ids=idfunction)
# pylint: disable-next=too-many-arguments too-many-locals
def test_mempool_reputation_rules_all_entities(
    w3, entrypoint_contract, paymaster_contract, factory_contract, entity, case
):
    wallet = deploy_wallet_contract(w3)
    factory = factory_contract.address
    factory_data = factory_contract.functions.create(
        456, "", entrypoint_contract.address
    ).build_transaction()["data"]
    # it should not matter to the bundler whether sender is deployed or not
    sender = deposit_to_undeployed_sender(
        w3, entrypoint_contract, factory_contract.address, factory_data
    )
    calldata = wallet.encode_abi(abi_element_identifier="setState", args=[1])

    assert dump_mempool() == []
    if entity == "sender":
        set_reputation(
            sender,
            ops_seen=reputations[case.stake_status]["ops_seen"],
            ops_included=reputations[case.stake_status]["ops_included"],
        )
    elif entity == "paymaster":
        set_reputation(
            paymaster_contract.address,
            ops_seen=reputations[case.stake_status]["ops_seen"],
            ops_included=reputations[case.stake_status]["ops_included"],
        )
    elif entity == "factory":
        set_reputation(
            factory_contract.address,
            ops_seen=reputations[case.stake_status]["ops_seen"],
            ops_included=reputations[case.stake_status]["ops_included"],
        )
    # add missing aggregator cases

    allowed_in_mempool = case.allowed_in_mempool

    # 'unstaked sender' has a unique reputation rule
    if entity == "sender" and case.stake_status == "unstaked":
        allowed_in_mempool = 4

    wallet_ops = []
    # fill the mempool with the allowed number of UserOps
    for i in range(allowed_in_mempool):

        paymaster = None
        paymaster_data = None
        paymaster_verification = None
        paymaster_postop = None

        if entity != "factory":
            factory_contract = deploy_and_deposit(
                w3, entrypoint_contract, "TestRulesFactory", False
            )

        if entity != "sender":
            # differentiate 'sender' address unless checking it to avoid hitting the 4 transactions limit :-(
            factory_data = factory_contract.functions.create(
                i + 123, "", entrypoint_contract.address
            ).build_transaction()["data"]
            sender = deposit_to_undeployed_sender(
                w3, entrypoint_contract, factory_contract.address, factory_data
            )

        if entity != "paymaster":
            # differentiate 'paymaster' address unless checking it
            paymaster_contract = deploy_and_deposit(
                w3, entrypoint_contract, "TestRulesPaymaster", False
            )
            paymaster = paymaster_contract.address
            # 'nothing' is a special string to pass validation
            paymaster_data = to_hex(text="nothing")
            paymaster_verification = "0x10000"
            paymaster_postop = "0x10000"

        user_op = UserOperation(
            sender=sender,
            nonce=hex(i << 64),
            callData=calldata,
            factory=factory,
            factoryData=factory_data,
            paymaster=paymaster,
            paymasterData=paymaster_data,
            paymasterVerificationGasLimit=paymaster_verification,
            paymasterPostOpGasLimit=paymaster_postop,
        )
        wallet_ops.append(user_op)
        assert_ok(user_op.send())

    assert dump_mempool() == wallet_ops
    # create a UserOperation that exceeds the mempool limit
    user_op = UserOperation(
        sender=sender,
        nonce=hex(case.allowed_in_mempool << 64),
        callData=calldata,
        factory=factory,
        factoryData=factory_data,
        paymaster=paymaster_contract.address,
        paymasterData=to_hex(text="nothing"),
        paymasterVerificationGasLimit="0x10000",
        paymasterPostOpGasLimit="0x10000",
    )
    response = user_op.send()
    assert dump_mempool() == wallet_ops
    entity_address = ""
    if entity == "sender":
        entity_address = user_op.sender
    elif entity == "paymaster":
        entity_address = user_op.paymaster
    elif entity == "factory":
        entity_address = user_op.factory
    assert_rpc_error(response, case.stake_status, case.errorCode)
    assert_rpc_error(response, entity_address, case.errorCode)


@pytest.mark.usefixtures("manual_bundling_mode")
def test_max_allowed_ops_unstaked_sender(w3, helper_contract):
    """
    UREP-010: An unstaked sender is only allowed to have SAME_SENDER_MEMPOOL_COUNT UserOperations in the mempool.
    """
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encode_abi(abi_element_identifier="setState", args=[1])
    wallet_ops = [
        UserOperation(sender=wallet.address, nonce=hex(i << 64), callData=calldata)
        for i in range(SAME_SENDER_MEMPOOL_COUNT + 1)
    ]
    for i, userop in enumerate(wallet_ops):
        userop.send()
        if i < SAME_SENDER_MEMPOOL_COUNT:
            assert dump_mempool() == wallet_ops[: i + 1]
        else:
            mempool = dump_mempool()
            assert mempool == wallet_ops[:-1]
    send_bundle_now()
    ophash = userop_hash(helper_contract, wallet_ops[0])
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash],
    ).send()
    assert response.result["userOpHash"] == ophash


@pytest.mark.usefixtures("manual_bundling_mode")
def test_max_allowed_ops_staked_sender(w3, entrypoint_contract, helper_contract):
    wallet = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", True)
    calldata = wallet.encode_abi(abi_element_identifier="setState", args=[1])
    wallet_ops = [
        UserOperation(
            sender=wallet.address, nonce=hex((i + 1) << 64), callData=calldata
        )
        for i in range(SAME_SENDER_MEMPOOL_COUNT + 1)
    ]
    for i, userop in enumerate(wallet_ops):
        userop.send()
        assert dump_mempool() == wallet_ops[: i + 1]
    assert dump_mempool() == wallet_ops
    send_bundle_now()
    ophash = userop_hash(helper_contract, wallet_ops[0])
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash],
    ).send()
    assert response.result["userOpHash"] == ophash


# STO-041
@pytest.mark.usefixtures("manual_bundling_mode")
def test_ban_user_op_access_other_ops_sender_in_bundle(
    w3, entrypoint_contract, helper_contract
):
    # wallet 2 will treat this wallet as a "token" and access associated storage
    wallet1_token = deploy_and_deposit(
        w3, entrypoint_contract, "TestFakeWalletToken", False
    )
    wallet2 = deploy_and_deposit(w3, entrypoint_contract, "TestFakeWalletToken", False)
    wallet1_token.functions.sudoSetBalance(wallet1_token.address, 10**18).transact(
        {"from": w3.eth.default_account}
    )
    wallet1_token.functions.sudoSetBalance(wallet2.address, 10**18).transact(
        {"from": w3.eth.default_account}
    )
    wallet1_token.functions.sudoSetAnotherWallet(wallet1_token.address).transact(
        {"from": w3.eth.default_account}
    )
    wallet2.functions.sudoSetAnotherWallet(wallet1_token.address).transact(
        {"from": w3.eth.default_account}
    )
    calldata1 = wallet2.address
    calldata2 = "0x"
    user_op1 = UserOperation(sender=wallet1_token.address, callData=calldata1)
    user_op2 = UserOperation(sender=wallet2.address, callData=calldata2)
    user_op1.send()
    user_op2.send()
    send_bundle_now()

    # check the UserOp2 is still in the mempool as it did nothing wrong
    assert dump_mempool() == [user_op2]

    # only UserOp1 can be included in one bundle
    ophash1 = userop_hash(helper_contract, user_op1)
    ophash2 = userop_hash(helper_contract, user_op2)

    response1 = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash1],
    ).send()
    assert response1.result["userOpHash"] == ophash1

    response2 = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash2],
    ).send()
    assert response2.result is None


# this condition is extremely similar to STO-041 but the access is in the entity and not in a 3rd contract
# which allows us to filter out such violations on their entry into the mempool
# STO-040
@pytest.mark.usefixtures("manual_bundling_mode")
def test_ban_user_sender_double_role_in_bundle(w3, entrypoint_contract):
    wallet1_and_paymaster = deploy_and_deposit(
        w3, entrypoint_contract, "TestFakeWalletPaymaster", False
    )
    wallet2 = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", True)
    user_op1 = UserOperation(sender=wallet1_and_paymaster.address, callData="0x")
    user_op2 = UserOperation(
        sender=wallet2.address, callData="0x", paymaster=wallet1_and_paymaster.address
    )

    # mempool addition order check: sender becomes paymaster
    response1 = user_op1.send()
    response2 = user_op2.send()
    assert_ok(response1)
    assert_rpc_error(
        response2,
        "is used as a sender entity in another UserOperation currently in mempool",
        RPCErrorCode.BANNED_OPCODE,
    )

    assert_ok(RPCRequest(method="debug_bundler_clearState").send())

    # mempool addition order check: paymaster becomes sender
    response2 = user_op2.send()
    response1 = user_op1.send()

    assert_ok(response2)
    assert_rpc_error(
        response1,
        "is used as a different entity in another UserOperation currently in mempool",
        RPCErrorCode.BANNED_OPCODE,
    )


# SREP-010
@pytest.mark.usefixtures("manual_bundling_mode")
def test_stake_check_in_bundler(w3, paymaster_contract, entrypoint_contract):
    response = get_stake_status(paymaster_contract.address, entrypoint_contract.address)

    assert response["stakeInfo"]["addr"].lower() == paymaster_contract.address.lower()
    assert str(response["stakeInfo"]["stake"]) == "0"
    assert str(response["stakeInfo"]["unstakeDelaySec"]) == "0"
    assert response["isStaked"] is False
    staked_paymaster = deploy_and_deposit(
        w3, entrypoint_contract, "TestRulesPaymaster", True
    )
    response = get_stake_status(staked_paymaster.address, entrypoint_contract.address)

    assert response["stakeInfo"]["addr"].lower() == staked_paymaster.address.lower()
    assert str(response["stakeInfo"]["stake"]) == "1000000000000000000"
    assert str(response["stakeInfo"]["unstakeDelaySec"]) == "2"
    assert response["isStaked"] is True
