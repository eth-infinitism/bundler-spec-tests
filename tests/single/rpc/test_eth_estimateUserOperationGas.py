"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

from dataclasses import asdict
import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs, RPCErrorCode, UserOperation
from tests.utils import assert_rpc_error


@pytest.mark.parametrize("schema_method", ["eth_estimateUserOperationGas"], ids=[""])
def test_eth_estimateUserOperationGas(userop: UserOperation, schema):
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(userop), CommandLineArgs.entrypoint],
    ).send()
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_estimateUserOperationGas_execution_revert(
    wallet_contract, userop: UserOperation
):
    userop.callData = wallet_contract.encodeABI(fn_name="fail")
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(userop), CommandLineArgs.entrypoint],
    ).send()
    assert_rpc_error(response, "test fail", RPCErrorCode.EXECUTION_REVERTED)


def test_eth_estimateUserOperationGas_simulation_revert(bad_sig_userop: UserOperation):
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(bad_sig_userop), CommandLineArgs.entrypoint],
    ).send()
    assert_rpc_error(response, "dead signature", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT)
