"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from tests.utils import userOpHash, assertRpcError
from jsonschema import validate, Validator



@pytest.mark.parametrize('method', ['eth_sendUserOperation'], ids=[''])
def test_eth_sendUserOperation(cmd_args, wallet_contract, userOp, schema):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = userOp.send(cmd_args)
    state_after = wallet_contract.functions.state().call()
    assert response.result == userOpHash(wallet_contract, userOp)
    assert state_after == 1111111
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_sendUserOperation_revert(cmd_args, wallet_contract, badSigUserOp):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = badSigUserOp.send(cmd_args)
    # print("response is", response)
    state_after = wallet_contract.functions.state().call()
    assert state_after == 0
    assertRpcError(response, "testWallet: dead signature", -32500)
