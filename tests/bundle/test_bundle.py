import pytest

from tests.types import UserOperation, RPCErrorCode, RPCRequest
from tests.utils import (
    assertRpcError,
    dumpMempool,
    deploy_wallet_contract,
    deploy_and_deposit,
    sendBundleNow,
    userOpHash,
)

allowedOpsPerUnstakedSender = 4


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
def test_max_allowed_ops_unstaked_sender(w3):
    wallet = deploy_wallet_contract(w3)
    callData = wallet.encodeABI(fn_name="setState", args=[1])
    walletOps = [
        UserOperation(sender=wallet.address, nonce=hex(i), callData=callData)
        for i in range(allowedOpsPerUnstakedSender + 1)
    ]
    for i, op in enumerate(walletOps):
        op.send()
        if i < allowedOpsPerUnstakedSender:
            assert dumpMempool() == walletOps[: i + 1]
        else:
            mempool = dumpMempool()
            assert mempool == walletOps[:-1]
    sendBundleNow()
    mempool = dumpMempool()
    assert mempool == walletOps[1:-1]
    ophash = userOpHash(wallet, walletOps[0])
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash],
    ).send()
    assert response.result["userOpHash"] == ophash


@pytest.mark.parametrize("mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clearState", "setBundlingMode")
def test_max_allowed_ops_staked_sender(w3, entrypoint_contract):
    wallet = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", True)
    callData = wallet.encodeABI(fn_name="setState", args=[1])
    walletOps = [
        UserOperation(sender=wallet.address, nonce=hex(i), callData=callData)
        for i in range(allowedOpsPerUnstakedSender + 1)
    ]
    for i, op in enumerate(walletOps):
        op.send()
        assert dumpMempool() == walletOps[: i + 1]
    assert dumpMempool() == walletOps
    sendBundleNow()
    mempool = dumpMempool()
    assert mempool == walletOps[1:]
    ophash = userOpHash(wallet, walletOps[0])
    response = RPCRequest(
        method="eth_getUserOperationReceipt",
        params=[ophash],
    ).send()
    assert response.result["userOpHash"] == ophash
