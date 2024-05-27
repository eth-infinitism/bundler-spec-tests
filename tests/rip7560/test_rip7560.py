from tests.utils import send_bundle_now, userop_hash


def test_eth_sendTransaction7560(wallet_contract, helper_contract, tx_7560):
    state_before = wallet_contract.functions.state().call()
    assert state_before == "new"
    response = tx_7560.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == "executed"


def test_valid_transaction():
    pass
