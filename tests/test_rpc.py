"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
import requests
import json

from .types import UserOperation


def test_eth_supportedEntryPoints(url, entry_point):
    print(url)
    payload = {
        "method": "eth_supportedEntryPoints",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1234,
    }
    response = requests.post(url, json=payload).json()

    supportedEPs = response["result"]
    assert len(supportedEPs) == 1
    assert supportedEPs[0] == entry_point
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1234


def test_eth_sendUserOperation(url, entry_point):
    userOp = UserOperation("0x41A35CBda6052F89439793e9F34F4CD8C5F9B59D",
                           0,
                           '0x1079b7398b6efd9845c4db079e6fac8d21cf67b3ffb5b6af0000000000000000000000005fbdb2315678afecb367f032d93f642f64180aa30000000000000000000000007d0b8e62fcb610eafe6a5329cf5f69aa0b7159f30000000000000000000000000000000000000000000000000000000000000000',
                           '0x80c5c7d00000000000000000000000009fe46736679d2d9a65f0992f2272de9f3c7fa6e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000064d1f9cf0e0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000b68656c6c6f20776f726c6400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
                           22557,
                           1214740,
                           48024,
                           2321842020,
                           1500000000,
                           '0x',
                           '0x2649a5497c4c0d1e9d97892637a0af947f2ff695cb1707744c48d910fa2380a06d22829e528f7cc71c6023fc8055310ff894643ba4abef59b90f65fb5871e2b91b')
    payload = {
        "method": "eth_sendUserOperation",
        "params": [json.dumps(userOp, default=vars), entry_point],
        "jsonrpc": "2.0",
        "id": 1234,
    }
    print('userOp is', json.dumps(userOp, default=vars))
    response = requests.post(url, json=payload).json()

    print("response is", response)
    assert response["result"] == ""
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1234


def test_eth_chainId(url, chain_id):
    print(url, chain_id, type(url), type(chain_id))
    payload = {
        "method": "eth_chainId",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1234,
    }
    response = requests.post(url, json=payload).json()
    print(response)

    assert int(response["result"], 16) == int(chain_id)
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1234
