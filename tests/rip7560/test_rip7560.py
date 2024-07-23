import pytest

from web3.constants import ADDRESS_ZERO

from tests.single.opbanning.test_op_banning import banned_opcodes
from tests.types import RPCErrorCode
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    fund,
    send_bundle_now,
    to_prefixed_hex, deploy_contract,
)


def test_eth_sendTransaction7560_valid(w3, wallet_contract, tx_7560):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    nonce = w3.eth.get_transaction_count(tx_7560.sender)
    # created contract has nonce==1
    assert nonce == 1
    tx_7560.send()
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 2
    assert nonce + 1 == w3.eth.get_transaction_count(tx_7560.sender), "nonce not incremented"


def test_eth_sendTransaction7560_valid_with_factory(
        w3, tx_7560
):
    factory = deploy_contract(w3, "rip7560/TestAccountFactory")

    create_account_func = factory.functions.createAccount(1)

    tx_7560.sender = create_account_func.call()
    tx_7560.signature = "0x"
    tx_7560.factory = factory.address
    tx_7560.factoryData = create_account_func.build_transaction()["data"]
    tx_7560.nonce = hex(0)

    assert len(w3.eth.get_code(tx_7560.sender)) == 0
    nonce = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce == 0
    fund(w3, tx_7560.sender)
    response = tx_7560.send()
    assert_ok(response)
    send_bundle_now()
    assert len(w3.eth.get_code(tx_7560.sender)) > 0
    nonce_after = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce_after == 1


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


#
# def idfunction(case):
#     entity = re.match("TestRules(.*)", case.entity).groups()[0].lower()
#     result = "ok" if case.assert_func.__name__ == assert_ok.__name__ else "drop"
#     return f"[{case.ruleId}]{'staked' if case.staked else 'unstaked'}][{entity}][{case.rule}][{result}"
#
#
# @pytest.mark.usefixtures("clear_state")
# @pytest.mark.parametrize("case", cases, ids=idfunction)
# def test_rule(w3, entrypoint_contract, case):
#     entity_contract = deploy_and_deposit(
#         w3, entrypoint_contract, case.entity, case.staked
#     )
#     userop = case.userop_build_func(w3, entrypoint_contract, entity_contract, case.rule)
#     response = userop.send()
#     case.assert_func(response)
