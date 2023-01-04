import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest
from tests.utils import userOpHash, assertRpcError


@pytest.mark.usefixtures("sendUserOperation")
@pytest.mark.parametrize("method", ["eth_getUserOperationByHash"], ids=[""])
def test_eth_getUserOperationByHash(wallet_contract, userOp, schema):
    response = RPCRequest(
        method="eth_getUserOperationByHash",
        params=[userOpHash(wallet_contract, userOp)],
    ).send()
    print("response is", response)
    assert response.result["userOpHash"] == userOpHash(wallet_contract, userOp)
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_getUserOperationByHash_error():
    response = RPCRequest(method="eth_getUserOperationByHash", params=[""]).send()
    assertRpcError(response, "Missing/invalid userOpHash", -32601)
