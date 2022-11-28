import requests
from dataclasses import asdict
from tests.types import RPCRequest
from tests.utils import is_valid_jsonrpc_response

def test_eth_chainId(cmd_args):
    payload = RPCRequest(method="eth_chainId")
    bundler_response = requests.post(cmd_args.url, json=asdict(payload)).json()
    node_response = requests.post(cmd_args.ethereum_node, json=asdict(payload)).json()
    print(bundler_response, node_response)

    is_valid_jsonrpc_response(bundler_response)
    assert int(bundler_response["result"], 16) == int(node_response["result"], 16)
