import collections

import pytest
from tests.types import UserOperation, RPCErrorCode, RPCRequest
from tests.utils import (
    assert_rpc_error,
    dump_mempool,
    deploy_wallet_contract,
    deploy_and_deposit,
    send_bundle_now,
    userop_hash,
)

ALLOWED_OPS_PER_UNSTAKED_SENDER = 4
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 10**9
DEFAULT_MAX_FEE_PER_GAS = 5*10**9
MIN_PRICE_BUMP = 10

def bump_fee_by(fee, factor):
    return round((fee*(100+factor)/100))

def assert_ok(response):
    assert response.result

def assert_error(response):
    assert_rpc_error(response, response.message, RPCErrorCode.INVALID_FIELDS)

ReplaceOpTestCase = collections.namedtuple(
    "ReplaceOpTestCase", ["rule", "bump_priority", "bump_max", "assert_func"]
)
replace_op_cases = [
    ReplaceOpTestCase(
        "only_priority_fee_bump", MIN_PRICE_BUMP, 0, assert_error
    ),
    ReplaceOpTestCase(
        "only_max_fee_bump", 0, MIN_PRICE_BUMP, assert_error
    ),
    ReplaceOpTestCase(
        "with_same_fee", 0, 0, assert_error
    ),
    ReplaceOpTestCase(
        "with_less_fee", -MIN_PRICE_BUMP, -MIN_PRICE_BUMP, assert_error
    ),
    ReplaceOpTestCase(
        "fee_bump_below_threshold", MIN_PRICE_BUMP-1, MIN_PRICE_BUMP-1, assert_error
    ),
    ReplaceOpTestCase(
        "fee_bump_at_threshold", MIN_PRICE_BUMP, MIN_PRICE_BUMP, assert_ok
    ),
    ReplaceOpTestCase(
        "fee_bump_above_threshold", MIN_PRICE_BUMP+1, MIN_PRICE_BUMP+1, assert_ok
    )
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

    new_priority_fee_per_gas = bump_fee_by(DEFAULT_MAX_PRIORITY_FEE_PER_GAS, case.bump_priority)
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
    assert dump_mempool() == [replacement_op if case.assert_func.__name__ == assert_ok.__name__ else new_op]

@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_max_allowed_ops_unstaked_sender(w3, helper_contract):
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


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_max_allowed_ops_staked_sender(w3, entrypoint_contract, helper_contract):
    wallet = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", True)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    wallet_ops = [
        UserOperation(sender=wallet.address, nonce=hex((i+1) << 64), callData=calldata)
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


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_ban_user_op_access_other_ops_sender_in_bundle(w3, entrypoint_contract, helper_contract):
    # wallet 2 will treat this wallet as a "token" and access associated storage
    wallet1_token = deploy_and_deposit(w3, entrypoint_contract, "TestFakeWalletToken", False)
    wallet2 = deploy_and_deposit(w3, entrypoint_contract, "TestFakeWalletToken", False)
    wallet1_token.functions.sudoSetBalance(wallet1_token.address, 10**18).transact(
        {"from": w3.eth.accounts[0]}
    )
    wallet1_token.functions.sudoSetBalance(wallet2.address, 10**18).transact(
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

    ophash1 = userop_hash(helper_contract, user_op1)
    ophash2 = userop_hash(helper_contract, user_op2)

    response1 = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash1],
    ).send()
    assert response1.result["userOpHash"] == ophash1

    #
    response2 = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash2],
    ).send()
    assert response2.result is None
