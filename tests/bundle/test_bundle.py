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

def bump_fee_by(fee, percentage):
    return round(fee*(100+percentage)/100)


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_only_priority_fee_bump(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    new_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    new_priority_fee_per_gas = bump_fee_by(DEFAULT_MAX_PRIORITY_FEE_PER_GAS, MIN_PRICE_BUMP)
    replacement_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(new_priority_fee_per_gas),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    assert new_op.send().result
    assert dump_mempool() == [new_op]

    assert_rpc_error(replacement_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [new_op]

@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_only_max_fee_bump(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    new_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    new_max_fee_per_gas = bump_fee_by(DEFAULT_MAX_FEE_PER_GAS, MIN_PRICE_BUMP)
    replacement_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(new_max_fee_per_gas),
    )

    assert new_op.send().result
    assert dump_mempool() == [new_op]

    assert_rpc_error(replacement_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [new_op]

@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_fee_reduction(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    new_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    new_priority_fee_per_gas = bump_fee_by(DEFAULT_MAX_PRIORITY_FEE_PER_GAS, -MIN_PRICE_BUMP)
    new_max_fee_per_gas = bump_fee_by(DEFAULT_MAX_FEE_PER_GAS, -MIN_PRICE_BUMP)
    replacement_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(new_priority_fee_per_gas),
        maxFeePerGas=hex(new_max_fee_per_gas),
    )

    assert new_op.send().result
    assert dump_mempool() == [new_op]

    assert_rpc_error(replacement_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [new_op]

@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_fee_bump_below_threshold(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    new_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    new_priority_fee_per_gas = bump_fee_by(DEFAULT_MAX_PRIORITY_FEE_PER_GAS, MIN_PRICE_BUMP-1)
    new_max_fee_per_gas = bump_fee_by(DEFAULT_MAX_FEE_PER_GAS, MIN_PRICE_BUMP-1)
    replacement_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(new_priority_fee_per_gas),
        maxFeePerGas=hex(new_max_fee_per_gas),
    )

    assert new_op.send().result
    assert dump_mempool() == [new_op]

    assert_rpc_error(replacement_op.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dump_mempool() == [new_op]

@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
def test_bundle_replace_with_fee_bump_above_threshold(w3):
    wallet = deploy_wallet_contract(w3)
    calldata = wallet.encodeABI(fn_name="setState", args=[1])
    lower_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(DEFAULT_MAX_PRIORITY_FEE_PER_GAS),
        maxFeePerGas=hex(DEFAULT_MAX_FEE_PER_GAS),
    )

    mid_priority_fee_per_gas = bump_fee_by(DEFAULT_MAX_PRIORITY_FEE_PER_GAS, MIN_PRICE_BUMP)
    mid_max_fee_per_gas = bump_fee_by(DEFAULT_MAX_FEE_PER_GAS, MIN_PRICE_BUMP)
    mid_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(mid_priority_fee_per_gas),
        maxFeePerGas=hex(mid_max_fee_per_gas)
    )

    higher_priority_fee_per_gas = bump_fee_by(mid_priority_fee_per_gas, MIN_PRICE_BUMP)
    higher_max_fee_per_gas = bump_fee_by(mid_max_fee_per_gas, MIN_PRICE_BUMP)
    higher_fee_op = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=calldata,
        maxPriorityFeePerGas=hex(higher_priority_fee_per_gas),
        maxFeePerGas=hex(higher_max_fee_per_gas)
    )

    assert lower_fee_op.send().result
    assert dump_mempool() == [lower_fee_op]

    assert mid_fee_op.send().result
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
