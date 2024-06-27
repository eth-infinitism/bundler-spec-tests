import pytest
from tests.single.opbanning.test_op_banning import banned_opcodes
from tests.types import RPCErrorCode
from tests.utils import send_bundle_now, assert_rpc_error, to_prefixed_hex


def test_eth_sendTransaction7560(wallet_contract, tx_7560):
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
    tx_7560.paymasterVerificationGasLimit = hex(100000)
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
        wallet_contract_rules, tx_7560, factory_contract_7560, banned_op
):
    state_before = wallet_contract_rules.functions.state().call()
    assert state_before == 0
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.factory = factory_contract_7560.address
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
    state_after = wallet_contract_rules.functions.state().call()
    assert state_after == 0

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
