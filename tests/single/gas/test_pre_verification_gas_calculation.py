import pytest
from eth_abi import decode

from tests.types import UserOperation, RPCRequest
from tests.utils import (
    pack_user_op,
    to_prefixed_hex,
    to_number,
    deploy_wallet_contract,
    hex_concat,
    deploy_and_deposit,
    clear_mempool,
    assert_ok,
)


def find_min(op, op_field, low, high):
    e = call_userop_with_gas_field(op, op_field, high)
    if e:
        raise ValueError(f"high {high} should be high enough, but reverts with: {e}")

    e = call_userop_with_gas_field(op, op_field, low)
    if not e:
        raise ValueError(f"low {low} should be low enough, but does not revert")

    while low < high:
        #         print("low=", low, "high=", high, "diff=", high - low)
        mid = low + (high - low) // 2
        e = call_userop_with_gas_field(op, op_field, mid)
        if e is None:
            high = mid
        else:
            low = mid + 1
    return low


field_names = ["callData", "paymasterData", "signature"]
field_lengths = [0, 100, 2000]

# note that currently there is no difference which field is big
# this may change with signature aggregation but for now this parametrization is unnecessary
expected_min_pre_verification_gas = {
    "callData": {0: 41860, 100: 42244, 2000: 50056},
    "paymasterData": {0: 41860, 100: 42244, 2000: 50056},
    "signature": {0: 41860, 100: 42244, 2000: 50056},
}


@pytest.mark.parametrize("field_name", field_names)
@pytest.mark.parametrize("field_length", field_lengths)
def test_pre_verification_gas_calculation(
    w3, wallet_contract, field_name, field_length
):

    op = UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[123]),
        signature="0x",
    )

    match field_name:
        case "signature":
            op.signature = "0x" + "ff" * field_length
        case "paymasterData":
            op.paymasterData = "0x" + "ff" * field_length
        case "callData":
            op.callData = "0x" + "ff" * field_length
    min_pre_verification_gas = find_min(op, "verificationGasLimit", 1, 200000)

    print("field=", field, "len=", len, "min_prevg=", min_pre_verification_gas)
    assert (
        min_pre_verification_gas
        == expected_min_pre_verification_gas[field_name][field_length]
    )
