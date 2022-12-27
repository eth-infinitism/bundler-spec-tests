import pytest

from tests.types import UserOperation, RPCErrorCode
from tests.utils import assertRpcError, dumpMempool, deploy_wallet_contract


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clearState", "setBundlingMode")
def test_bundle_replace_by_fee(w3):
    wallet = deploy_wallet_contract(w3)
    callData = wallet.encodeABI(fn_name="setState", args=[1])
    lowerFeeOp = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=callData,
        maxPriorityFeePerGas=hex(10**9),
    )
    higherFeeOp = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=callData,
        maxPriorityFeePerGas=hex(10**10),
    )
    midFeeOp = UserOperation(
        sender=wallet.address,
        nonce="0x1",
        callData=callData,
        maxPriorityFeePerGas=hex(5 * 10**9),
    )

    assert lowerFeeOp.send().result
    assert dumpMempool() == [lowerFeeOp]
    assert higherFeeOp.send().result
    assert dumpMempool() == [higherFeeOp]
    assertRpcError(midFeeOp.send(), "", RPCErrorCode.INVALID_FIELDS)
    assert dumpMempool() == [higherFeeOp]


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clearState", "setBundlingMode")
def test_bundle(w3):
    wallet1 = deploy_wallet_contract(w3)
    wallet2 = deploy_wallet_contract(w3)
    callData = wallet1.encodeABI(fn_name="setState", args=[1])
    wallet1ops = [
        UserOperation(sender=wallet1.address, nonce=hex(i), callData=callData)
        for i in range(4)
    ]
    wallet2op1 = UserOperation(sender=wallet2.address, nonce="0x1", callData=callData)

    for i, op in enumerate(wallet1ops):
        print("what is i", i)
        op.send()
        assert dumpMempool() == wallet1ops[: i + 1]

    wallet2op1.send()
    assert dumpMempool() == wallet1ops + [wallet2op1]
