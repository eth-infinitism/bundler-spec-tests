from eth_abi.packed import encode_packed

from tests.utils import send_bundle_now


def test_eth_sendTransaction7560_7712_valid(w3, wallet_contract, nonce_manager, tx_7560):
    key = 777
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    get_nonce_call_data = encode_packed(
        ["address", "uint192"],
        [wallet_contract.address, key]
    )
    nonce_before = w3.eth.call(
        {"to": nonce_manager.address, "data": get_nonce_call_data}
    )
    assert nonce_before == encode_packed(
        ["uint192", "uint64"],
        [key, 0]
    )
    tx_7560.bigNonce = "0x" + nonce_before.hex().lstrip('0')
    print("tx_7560.bigNonce", tx_7560.bigNonce)
    res = tx_7560.send()
    rethash = res.result
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    nonce_after = w3.eth.call(
        {"to": nonce_manager.address, "data": get_nonce_call_data}
    )
    assert nonce_after == encode_packed(
        ["uint192", "uint64"],
        [key, 1]
    )
    assert state_after == 2
    # pylint: disable=fixme
    # todo: duplicate - extract to function
    # pylint: disable=duplicate-code
    ev = wallet_contract.events.AccountExecutionEvent().get_logs()[0]
    evhash = ev.transactionHash.to_0x_hex()
    assert rethash == evhash
    assert wallet_contract.address == ev.address
    w3.eth.get_transaction(rethash)
