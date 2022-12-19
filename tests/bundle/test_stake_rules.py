import re

import pytest
from tests.utils import (
    deploy_contract,
    deploy_wallet_contract,
    UserOperation,
    RPCRequest,
    assertRpcError,
    CommandLineArgs,
)
from tests.types import RPCErrorCode

ruletable = """
|                 | unstaked    | unstaked | staked  | staked  | st-throttled | st-throttled |
| --------------- | ----------- | -------- | ------- | ------- | ------------ | ------------ |
| rules           | **1st sim** | **2nd**  | **1st** | **2nd** | **1st**      | **2nd**      |
| No-storage      | ok          | ok       | ok      | ok      | throttle     | throttle     |
| Acct-ref-noinit | ok          | ok       | ok      | ok      | throttle     | throttle     |
| Acct-ref-init   | drop        | drop     | ok      | ok      | throttle     | throttle     |
| Acct-storage    | ok          | ok       | ok      | ok      | throttle     | throttle     |
| ent-storage     | drop        | drop     | ok      | ok      | throttle     | throttle     |
| ent-ref         | drop        | drop     | ok      | ok      | throttle     | throttle     |
| ent==sender     | 4           | 1        | ok      | ok      | throttle     | throttle     |
"""

# see actions in https://docs.google.com/document/d/1DFX5hUhv_fwqC7wez6SBT3pWTGfSDiV45NyXllhxYik/edit?usp=sharing
ok = "ok"
throttle = 1
drop = "drop"

# keys are rules to pass to our entity
# values are 6 columns: 2 columns for each scenario of (unstaked, staked, staked+throttle)
# the 2 are rule for 1st simulation (rpc/p2p) and rule for 2nd simulation (bundling)
rules = dict(
    no_storage=[ok, ok, ok, ok, throttle, throttle],
    account_reference_storage=[ok, ok, ok, ok, throttle, throttle],
    # account_reference_storage_init_code=[drop, drop, ok, ok, throttle, throttle],
    account_storage=[ok, ok, ok, ok, throttle, throttle],
    entity_storage=[drop, drop, ok, ok, throttle, throttle],
    # ent_ref=[drop, drop, ok, ok, throttle, throttle],
    # context=[drop, drop, ok, ok, throttle, throttle],
    # not a real rule: sender is entity just like others.
    # entSender=[4, 1, ok, ok, throttle, throttle],
)


def get_action(rule, isStaked, isThrottled=False):
    """
    :param rule: row in the table
    :param isStaked: False for cols 1,2 True for 3,4
    :param isThrottled for st-throttled column (5,6)
    :return: [rule1, rule2] - rule for 1st and 2nd simulation
    """
    r = rules[rule]
    if r is None:
        raise Exception("unknown rule: " + rule)
    index = 0 if not isStaked else 2 if not isThrottled else 4
    return r[index : index + 2]


def setThrottled(ent):
    # todo: set proper values that will consider it "throttled"
    RPCRequest(
        method="aa_setReputation",
        params=[{"reputation": {ent.address: {"opsSeen": 1, "opsIncluded": 2}}}],
    ).send().result


entityTypes = [
    # 'factory',
    # 'sender',
    "paymaster"
]


def test_dict():
    # git nocommit
    print(dict((key, value) for key, value in rules.items() if value[0] == "drop"))
    print(dict((key, value) for key, value in rules.items() if value[0] == "ok"))


def getSenderAddress(w3, initCode):
    helper = deploy_contract(w3, "Helper")
    return helper.functions.getSenderAddress(CommandLineArgs.entryPoint, initCode).call(
        {"gas": 10000000}
    )


@pytest.mark.usefixtures("clearState")
@pytest.mark.parametrize("amount", [2], ids=[""])
@pytest.mark.parametrize(
    "rule", dict((key, value) for key, value in rules.items() if value[0] == "ok")
)
def test_unstaked_paymaster_storage_ok(wallet_contracts, paymaster_contract, rule):
    senders = [wallet.address for wallet in wallet_contracts]
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    for sender in senders:
        assert (
            UserOperation(sender=sender, paymasterAndData=paymasterAndData)
            .send()
            .result
        )


