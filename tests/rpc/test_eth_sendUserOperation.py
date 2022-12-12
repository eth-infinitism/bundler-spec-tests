"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from tests.utils import userOpHash, assertRpcError
from tests.types import RPCErrorCode
from jsonschema import validate, Validator


@pytest.mark.parametrize("method", ["eth_sendUserOperation"], ids=[""])
def test_eth_sendUserOperation(wallet_contract, userOp, schema):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = userOp.send()
    state_after = wallet_contract.functions.state().call()
    assert response.result == userOpHash(wallet_contract, userOp)
    assert state_after == 1111111
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_sendUserOperation_revert(wallet_contract, badSigUserOp):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = badSigUserOp.send()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 0
    assertRpcError(
        response, "testWallet: dead signature", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT
    )
