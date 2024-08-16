from tests.utils import assert_ok, deploy_contract, send_bundle_now

def test_eth_sendTransaction7560_7712_valid(w3, wallet_contract, tx_7560):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    tx_7560.bigNonce = hex(2 ** 65) # bigger than 2**64
    res = tx_7560.send()
    rethash = res.result
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 2
    ev = wallet_contract.events.AccountExecutionEvent().get_logs()[0]
    evhash = ev.transactionHash.to_0x_hex()
    assert rethash == evhash
    assert wallet_contract.address == ev.address
    w3.eth.get_transaction(rethash)
