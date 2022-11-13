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
    userOp = UserOperation("0x0000000000000000000000000000000000000000",
                           0,
                           '',
                           '',
                           100000,
                           100000,
                           100000,
                           100000,
                           100000,
                           '',
                           '')
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
