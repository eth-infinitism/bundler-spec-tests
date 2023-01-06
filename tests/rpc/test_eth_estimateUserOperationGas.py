"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

from dataclasses import asdict
import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs, RPCErrorCode
from tests.utils import assertRpcError


@pytest.mark.parametrize("method", ["eth_estimateUserOperationGas"], ids=[""])
def test_eth_estimateUserOperationGas(userOp, schema):
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(userOp), CommandLineArgs.entryPoint],
    ).send()
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_estimateUserOperationGas_execution_revert(wallet_contract, userOp):
    userOp.callData = wallet_contract.encodeABI(fn_name="fail")
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(userOp), CommandLineArgs.entryPoint],
    ).send()
    assertRpcError(response, "test fail", RPCErrorCode.EXECUTION_REVERTED)


def test_eth_estimateUserOperationGas_simulation_revert(badSigUserOp):
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(badSigUserOp), CommandLineArgs.entryPoint],
    ).send()
    assertRpcError(response, "dead signature", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT)
