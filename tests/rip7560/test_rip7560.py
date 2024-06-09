from tests.types import RPCErrorCode
from tests.utils import send_bundle_now, assert_rpc_error


def test_eth_sendTransaction7560(wallet_contract, tx_7560):
    state_before = wallet_contract.functions.state().call()
    assert state_before == "new"
    tx_7560.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == "executed"


def test_eth_sendTransaction7560_banned_opcode(wallet_contract_rules, tx_7560):
    state_before = wallet_contract_rules.functions.state().call()
    assert state_before == 0
    rule = "TIMESTAMP"
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.signature = "0x" + rule.encode().hex()
    response = tx_7560.send()
    assert_rpc_error(response, response.message, RPCErrorCode.BANNED_OPCODE)
    send_bundle_now()
    state_after = wallet_contract_rules.functions.state().call()
    assert state_after == 0


def test_valid_transaction():
    pass
