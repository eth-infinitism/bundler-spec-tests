# pylint: skip-file
import collections

import pytest
from tests.types import RPCErrorCode
from tests.utils import (
    UserOperation,
    assert_rpc_error,
)
from tests.utils import get_sender_address

pytest.skip(allow_module_level=True)

# see actions in https://docs.google.com/document/d/1DFX5hUhv_fwqC7wez6SBT3pWTGfSDiV45NyXllhxYik/edit?usp=sharing
ok = "ok"
throttle = 1
drop = "drop"

Rule = collections.namedtuple("Rule", ["Unstaked", "Staked", "Throttled"])

# keys are rules to pass to our entity
# values are 6 columns: 2 columns for each scenario of (unstaked, staked, staked+throttle)
# the 2 are rule for 1st simulation (rpc/p2p) and rule for 2nd simulation (bundling)
paymaster_rules = dict(
    no_storage=Rule(ok, ok, throttle),
    storage=Rule(drop, ok, throttle),
    reference_storage=Rule(drop, ok, throttle),
    account_storage=Rule(ok, ok, throttle),
    account_reference_storage=Rule(ok, ok, throttle),
    # account_reference_storage_init_code=Rule(drop, ok, throttle),
    context=Rule(drop, ok, throttle),
)

factory_rules = dict(
    no_storage=Rule(ok, ok, throttle),
    storage=Rule(drop, ok, throttle),
    reference_storage=Rule(drop, ok, throttle),
    account_storage=Rule(ok, ok, throttle),
    account_reference_storage=Rule(drop, ok, throttle),
)

sender_rules = dict(
    no_storage=Rule(ok, ok, throttle),
    account_storage=Rule(ok, ok, throttle),
    account_reference_storage=Rule(ok, ok, throttle),
    account_reference_storage_init_code=Rule(drop, ok, throttle),
)


################### sender tests #################
@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict((key, value) for key, value in sender_rules.items() if value.Unstaked == ok),
)
def test_unstaked_sender_storage_ok(rules_account_contract, rule):
    signature = "0x" + rule.encode().hex()
    assert (
        UserOperation(sender=rules_account_contract.address, signature=signature)
        .send()
        .result
    )


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict((key, value) for key, value in sender_rules.items() if value.Unstaked == drop),
)
def test_unstaked_sender_storage_initcode_drop(
    w3, entrypoint_contract, factory_contract, rule
):
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, "", entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = get_sender_address(w3, initCode)
    entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    signature = "0x" + rule.encode().hex()
    response = UserOperation(
        sender=sender, signature=signature, initCode=initCode
    ).send()
    assert_rpc_error(response, "unstaked account", RPCErrorCode.BANNED_OPCODE)


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict((key, value) for key, value in sender_rules.items() if value.Staked == ok),
)
def test_staked_sender_storage_ok(
    w3, entrypoint_contract, rules_account_contract, rule
):
    rules_account_contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.accounts[0], "value": 1 * 10**18}
    )
    signature = "0x" + rule.encode().hex()
    assert (
        UserOperation(sender=rules_account_contract.address, signature=signature)
        .send()
        .result
    )


################### sender tests end ##############


################### factory tests start ##############
@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict((key, value) for key, value in factory_rules.items() if value.Unstaked == ok),
)
def test_unstaked_factory_storage_ok(w3, entrypoint_contract, factory_contract, rule):
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, rule, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = get_sender_address(w3, initCode)
    entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    assert UserOperation(sender=sender, initCode=initCode).send().result


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict(
        (key, value) for key, value in factory_rules.items() if value.Unstaked == drop
    ),
)
def test_unstaked_factory_storage_drop(w3, entrypoint_contract, factory_contract, rule):

    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, rule, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = get_sender_address(w3, initCode)
    entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    response = UserOperation(sender=sender, initCode=initCode).send()
    assert_rpc_error(response, "unstaked factory", RPCErrorCode.BANNED_OPCODE)


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict((key, value) for key, value in factory_rules.items() if value.Staked == ok),
)
def test_staked_factory_storage_ok(w3, entrypoint_contract, factory_contract, rule):
    factory_contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.accounts[0], "value": 1 * 10**18}
    )
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, rule, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = get_sender_address(w3, initCode)
    entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    assert UserOperation(sender=sender, initCode=initCode).send().result


################### factory tests end ##############

################### paymaster tests start ##############
@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict(
        (key, value) for key, value in paymaster_rules.items() if value.Unstaked == ok
    ),
)
def test_unstaked_paymaster_storage_ok(wallet_contract, paymaster_contract, rule):
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    assert (
        UserOperation(sender=wallet_contract.address, paymasterAndData=paymasterAndData)
        .send()
        .result
    )


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict(
        (key, value) for key, value in paymaster_rules.items() if value.Unstaked == drop
    ),
)
def test_unstaked_paymaster_storage_drop(paymaster_contract, wallet_contract, rule):
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    response = UserOperation(
        sender=wallet_contract.address, paymasterAndData=paymasterAndData
    ).send()
    assert_rpc_error(response, "unstaked paymaster", RPCErrorCode.BANNED_OPCODE)


@pytest.mark.usefixtures("clear_state")
def test_unstaked_paymaster_storage_initcode_drop(
    w3, paymaster_contract, entrypoint_contract, factory_contract
):
    rule = "account_reference_storage_init_code"
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, "", entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    response = UserOperation(
        sender=get_sender_address(w3, initCode),
        paymasterAndData=paymasterAndData,
        initCode=initCode,
    ).send()
    assert_rpc_error(response, "", RPCErrorCode.BANNED_OPCODE)


@pytest.mark.usefixtures("clear_state")
def test_staked_paymaster_storage_initcode_ok(
    w3, paymaster_contract, entrypoint_contract, factory_contract
):
    rule = "account_reference_storage_init_code"
    paymaster_contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.accounts[0], "value": 1 * 10**18}
    )
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, "", entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    assert (
        UserOperation(
            sender=get_sender_address(w3, initCode),
            paymasterAndData=paymasterAndData,
            initCode=initCode,
        )
        .send()
        .result
    )


@pytest.mark.usefixtures("clear_state")
@pytest.mark.parametrize(
    "rule",
    dict((key, value) for key, value in paymaster_rules.items() if value.Staked == ok),
)
def test_staked_paymaster_storage_ok(
    w3, entrypoint_contract, wallet_contract, paymaster_contract, rule
):
    paymaster_contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.accounts[0], "value": 1 * 10**18}
    )
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    assert (
        UserOperation(sender=wallet_contract.address, paymasterAndData=paymasterAndData)
        .send()
        .result
    )
