from dataclasses import asdict

from tests.find_min import find_min_userop_with_field
from tests.conftest import assert_ok
from tests.types import RPCErrorCode, RPCRequest, CommandLineArgs
from tests.user_operation_erc4337 import UserOperation
from tests.utils import assert_rpc_error, to_hex


def with_min_validation_gas(op):
    min = find_min_userop_with_field(
        op,
        "verificationGasLimit",
        1,
        200000,
    )
    op.verificationGasLimit = to_hex(min)
    return op


def test_normal_calldata(w3, wallet_contract, entrypoint_contract):
    call_wasteGas = wallet_contract.encode_abi(abi_element_identifier="wasteGas", args=[])
    op = with_min_validation_gas(
        UserOperation(
            sender = wallet_contract.address,
            callData = call_wasteGas,
            callGasLimit = to_hex(10_000),
            preVerificationGas=to_hex(42000),
            signature = "0x",
        ))

    assert_ok(op.send())

def test_huge_calldata_failed(w3, wallet_contract, entrypoint_contract):
    # userop has large calldata, and requires more gas as per EIP-7623
    # note that actual tx will take enough gas, but we can only count validation+10% of callGasLimit

    call_wasteGas = wallet_contract.encode_abi(abi_element_identifier="wasteGas", args=[])
    op1 = with_min_validation_gas(
        UserOperation(
        sender = wallet_contract.address,
        callData = call_wasteGas + "ff" * 1000,
        callGasLimit = to_hex(10_000),
        preVerificationGas=to_hex(42000),
        signature = "0x",
    ))
    ret = op1.send()
    assert_rpc_error(ret, "preVerificationGas", RPCErrorCode.INVALID_FIELDS)

def test_huge_calldata_with_callgas(w3, wallet_contract, entrypoint_contract):
    # large userop, but with enough callGasLimit, so that 10% is enough to pay.

    call_wasteGas = wallet_contract.encode_abi(abi_element_identifier="wasteGas", args=[])
    op1 = with_min_validation_gas(
        UserOperation(
            sender = wallet_contract.address,
            callData = call_wasteGas + "ff" * 1000,
            callGasLimit = to_hex(1_000_000),
            preVerificationGas=to_hex(42000),
            signature = "0x",
        ))
    ret = op1.send()
    assert_rpc_error(ret, "preVerificationGas", RPCErrorCode.INVALID_FIELDS)


def test_estimate_huge_calldata(w3, wallet_contract, entrypoint_contract):
    # large userop, but with enough callGasLimit, so that 10% is enough to pay.

    call_wasteGas = wallet_contract.encode_abi(abi_element_identifier="wasteGas", args=[])
    op = UserOperation(
            sender = wallet_contract.address,
            callData = call_wasteGas + "ff" * 1000,
            callGasLimit = to_hex(1_000_000),
            preVerificationGas=to_hex(42000),
            signature = "0x",
        )

    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(op), CommandLineArgs.entrypoint]
    ).send()
    print(response)

    op.verificationGasLimit = response.result['verificationGasLimit']
    op.preVerificationGas = response.result['preVerificationGas']

    assert_ok(op.send())
