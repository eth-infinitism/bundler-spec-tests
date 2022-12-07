import pytest
from tests.types import RPCRequest
from jsonschema import validate, Validator


@pytest.mark.parametrize('method', ['eth_supportedEntryPoints'], ids=[''])
def test_eth_supportedEntryPoints(cmd_args, schema):
    response = RPCRequest(method="eth_supportedEntryPoints").send(cmd_args.url)
    supportedEPs = response.result
    assert len(supportedEPs) == 1
    assert supportedEPs[0] == cmd_args.entry_point
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)
