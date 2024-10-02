from dataclasses import asdict
import pytest

from tests.types import UserOperation, RPCRequest
from tests.utils import assert_ok, deploy_contract


# create a copy of a UserOperation object while overriding a 'test_field_name' field with a 'new_value'
def set_user_op_field_value(user_op_input, test_field_name, new_value):
    user_op = asdict(user_op_input)
    user_op[test_field_name] = hex(new_value)
    return UserOperation(**user_op)


# perform a binary search for a minimal valid numeric value for a UserOperation field
def find_min_value_for_field(
        entrypoint_contract, user_op_input, test_field_name, minimum_value, maximum_value
):
    # check that maximum value is sufficient
    assert_ok(RPCRequest(method="debug_bundler_clearState").send())
    user_op = set_user_op_field_value(user_op_input, test_field_name, maximum_value)
    res = user_op.send()
    if hasattr(res, "message") and res.message is not None:
        raise ValueError(
            f"providing '{test_field_name}' with maximum_value={maximum_value} should succeed but reverted with: {res.message}"
        )

    # check that minimum value is insufficient
    assert_ok(RPCRequest(method="debug_bundler_clearState").send())
    user_op = set_user_op_field_value(user_op, test_field_name, minimum_value)
    res = user_op.send()
    if not hasattr(res, "message") or res.message is None:
        raise ValueError(
            f"providing '{test_field_name}' with minimum_value={minimum_value} should revert but it succeeded"
        )

    low = minimum_value
    high = maximum_value
    while low < high:
        mid = low + (high - low) // 2
        print(f"low:{low} / high: {high} / mid: {mid}")
        assert_ok(RPCRequest(method="debug_bundler_clearState").send())
        # operation may have been included - update nonce for the next check
        user_op = set_user_op_field_value(user_op_input, test_field_name, mid)
        user_op.nonce = hex(
            entrypoint_contract.functions.getNonce(user_op.sender, 0).call()
        )
        res = user_op.send()
        print(res)
        if not hasattr(res, "message") or res.message is None:
            # user operation has been accepted by the bundler
            high = mid
        else:
            # user operation has been rejected by the bundler
            low = mid + 1
    return low


dynamic_length_field_names = ["callData", "signature", "paymasterData"]
field_lengths = [0, 100, 2000]
# dynamic_length_field_names = ["callData"]
# field_lengths = [0]

# note that currently there is no significant difference which field is the long one
# this may change with signature aggregation but for now this parametrization is unnecessary
# also note that these values are approximate
expected_min_pre_verification_gas = {
    "callData": {0: 41536, 100: 43264, 2000: 73888},
    "paymasterData": {0: 42112, 100: 43720, 2000: 74464},
    "signature": {0: 41536, 100: 43276, 2000: 73888},
}


@pytest.mark.parametrize("dynamic_length_field_name", dynamic_length_field_names)
@pytest.mark.parametrize("field_length", field_lengths)
def test_pre_verification_gas_calculation(
        w3, entrypoint_contract, wallet_contract, dynamic_length_field_name, field_length
):
    # this field can be parametrized as well
    # however currently ERC-4337 validates all other fields on-chain so testing them is unnecessary
    test_field_name = "preVerificationGas"

    op = UserOperation(
        sender=wallet_contract.address,
        callData="0x",
        signature="0x",
    )

    match dynamic_length_field_name:
        case "signature":
            op.signature = "0x" + "ff" * field_length
        case "paymasterData":
            paymaster = deploy_contract(
                w3,
                "TestSimplePaymaster",
                [entrypoint_contract.address],
                value=1 * 10 ** 18,
            )
            op.paymaster = paymaster.address
            op.paymasterData = "0x" + "ff" * field_length
        case "callData":
            op.callData = "0x" + "ff" * field_length
    min_pre_verification_gas = find_min_value_for_field(
        entrypoint_contract, op, test_field_name, 1, 200000
    )

    expected_pre_vg = expected_min_pre_verification_gas[dynamic_length_field_name][
        field_length
    ]
    assert min_pre_verification_gas == pytest.approx(expected_pre_vg, 0.1)
