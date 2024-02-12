import collections
import re

import pytest
from dataclasses import asdict
from tests.types import UserOperation, RPCErrorCode, RPCRequest
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    deploy_wallet_contract,
    deploy_state_contract,
    deploy_contract,
    deploy_and_deposit,
    deposit_to_undeployed_sender,
    staked_contract,
    userop_hash,
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
        initcode = (
            factory_contract.address
            + factory_contract.functions.create(
                123, "", entrypoint_contract.address
            ).build_transaction()["data"][2:]
        )
        sender = deposit_to_undeployed_sender(w3, entrypoint_contract, initcode)
        userop.sender = sender
        userop.initCode = initcode
        userop.verificationGasLimit = hex(5000000)
        return userop

    return _with_initcode


def build_userop_for_paymaster(w3, _entrypoint_contract, paymaster_contract, rule):
    wallet = deploy_wallet_contract(w3)
    paymaster_and_data = paymaster_contract.address + rule.encode().hex()
    return UserOperation(sender=wallet.address, paymasterAndData=paymaster_and_data)


def build_userop_for_sender(w3, _entrypoint_contract, rules_account_contract, rule):
    call_data = deploy_state_contract(w3).address
    signature = "0x" + rule.encode().hex()
    return UserOperation(
        sender=rules_account_contract.address, callData=call_data, signature=signature
    )


def build_userop_for_factory(w3, entrypoint_contract, factory_contract, rule):
    initcode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, rule, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = deposit_to_undeployed_sender(w3, entrypoint_contract, initcode)
    return UserOperation(sender=sender, initCode=initcode)


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
        "EREP-050",
        "context",
        UNSTAKED,
        PAYMASTER,
        build_userop_for_paymaster,
        assert_error,
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
        "EREP-050", "context", STAKED, PAYMASTER, build_userop_for_paymaster, assert_ok
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


@pytest.mark.usefixtures("clear_state", "auto_bundling_mode")
def test_enough_verification_gas(w3, entrypoint_contract, helper_contract):
    beneficiary = w3.eth.accounts[0]

    callGasLimit = hex(20000)
    calldata = wallet.encodeABI(fn_name="wasteGas")

    # Estimating gas for the op's gas limits
    wallet = deploy_wallet_contract(w3)
    userop = UserOperation(
        sender=wallet.address,
        nonce="0x0",
        callData=calldata,
        callGasLimit=callGasLimit,
        verificationGasLimit=hex(10**6),
        maxPriorityFeePerGas=hex(10**10),
        maxFeePerGas=hex(10**10),
        preVerificationGas=hex(10**6),
    )
    response = RPCRequest(
        method="eth_estimateUserOperationGas",
        params=[asdict(userop), entrypoint_contract.address],
    ).send()
    pre_verification_gas = response.result["preVerificationGas"]
    verification_gas = response.result["verificationGasLimit"]

    # Searching for the gas that gets us aa51 revert onchain
    low_gas = 0
    high_gas = 5 * 10**5
    min_verification_gas = high_gas
    while low_gas <= high_gas:
        wallet = deploy_wallet_contract(w3)
        mid_gas = (high_gas + low_gas) // 2
        userop = UserOperation(
            sender=wallet.address,
            nonce="0x0",
            callData=calldata,
            callGasLimit=callGasLimit,
            verificationGasLimit=hex(mid_gas),
            maxPriorityFeePerGas=hex(10**10),
            maxFeePerGas=hex(10**10),
            preVerificationGas=pre_verification_gas,
        )
        handleops_method = entrypoint_contract.functions.handleOps(
            [userop.to_tuple()], beneficiary
        )
        tx_hash = handleops_method.transact(
            {"from": w3.eth.accounts[0], "gas": 1 * 10**6}
        )
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 0:
            low_gas = mid_gas + 1
        else:
            high_gas = mid_gas - 1
            min_verification_gas = mid_gas

    wallet = deploy_wallet_contract(w3)
    userop = UserOperation(
        sender=wallet.address,
        nonce="0x0",
        callData=calldata,
        callGasLimit=callGasLimit,
        verificationGasLimit=hex(min_verification_gas - 1),
        maxPriorityFeePerGas=hex(10**10),
        maxFeePerGas=hex(10**10),
        preVerificationGas=pre_verification_gas,
    )

    # Finally sending the op to the bundler, expecting a revert
    nonce_before = entrypoint_contract.functions.getNonce(wallet.address, 0).call()
    response = userop.send()
    nonce_after = entrypoint_contract.functions.getNonce(wallet.address, 0).call()
    assert nonce_before == nonce_after, "handleoOps not reverted onchain"
    print(response)
    assert_rpc_error(
        response,
        "",
        RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT,
        "Bundler failed to detect AA51 revert",
    )
    # sanity check, should succeed with enough gas that was returned by the bundler
    userop.verificationGasLimit = verification_gas
    response = userop.send()
    nonce_after = entrypoint_contract.functions.getNonce(wallet.address, 0).call()
    assert (
        nonce_before + 1 == nonce_after
    ), "userop reverted onchain with returned limits from estimateGas"
    assert_ok(response)


def calldatacost(calldata):
    cost = 0
    for i in range(0, len(calldata), 2):
        if calldata[i : i + 2] == "00":
            cost += 4
        else:
            cost += 16
    return cost
