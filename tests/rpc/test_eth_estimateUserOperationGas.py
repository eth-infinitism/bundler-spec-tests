"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

from dataclasses import asdict
import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs
from tests.utils import assertRpcError


@pytest.mark.parametrize('method', ['eth_estimateUserOperationGas'], ids=[''])
def test_eth_estimateUserOperationGas(badSigUserOp, schema):
    response = RPCRequest(method='eth_estimateUserOperationGas',
                          params=[asdict(badSigUserOp), CommandLineArgs.entryPoint]).send()
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_estimateUserOperationGas_revert(wallet_contract, badSigUserOp):
    badSigUserOp.callData = wallet_contract.encodeABI(fn_name='fail')
    response = RPCRequest(method='eth_estimateUserOperationGas',
                          params=[asdict(badSigUserOp), CommandLineArgs.entryPoint]).send()
    assertRpcError(response, 'test fail', -32500)
