from eth_abi.packed import encode_packed

from tests.types import RPCErrorCode
from tests.utils import send_bundle_now, assert_rpc_error, assert_ok


def get_nonce(w3, nonce_manager, address, key):
    get_nonce_call_data = encode_packed(["address", "uint192"], [address, key])
    return w3.eth.call({"to": nonce_manager.address, "data": get_nonce_call_data})


def pack_nonce(key, value):
    return encode_packed(["uint192", "uint64"], [key, value])


def test_eth_sendTransaction7560_7712_valid(
    w3, wallet_contract, nonce_manager, tx_7560
):
    key = 777

    state_before = wallet_contract.functions.state().call()
    nonce_before = get_nonce(w3, nonce_manager, wallet_contract.address, key)
    legacy_nonce_before = w3.eth.get_transaction_count(tx_7560.sender)
    assert state_before == 0
    assert nonce_before == pack_nonce(key, 0)
    assert legacy_nonce_before == 1

    tx_7560.nonceKey = hex(key)
    tx_7560.nonce = hex(0)
    assert_ok(tx_7560.send())
    send_bundle_now()

    state_after = wallet_contract.functions.state().call()
    nonce_after = get_nonce(w3, nonce_manager, wallet_contract.address, key)
    legacy_nonce_after = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce_after == pack_nonce(key, 1)
    assert state_after == 2
    assert legacy_nonce_after == 1


def test_eth_sendTransaction7560_7712_failed(wallet_contract, tx_7560):
    key = 777
    tx_7560.nonceKey = hex(key)
    tx_7560.nonce = hex(0)
    tx_7560.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 2

    ret = tx_7560.send()
    assert_rpc_error(
        ret,
        "rip-7712 nonce validation failed: execution reverted",
        RPCErrorCode.INVALID_INPUT,
    )
