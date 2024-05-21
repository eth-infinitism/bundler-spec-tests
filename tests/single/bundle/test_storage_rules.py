import collections
import re

import pytest
from tests.types import UserOperation, RPCErrorCode
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    deploy_wallet_contract,
    deploy_state_contract,
    deploy_contract,
    deploy_and_deposit,
    deposit_to_undeployed_sender,
    staked_contract,
)


def assert_error(response):
    assert_rpc_error(response, response.message, RPCErrorCode.BANNED_OPCODE)


def deploy_unstaked_factory(w3, entrypoint_contract):
    return deploy_contract(
        w3,
        "TestRulesFactory",
        ctrparams=[entrypoint_contract.address],
    )


def deploy_staked_rule_factory(w3, entrypoint_contract):
    contract = deploy_contract(
        w3, "TestRulesAccountFactory", ctrparams=[entrypoint_contract.address]
    )
    return staked_contract(w3, entrypoint_contract, contract)


def deploy_staked_factory(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesFactory", True)


def with_initcode(build_userop_func, deploy_factory_func=deploy_unstaked_factory):
    def _with_initcode(w3, entrypoint_contract, contract, rule):
        factory_contract = deploy_factory_func(w3, entrypoint_contract)
        userop = build_userop_func(w3, entrypoint_contract, contract, rule)
        factoryData = factory_contract.functions.create(
            123, "", entrypoint_contract.address
        ).build_transaction()["data"]
        sender = deposit_to_undeployed_sender(
            w3, entrypoint_contract, factory_contract.address, factoryData
        )
        userop.sender = sender
        userop.factory = factory_contract.address
        userop.factoryData = factoryData
        userop.verificationGasLimit = hex(5000000)
        return userop

    return _with_initcode


def build_userop_for_paymaster(w3, _entrypoint_contract, paymaster_contract, rule):
    wallet = deploy_wallet_contract(w3)
    return UserOperation(
        sender=wallet.address,
        paymaster=paymaster_contract.address,
        paymasterData="0x" + rule.encode().hex(),
    )


def build_userop_for_sender(w3, _entrypoint_contract, rules_account_contract, rule):
    call_data = deploy_state_contract(w3).address
    signature = "0x" + rule.encode().hex()
    return UserOperation(
        sender=rules_account_contract.address, callData=call_data, signature=signature
    )


def build_userop_for_factory(w3, entrypoint_contract, factory_contract, rule):
    factoryData = factory_contract.functions.create(
        123, rule, entrypoint_contract.address
    ).build_transaction()["data"]

    sender = deposit_to_undeployed_sender(
        w3, entrypoint_contract, factory_contract.address, factoryData
    )
    return UserOperation(
        sender=sender, factory=factory_contract.address, factoryData=factoryData
    )


STAKED = True
UNSTAKED = False
PAYMASTER = "TestRulesPaymaster"
FACTORY = "TestRulesFactory"
SENDER = "TestRulesAccount"
AGGREGATOR = "TestRulesAggregator"

StorageTestCase = collections.namedtuple(
    "StorageTestCase",
    ["ruleId", "rule", "staked", "entity", "userop_build_func", "assert_func"],
)
cases = [
    # unstaked paymaster
    StorageTestCase(
        "STO-000",
        "no_storage",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-031",
        "storage",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "OP-070(STO-031)",
        "transient_storage_tstore",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "OP-070(STO-031)",
        "transient_storage_tload",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage_struct",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "STO-010",
        "account_storage",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "OP-070(STO-010)",
        "account_transient_storage",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage_struct",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-022",
        "account_reference_storage_init_code",
        UNSTAKED,
        PAYMASTER,
        with_initcode(build_userop_for_paymaster),
        assert_error,
    ),
    StorageTestCase(
        "EREP-050-regression",
        "context",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-032",
        "external_storage_read",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "OP-020",
        "out_of_gas",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "OP-020",
        "sstore_out_of_gas",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    # staked paymaster
    StorageTestCase(
        "STO-000",
        "no_storage",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-031", "storage", STAKED, PAYMASTER, build_userop_for_paymaster, assert_ok
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage_struct",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-033",
        "reference_storage_struct",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-010",
        "account_storage",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage_struct",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-022",
        "account_reference_storage_init_code",
        STAKED,
        PAYMASTER,
        with_initcode(build_userop_for_paymaster),
        assert_ok,
    ),
    StorageTestCase(
        "EREP-050-regression",
        "context",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "STO-033",
        "external_storage_write",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "STO-033",
        "external_storage_read",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_ok,
    ),
    StorageTestCase(
        "OP-020",
        "out_of_gas",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    StorageTestCase(
        "OP-020",
        "sstore_out_of_gas",
        STAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
    ),
    # unstaked factory
    StorageTestCase(
        "STO-000", "no_storage", UNSTAKED, FACTORY, build_userop_for_factory, assert_ok
    ),
    StorageTestCase(
        "STO-000", "storage", UNSTAKED, FACTORY, build_userop_for_factory, assert_error
    ),
    StorageTestCase(
        "STO-000",
        "reference_storage",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage_struct",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "STO-010",
        "account_storage",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage_struct",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "STO-000",
        "external_storage_read",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-042",
        "EXTCODEx_CALLx_undeployed_sender",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "OP-041",
        "EXTCODESIZE_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "EXTCODEHASH_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "EXTCODECOPY_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "CALL_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "CALLCODE_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "DELEGATECALL_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "STATICCALL_undeployed_contract",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-020",
        "out_of_gas",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-020",
        "sstore_out_of_gas",
        UNSTAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    # staked factory
    StorageTestCase(
        "STO-000", "no_storage", STAKED, FACTORY, build_userop_for_factory, assert_ok
    ),
    StorageTestCase(
        "STO-031", "storage", STAKED, FACTORY, build_userop_for_factory, assert_ok
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "STO-032",
        "reference_storage_struct",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "STO-010",
        "account_storage",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage_struct",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "STO-033",
        "external_storage_write",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "STO-033",
        "external_storage_read",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_ok,
    ),
    StorageTestCase(
        "OP-020",
        "out_of_gas",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    StorageTestCase(
        "OP-020",
        "sstore_out_of_gas",
        STAKED,
        FACTORY,
        build_userop_for_factory,
        assert_error,
    ),
    # unstaked sender
    StorageTestCase(
        "STO-000", "no_storage", UNSTAKED, SENDER, build_userop_for_sender, assert_ok
    ),
    StorageTestCase(
        "STO-010",
        "account_storage",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "STO-022",
        "account_reference_storage_init_code",
        UNSTAKED,
        SENDER,
        with_initcode(build_userop_for_sender),
        assert_error,
    ),
    StorageTestCase(
        "STO-022",
        "account_reference_storage_init_code",
        UNSTAKED,
        SENDER,
        with_initcode(build_userop_for_sender, deploy_staked_rule_factory),
        assert_ok,
    ),
    StorageTestCase(
        "STO-022",
        "account_reference_storage_init_code",
        UNSTAKED,
        PAYMASTER,
        with_initcode(build_userop_for_paymaster, deploy_staked_rule_factory),
        assert_error,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage_struct",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "STO-000",
        "external_storage_read",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-020", "out_of_gas", UNSTAKED, SENDER, build_userop_for_sender, assert_error
    ),
    StorageTestCase(
        "OP-020",
        "sstore_out_of_gas",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    # staked sender
    StorageTestCase(
        "STO-000", "no_storage", STAKED, SENDER, build_userop_for_sender, assert_ok
    ),
    StorageTestCase(
        "STO-010", "account_storage", STAKED, SENDER, build_userop_for_sender, assert_ok
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage",
        STAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "STO-021",
        "account_reference_storage_struct",
        STAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "OP-020", "out_of_gas", STAKED, SENDER, build_userop_for_sender, assert_error
    ),
    StorageTestCase(
        "OP-020",
        "sstore_out_of_gas",
        STAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "STO-033",
        "external_storage_write",
        STAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "STO-033",
        "external_storage_read",
        STAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "OP-011",
        "entryPoint_call_balanceOf",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-061",
        "eth_value_transfer_forbidden",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-053",
        "eth_value_transfer_entryPoint",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "OP-052",
        "eth_value_transfer_entryPoint_depositTo",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
    StorageTestCase(
        "OP-041",
        "EXTCODESIZE_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "EXTCODEHASH_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "EXTCODECOPY_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-054",
        "EXTCODESIZE_entrypoint",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-054",
        "EXTCODEHASH_entrypoint",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-054",
        "EXTCODECOPY_entrypoint",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "CALL_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "CALLCODE_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "DELEGATECALL_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-041",
        "STATICCALL_undeployed_contract",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_error,
    ),
    StorageTestCase(
        "OP-062",
        "CALL_undeployed_contract_allowed_precompile",
        UNSTAKED,
        SENDER,
        build_userop_for_sender,
        assert_ok,
    ),
]


def idfunction(case):
    entity = re.match("TestRules(.*)", case.entity).groups()[0].lower()
    result = "ok" if case.assert_func.__name__ == assert_ok.__name__ else "drop"
    return f"[{case.ruleId}]{'staked' if case.staked else 'unstaked'}][{entity}][{case.rule}][{result}"


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize("case", cases, ids=idfunction)
def test_rule(w3, entrypoint_contract, case):
    entity_contract = deploy_and_deposit(
        w3, entrypoint_contract, case.entity, case.staked
    )
    userop = case.userop_build_func(w3, entrypoint_contract, entity_contract, case.rule)
    response = userop.send()
    case.assert_func(response)
