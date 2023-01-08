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
LOWER_MAX_PRIORITY_FEE_PER_GAS = 10**9
MID_MAX_PRIORITY_FEE_PER_GAS = 10**10
HIGHER_MAX_PRIORITY_FEE_PER_GAS = 5*10**10


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_only_priority_fee_change(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    lower_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(LOWER_MAX_PRIORITY_FEE_PER_GAS),
    )
    mid_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(MID_MAX_PRIORITY_FEE_PER_GAS),
    )
    higher_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(HIGHER_MAX_PRIORITY_FEE_PER_GAS),
    )

    assert mid_fee_op.send().result
    assert dump_mempool() == [mid_fee_op]

    assert_rpc_error(lower_fee_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [mid_fee_op]
    
    assert_rpc_error(higher_fee_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [mid_fee_op]

@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_equally_increasing_max_fee(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    lower_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(LOWER_MAX_PRIORITY_FEE_PER_GAS),
    )

    mid_max_fee_per_gas = int(lower_fee_op.maxFeePerGas, 16)+(MID_MAX_PRIORITY_FEE_PER_GAS-LOWER_MAX_PRIORITY_FEE_PER_GAS)
    mid_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(MID_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(mid_max_fee_per_gas)
    )

    higher_max_fee_per_gas = int(mid_fee_op.maxFeePerGas, 16)+(HIGHER_MAX_PRIORITY_FEE_PER_GAS-MID_MAX_PRIORITY_FEE_PER_GAS)
    higher_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(HIGHER_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(higher_max_fee_per_gas)
    )

    assert mid_fee_op.send().result
    assert dump_mempool() == [mid_fee_op]

    assert_rpc_error(lower_fee_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [mid_fee_op]

    assert higher_fee_op.send().result
    assert dump_mempool() == [higher_fee_op]


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_max_allowed_ops_unstaked_sender(w3, helper_contract):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    wallet_ops = [
        UserOperation(sender=wallet.address, nonce=hex(i), callData=calldata)
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
        UserOperation(sender=wallet.address, nonce=hex(i), callData=calldata)
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
