import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs, UserOperation
from tests.utils import userop_hash, assert_rpc_error


@pytest.mark.usefixtures("execute_user_operation")
@pytest.mark.parametrize("schema_method", ["eth_getUserOperationByHash"], ids=[""])
def test_eth_getUserOperationByHash(helper_contract, userop, schema):
    response = RPCRequest(
        method="eth_getUserOperationByHash",
        params=[userop_hash(helper_contract, userop)],
    ).send()
    assert userop_hash(
        helper_contract, UserOperation(**response.result["userOperation"])
    ) == userop_hash(helper_contract, userop), "user operation mismatch"
    assert (
        response.result["entryPoint"] == CommandLineArgs.entrypoint
    ), "wrong entrypoint"
    assert response.result["blockNumber"], "no block number"
    assert response.result["blockHash"], "no block hash"
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_getUserOperationByHash_error():
    response = RPCRequest(method="eth_getUserOperationByHash", params=[""]).send()
    assert_rpc_error(response, "Missing/invalid userOpHash", -32602)
