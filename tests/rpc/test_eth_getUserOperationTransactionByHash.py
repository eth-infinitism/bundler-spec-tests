import pytest
from jsonschema import validate, Validator
from tests.types import RPCRequest
from tests.utils import userOpHash, assertRpcError


@pytest.mark.skip
@pytest.mark.usefixtures('sendUserOperation')
@pytest.mark.parametrize('method', ['eth_getUserOperationTransactionByHash'], ids=[''])
def test_eth_getUserOperationTransactionByHash(cmd_args, wallet_contract, userOp, schema):
    response = RPCRequest(method="eth_getUserOperationTransactionByHash", params=[userOpHash(wallet_contract, userOp)]).send(cmd_args.url)
    # print('response is', response)
    # TODO test receipt better
    assert response.result['userOpHash'] == userOpHash(wallet_contract, userOp)
    Validator.check_schema(schema)
    validate(instance=response.result, schema=schema)


@pytest.mark.skip
def test_eth_getUserOperationTransactionByHash_error(cmd_args):
    response = RPCRequest(method="eth_getUserOperationTransactionByHash", params=['']).send(cmd_args.url)
    assertRpcError(response, 'Missing/invalid userOpHash', -32601)
