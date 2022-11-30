"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from dataclasses import asdict

from tests.types import RPCRequest
from tests.utils import userOpHash, assertRpcError


@pytest.fixture
def sendUserOperation(cmd_args, wallet_contract, userOp):
    test_eth_sendUserOperation(cmd_args, wallet_contract, userOp)


def test_eth_sendUserOperation(cmd_args, wallet_contract, userOp):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = RPCRequest(method="eth_sendUserOperation",
                          params=[asdict(userOp), cmd_args.entry_point]).send(cmd_args.url)
    state_after = wallet_contract.functions.state().call()
    assert response.result == userOpHash(wallet_contract, userOp)
    assert state_after == 1111111


def test_eth_sendUserOperation_revert(cmd_args, wallet_contract, badSigUserOp):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = RPCRequest(method="eth_sendUserOperation",
                          params=[asdict(badSigUserOp), cmd_args.entry_point]).send(cmd_args.url)
    # print("response is", response)
    state_after = wallet_contract.functions.state().call()
    assert state_after == 0
    assertRpcError(response, "testWallet: dead signature", -32500)
