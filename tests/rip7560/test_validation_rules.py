import pytest
from web3.constants import ADDRESS_ZERO
from tests.rip7560.types import TransactionRIP7560
from tests.single.bundle.test_storage_rules import (
    cases,
    case_id_function,
    PAYMASTER,
    FACTORY,
    SENDER,
    AGGREGATOR,
)

from tests.utils import (
    assert_ok,
    deploy_contract,
    deploy_state_contract,
    fund,
)


def deploy_unstaked_factory(w3):
    contract = deploy_contract(
        w3,
        "rip7560/RIP7560TestRulesAccountDeployer",
        value=1 * 10**18,
    )
    return contract


def with_initcode(build_tx7560_func, deploy_factory_func=deploy_unstaked_factory):
    def _with_initcode(w3, contract, rule):
        factory_contract = deploy_factory_func(w3)
        tx7560 = build_tx7560_func(w3, contract, rule)
        factory_data = factory_contract.functions.createAccount(
            ADDRESS_ZERO, 123, ""
        ).build_transaction()["data"]
        sender = factory_contract.functions.getCreate2Address(
            ADDRESS_ZERO, 123, ""
        ).call()
        fund(w3, sender)
        tx7560.sender = sender
        tx7560.factory = factory_contract.address
        tx7560.factoryData = factory_data
        tx7560.verificationGasLimit = hex(5000000)
        tx7560.nonce = hex(0)
        return tx7560

    return _with_initcode


def build_tx7560_for_paymaster(w3, paymaster_contract, rule):
    wallet = deploy_contract(w3, "rip7560/TestAccount")
    return TransactionRIP7560(
        sender=wallet.address,
        paymaster=paymaster_contract.address,
        paymasterData="0x" + rule.encode().hex(),
        bigNonce=hex(1),
    )


def build_tx7560_for_sender(w3, rules_account_contract, rule):
    call_data = deploy_state_contract(w3).address
    signature = "0x" + rule.encode().hex()
    return TransactionRIP7560(
        sender=rules_account_contract.address,
        callData=call_data,
        signature=signature,
        bigNonce=hex(2),
    )


def build_tx7560_for_factory(w3, factory_contract, rule):
    #     pass
    factory_data = factory_contract.functions.createAccount(
        ADDRESS_ZERO, 123, rule
    ).build_transaction()["data"]
    sender = factory_contract.functions.getCreate2Address(
        ADDRESS_ZERO, 123, rule
    ).call()
    fund(w3, sender)
    return TransactionRIP7560(
        sender=sender, factory=factory_contract.address, factoryData=factory_data
    )


def entity_to_contract_name(entity):
    if entity == PAYMASTER:
        return "rip7560/RIP7560Paymaster"
    if entity == FACTORY:
        return "rip7560/RIP7560Deployer"
    if entity == SENDER:
        return "rip7560/RIP7560TestRulesAccount"
    if entity == AGGREGATOR:
        # Not implemented yet
        return None
    return None


def get_build_func(entity, rule):
    build_func = None
    if entity == PAYMASTER:
        build_func = build_tx7560_for_paymaster
    elif entity == FACTORY:
        build_func = build_tx7560_for_factory
    elif entity == SENDER:
        build_func = build_tx7560_for_sender
    elif entity == AGGREGATOR:
        # Not implemented yet
        pass
    if rule.find("init_code") > 0:
        build_func = with_initcode(build_func)
    return build_func


@pytest.mark.parametrize("case", cases, ids=case_id_function)
def test_rule(w3, case):
    # Not implemented yet: staked entities
    if case.staked:
        pytest.skip()
    # Not implemented yet: This case needs a staked factory
    if (
        case.rule == "account_reference_storage_init_code"
        and case.entity == SENDER
        and case.assert_func is assert_ok
    ):
        pytest.skip()
    # EntryPoint rules are mostly irrelevant
    if case.rule == "entryPoint_call_balanceOf" or case.rule in (
        "eth_value_transfer_entryPoint",
        "eth_value_transfer_entryPoint_depositTo",
    ):
        pytest.skip()

    entity_contract_name = entity_to_contract_name(case.entity)
    entity_contract = deploy_contract(w3, entity_contract_name, value=1 * 10**18)
    build_func = get_build_func(case.entity, case.rule)
    tx7560 = build_func(w3, entity_contract, case.rule)
    response = tx7560.send()
    case.assert_func(response)
