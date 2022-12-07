import pytest
from tests.types import RPCRequest
from jsonschema import validate, Validator


@pytest.mark.parametrize('method', ['eth_chainId'], ids=[''])
def test_eth_chainId(cmd_args, schema):
    request = RPCRequest(method='eth_chainId')
    bundler_response = request.send(cmd_args.url)
    node_response = request.send(cmd_args.ethereum_node)
    print(bundler_response, node_response)
    assert int(bundler_response.result, 16) == int(node_response.result, 16)
    Validator.check_schema(schema)
    validate(instance=bundler_response.result, schema=schema)
