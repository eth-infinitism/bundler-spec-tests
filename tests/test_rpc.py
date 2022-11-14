"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
import requests
import json
from dataclasses import asdict

from .types import UserOperation
from .types import RPCRequest


def test_eth_supportedEntryPoints(cmd_args):
    print(cmd_args)
    payload = RPCRequest(method="eth_supportedEntryPoints", id=1234)
    response = requests.post(cmd_args.url, json=asdict(payload)).json()

    supportedEPs = response["result"]
    assert len(supportedEPs) == 1
    assert supportedEPs[0] == cmd_args.entry_point
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1234


def test_eth_sendUserOperation(cmd_args):
    userOp = UserOperation(
        "0x41A35CBda6052F89439793e9F34F4CD8C5F9B59D",
        hex(0),
        '0x1079b7398b6efd9845c4db079e6fac8d21cf67b3ffb5b6af0000000000000000000000005fbdb2315678afecb367f032d93f642f64180aa30000000000000000000000007d0b8e62fcb610eafe6a5329cf5f69aa0b7159f30000000000000000000000000000000000000000000000000000000000000000',
        '0x80c5c7d00000000000000000000000009fe46736679d2d9a65f0992f2272de9f3c7fa6e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000064d1f9cf0e0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000b68656c6c6f20776f726c6400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
        hex(22557),
        hex(1214740),
        hex(48024),
        hex(2321842020),
        hex(1500000000),
        '0x',
        '0x2649a5497c4c0d1e9d97892637a0af947f2ff695cb1707744c48d910fa2380a06d22829e528f7cc71c6023fc8055310ff894643ba4abef59b90f65fb5871e2b91b')
    payload = RPCRequest(method="eth_sendUserOperation", params=[json.dumps(userOp, default=vars), cmd_args.entry_point], id=1234)
    print('userOp is', json.dumps(asdict(userOp), default=vars))
    response = requests.post(cmd_args.url, json=asdict(payload)).json()

    print("response is", response)
    assert response["result"] == ""
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1234


def test_eth_chain_id(cmd_args):
    payload = RPCRequest(method="eth_chainId", id=1234)
    bundler_response = requests.post(cmd_args.url, json=asdict(payload)).json()
    node_response = requests.post(cmd_args.ethereum_node, json=asdict(payload)).json()
    print(bundler_response, node_response)

    assert int(bundler_response["result"], 16) == int(node_response["result"], 16)
    assert bundler_response["jsonrpc"] == "2.0"
    assert bundler_response["id"] == 1234


def is_valid_jsonrpc_response(response):
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1234

