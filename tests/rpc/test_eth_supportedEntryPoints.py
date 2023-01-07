import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs


@pytest.mark.parametrize("method", ["eth_supportedEntryPoints"], ids=[""])
def test_eth_supportedEntryPoints(schema):
    response = RPCRequest(method="eth_supportedEntryPoints").send(CommandLineArgs.url)
    supported_entrypoints = response.result
    assert len(supported_entrypoints) == 1
    assert supported_entrypoints[0] == CommandLineArgs.entrypoint
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)
