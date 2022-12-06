import pytest

from tests.types import RPCRequest
from tests.utils import userOpHash, assertRpcError
from .test_eth_sendUserOperation import sendUserOperation


@pytest.mark.usefixtures('sendUserOperation')
def test_eth_getUserOperationReceipt(cmd_args, wallet_contract, userOp, w3):
    response = RPCRequest(method="eth_getUserOperationReceipt",
                          params=[userOpHash(wallet_contract, userOp)]).send(cmd_args.url)
    # TODO test receipt better
    assert response.result['userOpHash'] == userOpHash(wallet_contract, userOp)
    receipt = w3.eth.getTransactionReceipt(response.result['receipt']['transactionHash'])
    assert response.result['receipt']['blockHash'] == receipt['blockHash'].hex()


def test_eth_getUserOperationReceipt_error(cmd_args):
    response = RPCRequest(method="eth_getUserOperationReceipt", params=['']).send(cmd_args.url)
    assertRpcError(response, 'Missing/invalid userOpHash', -32601)
