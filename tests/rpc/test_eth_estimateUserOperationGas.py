"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
import requests
from dataclasses import asdict

from tests.types import RPCRequest
from tests.utils import is_valid_jsonrpc_response, assertRpcError, assertFieldsTypes


def test_eth_estimateUserOperationGas(cmd_args, badSigUserOp):
    payload = RPCRequest(method="eth_estimateUserOperationGas",
                         params=[asdict(badSigUserOp), cmd_args.entry_point], id=1234)
    response = requests.post(cmd_args.url, json=asdict(payload)).json()
    is_valid_jsonrpc_response(response)
    assertFieldsTypes(response['result'], ['callGasLimit', 'preVerificationGas', 'verificationGas'], [int, int, int])


def test_eth_estimateUserOperationGas_revert(cmd_args, wallet_contract, badSigUserOp):
    badSigUserOp.callData = wallet_contract.encodeABI(fn_name='fail')
    payload = RPCRequest(method="eth_estimateUserOperationGas",
                         params=[asdict(badSigUserOp), cmd_args.entry_point], id=1234)
    response = requests.post(cmd_args.url, json=asdict(payload)).json()

    print('response is', response)
    is_valid_jsonrpc_response(response)
    assertRpcError(response, "test fail", -32500)
