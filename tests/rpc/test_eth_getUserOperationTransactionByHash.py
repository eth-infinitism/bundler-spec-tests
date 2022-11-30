import pytest

from tests.types import RPCRequest
from tests.utils import userOpHash, assertRpcError
from .test_eth_sendUserOperation import sendUserOperation


@pytest.mark.usefixtures('sendUserOperation')
def test_eth_getUserOperationTransactionByHash(cmd_args, wallet_contract, userOp):
    response = RPCRequest(method="eth_getUserOperationTransactionByHash", params=[userOpHash(wallet_contract, userOp)]).send(cmd_args.url)
    # print('response is', response)
    # TODO test receipt better
    assert response.result['userOpHash'] == userOpHash(wallet_contract, userOp)


def test_eth_getUserOperationTransactionByHash_error(cmd_args):
    response = RPCRequest(method="eth_getUserOperationTransactionByHash", params=['']).send(cmd_args.url)
    assertRpcError(response, 'Missing/invalid userOpHash', -32601)
