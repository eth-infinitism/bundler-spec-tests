import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest
from tests.utils import userOpHash, assertRpcError


@pytest.mark.skip
@pytest.mark.usefixtures('sendUserOperation')
@pytest.mark.parametrize('method', ['eth_getUserOperationTransactionByHash'], ids=[''])
def test_eth_getUserOperationTransactionByHash(wallet_contract, userOp, schema):
    response = RPCRequest(method="eth_getUserOperationTransactionByHash", params=[userOpHash(wallet_contract, userOp)]).send()
    # print('response is', response)
    # TODO test receipt better
    assert response.result['userOpHash'] == userOpHash(wallet_contract, userOp)
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


@pytest.mark.skip
def test_eth_getUserOperationTransactionByHash_error():
    response = RPCRequest(method="eth_getUserOperationTransactionByHash", params=['']).send()
    assertRpcError(response, 'Missing/invalid userOpHash', -32601)
