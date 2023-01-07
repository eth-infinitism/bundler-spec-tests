import pytest
from jsonschema import validate, Validator

from tests.types import RPCRequest
from tests.utils import userop_hash, assert_rpc_error


@pytest.mark.usefixtures("send_user_operation", "send_bundle_now")
@pytest.mark.parametrize("schema_method", ["eth_getUserOperationReceipt"], ids=[""])
def test_eth_getUserOperationReceipt(wallet_contract, userop, w3, schema):
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[userop_hash(wallet_contract, userop)],
    ).send()
    assert response.result["userOpHash"] == userop_hash(wallet_contract, userop)
    receipt = w3.eth.get_transaction_receipt(
        response.result["receipt"]["transactionHash"]
    )
    assert response.result["receipt"]["blockHash"] == receipt["blockHash"].hex()
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


def test_eth_getUserOperationReceipt_error():
    response = RPCRequest(method="eth_getUserOperationReceipt", params=[""]).send()
    assert_rpc_error(response, "Missing/invalid userOpHash", -32601)
