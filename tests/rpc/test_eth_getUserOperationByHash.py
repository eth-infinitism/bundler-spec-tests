import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest, CommandLineArgs, UserOperation
from tests.utils import userop_hash, assert_rpc_error


@pytest.mark.usefixtures("send_user_operation", "send_bundle_now")
@pytest.mark.parametrize("schema_method", ["eth_getUserOperationByHash"], ids=[""])
def test_eth_getUserOperationByHash(wallet_contract, userop, schema):
    response = RPCRequest(
        method="eth_getUserOperationByHash",
        params=[userop_hash(wallet_contract, userop)],
    ).send()
    assert userop_hash(
        wallet_contract, UserOperation(**response.result["userOperation"])
    ) == userop_hash(wallet_contract, userop), "user operation mismatch"
    assert (
        response.result["entryPoint"] == CommandLineArgs.entrypoint
    ), "wrong entrypoint"
    assert response.result["blockNumber"], "no block number"
    assert response.result["blockHash"], "no block hash"
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_getUserOperationByHash_error():
    response = RPCRequest(method="eth_getUserOperationByHash", params=[""]).send()
    assert_rpc_error(response, "Missing/invalid userOpHash", -32601)
