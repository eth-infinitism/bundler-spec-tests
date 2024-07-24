import pytest
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
    send_bundle_now,
    assert_rpc_error,
    to_prefixed_hex,
    deploy_contract,
    deploy_state_contract,
)

# def with_initcode(build_tx7560_func, deploy_factory_func=deploy_unstaked_factory):
#     def _with_initcode(w3, entrypoint_contract, contract, rule):
#         factory_contract = deploy_factory_func(w3, entrypoint_contract)
#         userop = build_tx7560_func(w3, entrypoint_contract, contract, rule)
#         factoryData = factory_contract.functions.create(
#             123, "", entrypoint_contract.address
#         ).build_transaction()["data"]
#         sender = deposit_to_undeployed_sender(
#             w3, entrypoint_contract, factory_contract.address, factoryData
#         )
#         userop.sender = sender
#         userop.factory = factory_contract.address
#         userop.factoryData = factoryData
#         userop.verificationGasLimit = hex(5000000)
#         return userop
#
#     return _with_initcode


def build_tx7560_for_paymaster(w3, paymaster_contract, rule):
    wallet = deploy_contract(w3, "rip7560/TestAccount")
    return TransactionRIP7560(
        sender=wallet.address,
        paymaster=paymaster_contract.address,
        paymasterData="0x" + rule.encode().hex(),
    )


def build_tx7560_for_sender(w3, rules_account_contract, rule):
    call_data = deploy_state_contract(w3).address
    signature = "0x" + rule.encode().hex()
    return TransactionRIP7560(
        sender=rules_account_contract.address, callData=call_data, signature=signature
    )


def build_tx7560_for_factory(w3, entrypoint_contract, factory_contract, rule):
    pass
    # factoryData = factory_contract.functions.create(
    #     123, rule, entrypoint_contract.address
    # ).build_transaction()["data"]
    #
    # sender = deposit_to_undeployed_sender(
    #     w3, entrypoint_contract, factory_contract.address, factoryData
    # )
    # return TransactionRIP7560(
    #     sender=sender, factory=factory_contract.address, factoryData=factoryData
    # )


def entity_to_contract_name(entity):
    if entity == PAYMASTER:
        return "rip7560/RIP7560Paymaster"
    elif entity == FACTORY:
        return "rip7560/RIP7560Deployer"
    elif entity == SENDER:
        return "rip7560/RIP7560TestRulesAccount"
    elif entity == AGGREGATOR:
        # TODO: Not implemented yet
        return None


def get_build_func(entity):
    if entity == PAYMASTER:
        return build_tx7560_for_paymaster
    elif entity == FACTORY:
        return build_tx7560_for_factory
    elif entity == SENDER:
        return build_tx7560_for_sender
    elif entity == AGGREGATOR:
        # TODO: Not implemented yet
        return None


@pytest.mark.parametrize("case", cases, ids=case_id_function)
def test_rule(w3, case):
    if case.entity != SENDER and case.entity != PAYMASTER:
        pytest.skip()
    entity_contract_name = entity_to_contract_name(case.entity)
    entity_contract = deploy_contract(w3, entity_contract_name, value=1 * 10**18)
    print("WTF paymaster coin", entity_contract.functions.coin().call())
    build_func = get_build_func(case.entity)
    tx7560 = build_func(w3, entity_contract, case.rule)
    response = tx7560.send()
    case.assert_func(response)
