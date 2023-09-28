import collections
import operator
import pytest

from tests.types import UserOperation, RPCErrorCode, RPCRequest
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    dump_mempool,
    set_reputation,
    deposit_to_undeployed_sender,
    deploy_wallet_contract,
    deploy_and_deposit,
    send_bundle_now,
    userop_hash,
)
from eth_typing import (
    HexStr,
)
from eth_abi.packed import (
    encode_packed
)

ALLOWED_OPS_PER_UNSTAKED_SENDER = 4
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


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize("case", replace_op_cases, ids=lambda case: case.rule)
def test_bundle_replace_op(w3, case):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
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
    replacement_calldata = wallet.encodeABI(fn_name="setState", args=[2])
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
    ["ruleId", "rule_description", "stake_status", "allowed_in_mempool"]
)


reputations = {
    'banned': {'ops_seen': 100000, 'ops_included': 1},
    'throttled': {'ops_seen': 70, 'ops_included': 1},  # numbers here and configuration in 'bundler.ts' are arbitrary
    'unstaked': {'ops_seen': 0, 'ops_included': 0}
}


cases = [
    ReputationTestCase(
        'SREP-020', 'banned-entity-not-allowed', 'banned', 0
    ),
    ReputationTestCase(
        'SREP-030', 'throttled-entity-allowed-a-little', 'throttled', 4
    ),
    ReputationTestCase(
        # TODO: different allowed number for sender (SAME_UNSTAKED_ENTITY_MEMPOOL_COUNT vs SAME_SENDER_MEMPOOL_COUNT)
        'UREP-020', 'unstaked-entity-allowed-function', 'unstaked', 11
    ),
]


def idfunction(case):
    # entity = re.match("TestRules(.*)", case.entity).groups()[0].lower()
    return f"{case.ruleId}-{case.rule_description}-{case.stake_status}"


@pytest.mark.parametrize("bundling_mode", ["manual"])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
@pytest.mark.parametrize("entry", ['sender', 'paymaster', 'factory'])
@pytest.mark.parametrize("case", cases, ids=idfunction)
def test_banned_entry_not_allowed_alexf(
        w3,
        entrypoint_contract,
        paymaster_contract,
        factory_contract,
        helper_contract,
        entry,
        case
):
    wallet = deploy_wallet_contract(w3)
    initcode = (
            factory_contract.address
            + factory_contract.functions.create(
                123, "", entrypoint_contract.address
            ).build_transaction()["data"][2:]
    )
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    # it should not matter to the bundler whether sender is deployed or not
    sender = deposit_to_undeployed_sender(w3, entrypoint_contract, initcode)

    # 'nothing' is a special string to pass validation
    paymaster_and_data = '0x' + encode_packed(['address', 'string'], [paymaster_contract.address, 'nothing']).hex()

    assert dump_mempool() == []
    if entry == 'sender':
        set_reputation(sender, ops_seen=reputations[case.stake_status]['ops_seen'], ops_included=reputations[case.stake_status]['ops_included'])
    elif entry == 'paymaster':
        set_reputation(paymaster_contract.address, ops_seen=reputations[case.stake_status]['ops_seen'], ops_included=reputations[case.stake_status]['ops_included'])
    elif entry == 'factory':
        set_reputation(factory_contract.address, ops_seen=reputations[case.stake_status]['ops_seen'], ops_included=reputations[case.stake_status]['ops_included'])
    # TODO: missing aggregator cases

    wallet_ops = []
    # fill the mempool with the allowed number of UserOps
    for i in range(case.allowed_in_mempool):
        user_op = UserOperation(
            sender=sender,
            nonce=hex(i << 64),
            callData=calldata,
            initCode=initcode,
            paymasterAndData=paymaster_and_data
        )
        wallet_ops.append(user_op)
        user_op.send()

    assert dump_mempool() == wallet_ops
    # create a UserOperation that will not fit the mempool
    user_op = UserOperation(
        sender=sender,
        nonce=hex(case.allowed_in_mempool << 64),
        callData=calldata,
        initCode=initcode,
        paymasterAndData=paymaster_and_data
    )
    response = user_op.send()
    assert dump_mempool() == wallet_ops
    assert operator.contains(response.message, case.stake_status)


@pytest.mark.parametrize("bundling_mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_max_allowed_ops_unstaked_sender(w3, helper_contract, state, entry):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    wallet_ops = [
        UserOperation(sender=wallet.address, nonce=hex(i << 64), callData=calldata)
        for i in range(ALLOWED_OPS_PER_UNSTAKED_SENDER + 1)
    ]
    for i, userop in enumerate(wallet_ops):
        userop.send()
        if i < ALLOWED_OPS_PER_UNSTAKED_SENDER:
            assert dump_mempool() == wallet_ops[: i + 1]
        else:
            mempool = dump_mempool()
            assert mempool == wallet_ops[:-1]
    send_bundle_now()
    mempool = dump_mempool()
    assert mempool == wallet_ops[1:-1]
    ophash = userop_hash(helper_contract, wallet_ops[0])
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash],
    ).send()
    assert response.result["userOpHash"] == ophash


@pytest.mark.parametrize("bundling_mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_max_allowed_ops_staked_sender(w3, entrypoint_contract, helper_contract):
    wallet = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", True)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    wallet_ops = [
        UserOperation(
            sender=wallet.address, nonce=hex((i + 1) << 64), callData=calldata
        )
        for i in range(ALLOWED_OPS_PER_UNSTAKED_SENDER + 1)
    ]
    for i, userop in enumerate(wallet_ops):
        userop.send()
        assert dump_mempool() == wallet_ops[: i + 1]
    assert dump_mempool() == wallet_ops
    send_bundle_now()
    mempool = dump_mempool()
    assert mempool == wallet_ops[1:]
    ophash = userop_hash(helper_contract, wallet_ops[0])
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash],
    ).send()
    assert response.result["userOpHash"] == ophash


@pytest.mark.parametrize("bundling_mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_ban_user_op_access_other_ops_sender_in_bundle(
    w3, entrypoint_contract, helper_contract
):
    # wallet 2 will treat this wallet as a "token" and access associated storage
    wallet1_token = deploy_and_deposit(
        w3, entrypoint_contract, "TestFakeWalletToken", False
    )
    wallet2 = deploy_and_deposit(w3, entrypoint_contract, "TestFakeWalletToken", False)
    wallet1_token.functions.sudoSetBalance(wallet1_token.address, 10**18).transact(
        {"from": w3.eth.accounts[0]}
    )
    wallet1_token.functions.sudoSetBalance(wallet2.address, 10**18).transact(
        {"from": w3.eth.accounts[0]}
    )
    wallet1_token.functions.sudoSetAnotherWallet(wallet1_token.address).transact(
        {"from": w3.eth.accounts[0]}
    )
    wallet2.functions.sudoSetAnotherWallet(wallet1_token.address).transact(
        {"from": w3.eth.accounts[0]}
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
