import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs


@pytest.mark.parametrize("method", ["eth_supportedEntryPoints"], ids=[""])
def test_eth_supportedEntryPoints(schema):
    response = RPCRequest(method="eth_supportedEntryPoints").send(CommandLineArgs.url)
    supportedEPs = response.result
    assert len(supportedEPs) == 1
    assert supportedEPs[0] == CommandLineArgs.entryPoint
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)