@pytest.mark.usefixtures("clearState")
@pytest.mark.parametrize(
    "rule", dict((key, value) for key, value in rules.items() if value[0] == "drop")
)
def test_unstaked_paymaster_storage_drop(w3, paymaster_contract, rule):
    factory = deploy_contract(w3, "TestRuleFactory", [CommandLineArgs.entryPoint])
    initCode = (
        factory.address
        + factory.functions.create(123, "").build_transaction()["data"][2:]
    )
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    response = UserOperation(
        sender=getSenderAddress(w3, initCode),
        paymasterAndData=paymasterAndData,
        initCode=initCode,
    ).send()
    assertRpcError(response, "", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT)


@pytest.mark.usefixtures("clearState")
def test_unstaked_paymaster_storage_initcode_drop(w3, paymaster_contract):
    rule = "account_reference_storage_init_code"
    factory = deploy_contract(w3, "TestRuleFactory", [CommandLineArgs.entryPoint])
    initCode = (
        factory.address
        + factory.functions.create(123, "").build_transaction()["data"][2:]
    )
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    response = UserOperation(
        sender=getSenderAddress(w3, initCode),
        paymasterAndData=paymasterAndData,
        initCode=initCode,
    ).send()
    assertRpcError(response, "", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT)


@pytest.mark.skip
@pytest.mark.usefixtures("clearState")
@pytest.mark.parametrize("amount", [2], ids=[""])
@pytest.mark.parametrize("rule", rules.keys())
def test_staked_paymaster_storage_ok(
    w3, entrypoint_contract, wallet_contracts, paymaster_contract, rule
):
    initCodes = ["0x", "0x"]
    senders = [wallet.address for wallet in wallet_contracts]
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    sig = "0x"
    isStaked = False
    isThrottled = False
    action = get_action(rule, isStaked, isThrottled)
    for sender, initCode in zip(senders, initCodes):
        assert (
            UserOperation(
                sender=sender,
                signature=sig,
                paymasterAndData=paymasterAndData,
                initCode=initCode,
            )
            .send()
            .result
        )


@pytest.mark.skip
@pytest.mark.usefixtures("clearState")
@pytest.mark.parametrize("amount", [2], ids=[""])
@pytest.mark.parametrize("rule", rules.keys())
def test_staked_paymaster_storage_drop(
    w3, entrypoint_contract, wallet_contracts, paymaster_contract, rule
):
    initCodes = ["0x", "0x"]
    senders = [wallet.address for wallet in wallet_contracts]
    paymasterAndData = paymaster_contract.address + rule.encode().hex()
    sig = "0x"
    isStaked = False
    isThrottled = False
    action = get_action(rule, isStaked, isThrottled)
    for sender, initCode in zip(senders, initCodes):
        assert (
            UserOperation(
                sender=sender,
                signature=sig,
                paymasterAndData=paymasterAndData,
                initCode=initCode,
            )
            .send()
            .result
        )


