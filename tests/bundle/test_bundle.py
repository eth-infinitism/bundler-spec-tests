import pytest

from tests.types import UserOperation, RPCErrorCode
from tests.utils import userOpHash, assertRpcError, dumpMempool, deploy_wallet_contract


@pytest.mark.usefixtures('clearState', 'setBundleInterval')
def test_bundle_replace_by_fee(cmd_args, w3):
    wallet = deploy_wallet_contract(cmd_args, w3)
    callData = wallet.encodeABI(fn_name='setState', args=[1])
    lowerFeeOp = UserOperation(sender=wallet.address, nonce='0x1', callData=callData, maxPriorityFeePerGas=hex(10**9))
    higherFeeOp = UserOperation(sender=wallet.address, nonce='0x1', callData=callData, maxPriorityFeePerGas=hex(10**10))
    midFeeOp = UserOperation(sender=wallet.address, nonce='0x1', callData=callData, maxPriorityFeePerGas=hex(5*10**9))

    assert lowerFeeOp.send(cmd_args).result
    assert dumpMempool(cmd_args) == [lowerFeeOp]
    assert higherFeeOp.send(cmd_args).result
    assert dumpMempool(cmd_args) == [higherFeeOp]
    assertRpcError(midFeeOp.send(cmd_args), '', RPCErrorCode.INVALID_FIELDS)
    assert dumpMempool(cmd_args) == [higherFeeOp]


@pytest.mark.skip
@pytest.mark.usefixtures('clearState', 'setBundleInterval')
def test_bundle(cmd_args, w3):
    wallet1 = deploy_wallet_contract(cmd_args, w3)
    wallet2 = deploy_wallet_contract(cmd_args, w3)
    callData = wallet1.encodeABI(fn_name='setState', args=[1])
    wallet1op1 = UserOperation(sender=wallet1.address, nonce='0x1', callData=callData)
    wallet1op2 = UserOperation(sender=wallet1.address, nonce='0x2', callData=callData)
    wallet2op1 = UserOperation(sender=wallet2.address, nonce='0x1', callData=callData)

    wallet1op1.send(cmd_args)
    print('what is wallet1op1', wallet1op1)
    assert dumpMempool(cmd_args) == [wallet1op1]
    wallet1op2.send(cmd_args)
    assert dumpMempool(cmd_args) == [wallet1op1]
    wallet2op1.send(cmd_args)
    assert dumpMempool(cmd_args) == [wallet1op2, wallet2op1]

