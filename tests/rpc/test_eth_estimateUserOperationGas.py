"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

from dataclasses import asdict
import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest
from tests.utils import assertRpcError


@pytest.mark.parametrize('method', ['eth_estimateUserOperationGas'], ids=[''])
def test_eth_estimateUserOperationGas(cmd_args, badSigUserOp, schema):
    response = RPCRequest(method="eth_estimateUserOperationGas",
                          params=[asdict(badSigUserOp), cmd_args.entry_point]).send()
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_estimateUserOperationGas_revert(cmd_args, wallet_contract, badSigUserOp):
    badSigUserOp.callData = wallet_contract.encodeABI(fn_name='fail')
    response = RPCRequest(method="eth_estimateUserOperationGas",
                          params=[asdict(badSigUserOp), cmd_args.entry_point]).send()
    assertRpcError(response, "test fail", -32500)
