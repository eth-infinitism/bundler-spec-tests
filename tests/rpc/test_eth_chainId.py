import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs


@pytest.mark.parametrize("schema_method", ["eth_chainId"], ids=[""])
def test_eth_chainId(schema):
    request = RPCRequest(method="eth_chainId")
    bundler_response = request.send(CommandLineArgs.url)
    node_response = request.send(CommandLineArgs.ethereum_node)
    assert int(bundler_response.result, 16) == int(node_response.result, 16)
    Validator.check_schema(schema)
    validate(instance=bundler_response.result, schema=schema)
