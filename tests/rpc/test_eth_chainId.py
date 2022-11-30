
from tests.types import RPCRequest

def test_eth_chainId(cmd_args):
    request = RPCRequest(method="eth_chainId")
    bundler_response = request.send(cmd_args.url)
    node_response = request.send(cmd_args.ethereum_node)
    print(bundler_response, node_response)
    assert int(bundler_response.result, 16) == int(node_response.result, 16)