@pytest.mark.parametrize("amount", [2])
@pytest.mark.parametrize("rule", rules.keys())
@pytest.mark.parametrize("entity", entityTypes)
@pytest.mark.parametrize("isStaked", [False, True])
@pytest.mark.parametrize("isThrottled", [False, True])
@pytest.mark.usefixtures("clearState")
def detest_stake_rule(
    entrypoint_contract, w3, wallet_contracts, entity, rule, isStaked, isThrottled
):
    entryPoint = entrypoint_contract

    helper = deploy_contract(w3, "Helper")

    def getSenderAddress(initCode):
        return helper.functions.getSenderAddress(entryPoint.address, initCode).call(
            {"gas": 10000000}
        )

    # remove unsupported combinations
    if isThrottled and not isStaked:
        return
    # the "init/noinit" rules are for all entities but factory
    # (they check other entity with/without factory
    if rule.find("init") > 0 and entity == "factory":
        return
    # if rule == 'entSender' and entity != 'sender': return
    if rule == "context" and entity != "paymaster":
        return

    # depending on entity, fill in the fields
    # (paymaster is a single string. factory is an array, since it needs different
    # ctr params to create 2 separate accounts)
    # either initCodes or sender is empty
    initCodes = ["0x", "0x"]
    # default to 2 wallets, unless we have initCode, in which case we derive wallet addresses from there.
    senders = [wallet.address for wallet in wallet_contracts]
    paymasterAndData = "0x"
    ent = None
    sig = "0x"
    # testing (sender, paymaster) but with initCode
    if rule.find("-init") > 0:
        factory = deploy_contract("TestFactory")
        initCodes = [
            ent.address + factory.functions.create(1, "").build_transaction()["data"],
            ent.address + factory.functions.create(2, "").build_transaction()["data"],
        ]
        # remove the init/noinit marker from the rule
        rule = re.sub("-(no)?init", "")

    if entity == "paymaster":
        ent = deploy_contract(w3, "TestRulePaymaster")
        paymasterAndData = ent.address + rule.encode().hex()
    elif entity == "factory":
        ent = deploy_contract(w3, "TestRuleFactory", [CommandLineArgs.entryPoint])
        initCodes = [
            ent.address + ent.functions.create(1, rule).build_transaction()["data"],
            ent.address + ent.functions.create(2, rule).build_transaction()["data"],
        ]
    elif entity == "sender":
        ent = deploy_wallet_contract()
        sig = "0x" + rule.encode().hex()
        senders = [ent, ent]
    else:
        raise Exception("unknown entity", entity)
        # paymaster = deploy_contract('TestRulePaymaster')

    if isStaked:
        ent.addStake(entryPoint, 1)
        if isThrottled:
            setThrottled(ent)

    if initCodes != ["0x", "0x"]:
        # we have initcode: replace senders with initCode's sender address
        senders = [
            getSenderAddress(initCodes[0]),
            getSenderAddress(initCodes[1]),
        ]

    action = get_action(rule, isStaked, isThrottled)

    print("action=", action)
    # action[0] is the action for 1st simuulation (rpc/p2p)
    # action[1] is the action for 2nd simulation (build bundle)
    if action[0] == "ok":
        # should succeed
        for i in range(0, 2):
            UserOperation(
                sender=senders[i],
                signature=sig,
                paymasterAndData=paymasterAndData,
                initCode=initCodes[i],
            ).send().result
    elif action[0] == "drop":
        UserOperation(
            sender=senders[0],
            signature=sig,
            paymasterAndData=paymasterAndData,
            initCode=initCodes[0],
        ).send().result
        err = (
            UserOperation(
                sender=senders[0],
                signature=sig,
                paymasterAndData=paymasterAndData,
                initCode=initCodes[0],
            )
            .send()
            .error
        )
        assertRpcError(err, "", RPCErrorCode.BANNED_OR_THROTTLED_PAYMASTER)
    elif action[0] == "4":
        # special case for wallet: allow 4 entries in mempool (different nonces)
        for i in range(1, 5):
            UserOperation(
                sender=senders[0],
                signature=sig,
                paymasterAndData=paymasterAndData,
                nonce=i,
            ).send().result
        # the next will fail:
        err = (
            UserOperation(
                sender=senders[0],
                signature=sig,
                paymasterAndData=paymasterAndData,
                nonce=5,
            )
            .send()
            .error
        )
        assertRpcError(err, "", RPCErrorCode.BANNED_OR_THROTTLED_PAYMASTER)
    else:
        assert False, "unknown action" + action[0]

    # todo: validate mempool contains needed items?!

    # todo: validate we build bundle based on rule action[1]
