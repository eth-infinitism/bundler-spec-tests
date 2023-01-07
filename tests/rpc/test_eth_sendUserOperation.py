"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from jsonschema import validate, Validator
from tests.types import RPCErrorCode
from tests.utils import userop_hash, assert_rpc_error, send_bundle_now


@pytest.mark.parametrize("method", ["eth_sendUserOperation"], ids=[""])
def test_eth_sendUserOperation(wallet_contract, userop, schema):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = userop.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert response.result == userop_hash(wallet_contract, userop)
    assert state_after == 1111111
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_sendUserOperation_revert(wallet_contract, bad_sig_userop):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = bad_sig_userop.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 0
    assert_rpc_error(
        response, "testWallet: dead signature", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT
    )
