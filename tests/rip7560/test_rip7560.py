import pytest
from tests.rip7560.types import TransactionRIP7560

from web3.constants import ADDRESS_ZERO

from tests.single.opbanning.test_op_banning import banned_opcodes
from tests.types import RPCErrorCode
from tests.utils import (
    send_bundle_now,
    assert_rpc_error,
    to_prefixed_hex,
    deploy_contract,
    deploy_state_contract,
)


def test_eth_sendTransaction7560_valid(wallet_contract, tx_7560):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    tx_7560.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 2


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_eth_sendTransaction7560_banned_opcode(
    wallet_contract_rules, tx_7560, banned_op
):
    state_before = wallet_contract_rules.functions.state().call()
    assert state_before == 0
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.signature = to_prefixed_hex(banned_op)
    response = tx_7560.send()
    assert_rpc_error(response, response.message, RPCErrorCode.BANNED_OPCODE)
    send_bundle_now()
    state_after = wallet_contract_rules.functions.state().call()
    assert state_after == 0


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_paymaster_eth_sendTransaction7560_banned_opcode(
    wallet_contract, tx_7560, paymaster_contract_7560, banned_op
):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    tx_7560.sender = wallet_contract.address
    tx_7560.paymaster = paymaster_contract_7560.address
    tx_7560.paymasterData = to_prefixed_hex(banned_op)
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "paymaster uses banned opcode: " + banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 0


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_factory_eth_sendTransaction7560_banned_opcode(
    w3, tx_7560, factory_contract_7560, banned_op
):
    new_sender_address = factory_contract_7560.functions.getCreate2Address(
        ADDRESS_ZERO, 123, banned_op
    ).call()
    tx_7560.sender = new_sender_address
    code = w3.eth.get_code(new_sender_address)
    assert code.hex() == ""
    tx_7560.factory = factory_contract_7560.address
    tx_7560.factoryData = factory_contract_7560.functions.createAccount(
        ADDRESS_ZERO, 123, banned_op
    ).build_transaction()["data"]
    tx_7560.signature = to_prefixed_hex(banned_op)
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "factory",
        RPCErrorCode.BANNED_OPCODE,
    )
    assert_rpc_error(
        response,
        banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
    send_bundle_now()
    # no code deployed is the only check I can come up with here
    code = w3.eth.get_code(new_sender_address)
    assert code.hex() == ""
