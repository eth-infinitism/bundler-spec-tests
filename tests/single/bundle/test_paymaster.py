import collections
import pytest
from eth_utils import to_hex

from tests.types import UserOperation, RPCErrorCode
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    deploy_wallet_contract,
    deploy_contract,
    get_userop_max_cost,
)


# EREP-010: paymaster should have deposit to cover all userops in mempool
@pytest.mark.usefixtures("manual_bundling_mode")
def test_paymaster_deposit(w3, entrypoint_contract, paymaster_contract):
    """
    test paymaster has deposit to cover all userops in mempool.
    make paymaster deposit enough for 2 userops.
    send 2 userops.
    see that the 3rd userop is dropped.
    """
    paymaster = deploy_contract(w3, "TestRulesPaymaster", [entrypoint_contract.address])
    userops = []
    for i in range(3):
        sender = deploy_wallet_contract(w3).address
        userop = UserOperation(
            sender=sender,
            paymaster=paymaster.address,
            paymasterVerificationGasLimit=to_hex(50000),
            paymasterData=to_hex(text="nothing"),
        )
        userops.append(userop)

    sums = [get_userop_max_cost(userop) for userop in userops]
    total_cost = sum(sums)

    # deposit enough just below the total cost
    entrypoint_contract.functions.depositTo(paymaster.address).transact(
        {"from": w3.eth.default_account, "value": total_cost - 1}
    )
    for u in userops[0:-1]:
        assert_ok(u.send())

    res = userops[-1].send()
    assert_rpc_error(res, "too low", RPCErrorCode.PAYMASTER_DEPOSIT_TOO_LOW)
