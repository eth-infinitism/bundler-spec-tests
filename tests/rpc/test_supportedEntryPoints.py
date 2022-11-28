import requests
from dataclasses import asdict
from tests.types import RPCRequest
from tests.utils import is_valid_jsonrpc_response

def test_eth_supportedEntryPoints(cmd_args):
    print(cmd_args)
    payload = RPCRequest(method="eth_supportedEntryPoints", id=1234)
    response = requests.post(cmd_args.url, json=asdict(payload)).json()

    supportedEPs = response["result"]
    assert len(supportedEPs) == 1
    assert supportedEPs[0] == cmd_args.entry_point
    is_valid_jsonrpc_response(response)
