from tests.utils import send_bundle_now, userop_hash


def test_eth_sendUserOperation(wallet_contract, helper_contract, userop):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    response = userop.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert response.result == userop_hash(helper_contract, userop)
    assert state_after == 1111111


def test_valid_transaction():
    pass
