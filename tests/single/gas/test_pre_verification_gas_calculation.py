from dataclasses import asdict
import pytest

from tests.conftest import wallet_contract
from tests.types import UserOperation, RPCRequest, CommandLineArgs
from tests.utils import (
    assert_ok,
    deploy_contract,
    send_bundle_now,
    userop_hash,
    deploy_wallet_contract,
)

pytest.skip("Slow and requires fixing", allow_module_level=True)


# perform a binary search for a minimal valid numeric value for a UserOperation field
def find_min_value_for_field(user_op, test_field_name, minimum_value, maximum_value):
    # check that maximum value is sufficient
    assert_ok(RPCRequest(method="debug_bundler_clearState").send())
    setattr(user_op, test_field_name, hex(maximum_value))
    res = user_op.send()
    if hasattr(res, "message") and res.message is not None:
        raise ValueError(
            f"providing '{test_field_name}' with maximum_value={maximum_value} should succeed but reverted with: {res.message}"
        )

    # check that minimum value is insufficient
    assert_ok(RPCRequest(method="debug_bundler_clearState").send())
    setattr(user_op, test_field_name, hex(minimum_value))
    res = user_op.send()
    if not hasattr(res, "message") or res.message is None:
        raise ValueError(
            f"providing '{test_field_name}' with minimum_value={minimum_value} should revert but it succeeded"
        )

    low = minimum_value
    high = maximum_value
    while low < high:
        mid = low + (high - low) // 2
        assert_ok(RPCRequest(method="debug_bundler_clearState").send())
        setattr(user_op, test_field_name, hex(mid))
        res = user_op.send()
        if not hasattr(res, "message") or res.message is None:
            # user operation has been accepted by the bundler
            high = mid
        else:
            # user operation has been rejected by the bundler
            low = mid + 1
    return low


dynamic_length_field_names = ["callData", "signature", "paymasterData"]
field_lengths = [0, 100, 2000]
expected_bundle_sizes = [1, 2, 5, 10, 20]

# note that currently there is no significant difference which field is the long one
# this may change with signature aggregation but for now this parametrization is unnecessary
# also note that these values are approximate
expected_min_pre_verification_gas = {
    "callData": {0: 51224, 100: 52952, 2000: 83576},
    "paymasterData": {0: 51224, 100: 52952, 2000: 83576},
    "signature": {0: 51224, 100: 52952, 2000: 83576},
}


@pytest.fixture(scope="session")
def test_simple_paymaster(w3, entrypoint_contract):
    return deploy_contract(
        w3,
        "TestSimplePaymaster",
        [entrypoint_contract.address],
        value=1 * 10**18,
    )


@pytest.mark.usefixtures("manual_bundling_mode")
@pytest.mark.parametrize("dynamic_length_field_name", dynamic_length_field_names)
@pytest.mark.parametrize("field_length", field_lengths)
def test_pre_verification_gas_calculation(
    w3,
    entrypoint_contract,
    test_simple_paymaster,
    wallet_contract,
    dynamic_length_field_name,
    field_length,
):
    RPCRequest(
        method="debug_bundler_setConfiguration",
        params=[{"expectedBundleSize": 1}],
    ).send()
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
            op.paymaster = test_simple_paymaster.address
            op.paymasterData = "0x" + "ff" * field_length
            op.paymasterPostOpGasLimit = "0xffffff"
            op.paymasterVerificationGasLimit = "0xffffff"
        case "callData":
            op.callData = "0x" + "ff" * field_length
    min_pre_verification_gas = find_min_value_for_field(op, test_field_name, 1, 200000)

    expected_pre_vg = expected_min_pre_verification_gas[dynamic_length_field_name][
        field_length
    ]
    # pylint: disable=fixme
    # todo: tighten the 'approx' parameter
    assert min_pre_verification_gas == pytest.approx(expected_pre_vg, 0.1)


# pylint: disable=fixme
# todo: parametrize this test for different bundler 'expectedBundleSize' (requires new 'debug_' RPC API)
@pytest.mark.usefixtures("manual_bundling_mode")
@pytest.mark.parametrize(
    "expected_bundle_size", expected_bundle_sizes, ids=lambda val: f"bundle_size={val}"
)
@pytest.mark.parametrize(
    "field_length", field_lengths, ids=lambda val: f"data_len={val}"
)
def test_gas_cost_estimate_close_to_reality(
    w3, entrypoint_contract, helper_contract, expected_bundle_size, field_length
):
    RPCRequest(
        method="debug_bundler_setConfiguration",
        params=[{"expectedBundleSize": expected_bundle_size}],
    ).send()
    user_op_hashes = []
    estimation = None
    for i in range(0, expected_bundle_size):
        # creating new wallets to avoid juggling the nonce field
        wallet = deploy_wallet_contract(w3)
        user_op = UserOperation(
            sender=wallet.address,
            callData=wallet.encode_abi(abi_element_identifier="setState", args=[0]),
            signature="0x" + "ff" * field_length,
            preVerificationGas="0xfffff",
            verificationGasLimit="0xfffff",
            callGasLimit="0xfffff",
        )
        if estimation is None:
            estimation = RPCRequest(
                method="eth_estimateUserOperationGas",
                params=[asdict(user_op), CommandLineArgs.entrypoint],
            ).send()

        user_op.preVerificationGas = estimation.result["preVerificationGas"]
        user_op.verificationGasLimit = estimation.result["verificationGasLimit"]
        user_op.callGasLimit = estimation.result["callGasLimit"]
        response = user_op.send()
        op_hash = userop_hash(helper_contract, user_op)
        assert response.result == op_hash
        user_op_hashes += op_hash

    send_bundle_now()

    response = {}
    actual_gas_used = 0
    for i in range(0, expected_bundle_size):
        response = RPCRequest(
            method="eth_getUserOperationReceipt",
            params=[op_hash],
        ).send()
        assert response.result["success"] is True
        actual_gas_used += int(response.result["actualGasUsed"], 16)

    gas_used_handle_ops_tx = int(response.result["receipt"]["gasUsed"], 16)
    # pylint: disable=fixme
    # todo: tighten the 'approx' parameter
    assert gas_used_handle_ops_tx == pytest.approx(actual_gas_used, 0.1)
