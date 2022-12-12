import pytest
from tests.types import RPCRequest, CommandLineArgs
from jsonschema import validate, Validator


@pytest.mark.parametrize("method", ["eth_chainId"], ids=[""])
def test_eth_chainId(schema):
    request = RPCRequest(method="eth_chainId")
    bundler_response = request.send(CommandLineArgs.url)
    node_response = request.send(CommandLineArgs.ethereumNode)
    assert int(bundler_response.result, 16) == int(node_response.result, 16)
    Validator.check_schema(schema)
    validate(instance=bundler_response.result, schema=schema)
