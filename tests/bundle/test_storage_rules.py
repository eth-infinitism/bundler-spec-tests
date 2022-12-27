import collections
import re

import pytest
from tests.types import UserOperation, RPCErrorCode
from tests.utils import (
    assertRpcError,
    deploy_wallet_contract,
    deploy_contract,
    getSenderAddress,
    deploy_and_deposit,
)


def assertOk(response):
    try:
        assert response.result
    except AttributeError:
        raise Exception(response)


def assertError(response):
    assertRpcError(response, response.message, RPCErrorCode.BANNED_OPCODE)


def withInitCode(buildUserOpFunc):
    def _withInitCode(w3, entrypoint_contract, contract, rule):
        factory_contract = deploy_contract(
            w3,
            "TestRulesFactory",
            ctrParams=[entrypoint_contract.address],
        )
        userOp = buildUserOpFunc(w3, entrypoint_contract, contract, rule)
        initCode = (
            factory_contract.address
            + factory_contract.functions.create(
                123, "", entrypoint_contract.address
            ).build_transaction()["data"][2:]
        )
        sender = getSenderAddress(w3, initCode)
        userOp.sender = sender
        userOp.initCode = initCode
        return userOp

    return _withInitCode


def buildUserOpForPaymasterTest(w3, _entrypoint_contract, paymaster_contract, rule):
    wallet = deploy_wallet_contract(w3)
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    return UserOperation(sender=wallet.address, paymasterAndData=paymasterAndData)


def buildUserOpForSenderTest(_w3, _entrypoint_contract, rules_account_contract, rule):
    signature = "0x" + rule.encode().hex()
    return UserOperation(sender=rules_account_contract.address, signature=signature)


def buildUserOpForFactoryTest(w3, entrypoint_contract, factory_contract, rule):
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, rule, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = getSenderAddress(w3, initCode)
    entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    return UserOperation(sender=sender, initCode=initCode)


staked = True
unstaked = False
paymaster = "TestRulesPaymaster"
factory = "TestRulesFactory"
sender = "TestRulesAccount"
aggregator = "TestRulesAggregator"

StorageTestCase = collections.namedtuple(
    "StorageTestCase", ["rule", "staked", "entity", "userOpBuildFunc", "assertFunc"]
)
cases = [
    # unstaked paymaster
    StorageTestCase(
        "no_storage", unstaked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    StorageTestCase(
        "storage", unstaked, paymaster, buildUserOpForPaymasterTest, assertError
    ),
    StorageTestCase(
        "reference_storage",
        unstaked,
        paymaster,
        buildUserOpForPaymasterTest,
        assertError,
    ),
    StorageTestCase(
        "account_storage", unstaked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    StorageTestCase(
        "account_reference_storage",
        unstaked,
        paymaster,
        buildUserOpForPaymasterTest,
        assertOk,
    ),
    StorageTestCase(
        "account_reference_storage_init_code",
        unstaked,
        paymaster,
        withInitCode(buildUserOpForPaymasterTest),
        assertError,
    ),
    StorageTestCase(
        "context", unstaked, paymaster, buildUserOpForPaymasterTest, assertError
    ),
    # staked paymaster
    StorageTestCase(
        "no_storage", staked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    StorageTestCase(
        "storage", staked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    StorageTestCase(
        "reference_storage", staked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    StorageTestCase(
        "account_storage", staked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    StorageTestCase(
        "account_reference_storage",
        staked,
        paymaster,
        buildUserOpForPaymasterTest,
        assertOk,
    ),
    StorageTestCase(
        "account_reference_storage_init_code",
        staked,
        paymaster,
        withInitCode(buildUserOpForPaymasterTest),
        assertOk,
    ),
    StorageTestCase(
        "context", staked, paymaster, buildUserOpForPaymasterTest, assertOk
    ),
    # unstaked factory
    StorageTestCase(
        "no_storage", unstaked, factory, buildUserOpForFactoryTest, assertOk
    ),
    StorageTestCase(
        "storage", unstaked, factory, buildUserOpForFactoryTest, assertError
    ),
    StorageTestCase(
        "reference_storage", unstaked, factory, buildUserOpForFactoryTest, assertError
    ),
    StorageTestCase(
        "account_storage", unstaked, factory, buildUserOpForFactoryTest, assertOk
    ),
    StorageTestCase(
        "account_reference_storage",
        unstaked,
        factory,
        buildUserOpForFactoryTest,
        assertError,
    ),
    # staked factory
    StorageTestCase("no_storage", staked, factory, buildUserOpForFactoryTest, assertOk),
    StorageTestCase("storage", staked, factory, buildUserOpForFactoryTest, assertOk),
    StorageTestCase(
        "reference_storage", staked, factory, buildUserOpForFactoryTest, assertOk
    ),
    StorageTestCase(
        "account_storage", staked, factory, buildUserOpForFactoryTest, assertOk
    ),
    StorageTestCase(
        "account_reference_storage",
        staked,
        factory,
        buildUserOpForFactoryTest,
        assertOk,
    ),
    # unstaked sender
    StorageTestCase("no_storage", unstaked, sender, buildUserOpForSenderTest, assertOk),
    StorageTestCase(
        "account_storage", unstaked, sender, buildUserOpForSenderTest, assertOk
    ),
    StorageTestCase(
        "account_reference_storage",
        unstaked,
        sender,
        buildUserOpForSenderTest,
        assertOk,
    ),
    StorageTestCase(
        "account_reference_storage_init_code",
        unstaked,
        sender,
        withInitCode(buildUserOpForSenderTest),
        assertError,
    ),
    # staked sender
    StorageTestCase("no_storage", staked, sender, buildUserOpForSenderTest, assertOk),
    StorageTestCase(
        "account_storage", staked, sender, buildUserOpForSenderTest, assertOk
    ),
    StorageTestCase(
        "account_reference_storage", staked, sender, buildUserOpForSenderTest, assertOk
    ),
]


def idfunction(case):
    entity = re.match("TestRules(.*)", case.entity).groups()[0].lower()
    result = "ok" if case.assertFunc == assertOk else "drop"
    return f"{'staked' if case.staked else 'unstaked'}_{entity}][{case.rule}_{result}"


@pytest.mark.usefixtures("clearState")
@pytest.mark.parametrize("case", cases, ids=idfunction)
def test_rule(w3, entrypoint_contract, case):
    entity_contract = deploy_and_deposit(
        w3, entrypoint_contract, case.entity, case.staked
    )
    userOp = case.userOpBuildFunc(w3, entrypoint_contract, entity_contract, case.rule)
    response = userOp.send()
    case.assertFunc(response)
