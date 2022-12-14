import re

import pytest
from web3 import constants
from tests.utils import deploy_contract, deploy_wallet_contract, UserOperation, RPCRequest, assertRpcError
from tests.types import RPCErrorCode

ADDRESS_ZERO = constants.ADDRESS_ZERO


ruletable = '''
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
'''

# see actions in https://docs.google.com/document/d/1DFX5hUhv_fwqC7wez6SBT3pWTGfSDiV45NyXllhxYik/edit?usp=sharing
ok = 'ok'
throttle = 1
drop = 'drop'

# keys are rules to pass to our entity
# values are 6 columns: 2 columns for each scenario of (unstaked, staked, staked+throttle)
# the 2 are rule for 1st simulation (rpc/p2p) and rule for 2nd simulation (bundling)
rules = dict(
    no_storage=[ok, ok, ok, ok, throttle, throttle],
    acct_ref_noinit=[ok, ok, ok, ok, throttle, throttle],
    acct_ref_init=[drop, drop, ok, ok, throttle, throttle],
    acct_storage=[ok, ok, ok, ok, throttle, throttle],
    ent_storage=[drop, drop, ok, ok, throttle, throttle],
    ent_ref=[drop, drop, ok, ok, throttle, throttle],

    # not a real rule: sender is entity just like others.
    # entSender=[4, 1, ok, ok, throttle, throttle],
)


def get_action(rule, isStake, isThrottled=False):
    '''
    :param rule: row in the table
    :param isStake: False for cols 1,2 True for 3,4
    :param isThrottled for st-throttled column (5,6)
    :return: [rule1, rule2] - rule for 1st and 2nd simulation
    '''
    r = rules[rule]
    if r is None: raise Exception("unknown rule: " + rule)
    index = 0 if not isStake else 2 if not isThrottled else 4
    return r[index:index + 2]

def setThrottled(ent):
    # todo: set proper values that will consider it "throttled"
    RPCRequest(method='aa_setReputation', params=[{
        'reputation': {
            ent.address: {
                'opsSeen': 1,
                'opsIncluded': 2
            }
        }
    }]).send().result


@pytest.mark.parametrize('rule', rules.keys())
@pytest.mark.parametrize('entity', ['factory', 'sender', 'paymaster'])
@pytest.mark.parametrize('isStake', [False, True])
@pytest.mark.parametrize('isThrottled', [False, True])
def test_stake_rule(clearState, w3, entity, rule, isStake, isThrottled):
    # remove unsupported combinations
    if isThrottled and not isStake: return
    # the "init/noinit" rules are for all entities but factory
    # (they check other entity with/without factory
    if rule.find('init') > 0 and entity == 'factory': return
    # if rule == 'entSender' and entity != 'sender': return

    # depending on entity, fill in the fields
    # (paymaster is a single string. factory is an array, since it needs different
    # ctr params to create 2 separate accounts)
    # either initCodes or sender is empty
    initCodes = []
    senders = []
    paymasterAndData = '0x'
    ent = None
    sig = '0x'
    # testing (sender, paymaster) but with initCode
    if rule.find('-init') > 0:
        factory = deploy_contract('TestFactory')
        # TODO: append createAccount signature (for 2 wallets)
        initCodes = [
            ent.address + ent.createAccount(1).build_transaction(),
            ent.address + ent.createAccount(2).build_transaction()
        ]
        senders = [
            entryPoint.getSenderAddress(initCodes[0]),
            entryPoint.getSenderAddress(initCodes[1]),
        ]
        #remove the init/noinit marker from the rule
        rule = re.sub('-(no)?init','')

    if entity == 'paymaster':
        ent = deploy_contract(w3, 'TestPaymaster')
        paymasterAndData = ent.address + rule.encode().hex()
    elif entity == 'factory':
        ent = deploy_contract(w3, 'TestFactory')
        # TODO: append method signature (for 2 wallets
        initCodes = [
            ent.address + ent.createAccount(1, rule).build_transaction(),
            ent.address + ent.createAccount(2, rule).build_transaction()
        ]
        senders = [
            entryPoint.getSenderAddress(initCodes[0]),
            entryPoint.getSenderAddress(initCodes[1]),
        ]
    elif entity == 'sender':
        ent = deploy_wallet_contract()
        sig = '0x' + rule.encode().hex()
        senders = [ent, ent]
    else:
        raise Exception("unknown entity", entity)
        paymaster = deploy_contract('TestPaymaster')
    if isStake:
        ent.addStake(entryPoint, 1)
        if isThrottled:
            setThrottled(ent)
    action = get_action(rule, isStake, isThrottled)
    # action[0] is the action for 1st simuulation (rpc/p2p)
    # action[1] is the action for 2nd simulation (build bundle)
    if action[0] == 'ok':
        # should succeed
        for i in range(0, 2):
            UserOperation(sender=senders[i], signature=sig, paymasterAndData=paymasterAndData, initCode=initCodes[i]).send().result
    elif action[0] == 'drop':
        UserOperation(sender=senders[0], signature=sig, paymasterAndData=paymasterAndData, initCode=initCodes[0]).send().result
        err = UserOperation(sender=senders[0], signature=sig, paymasterAndData=paymasterAndData, initCode=initCodes[0]).send().error
        assertRpcError(err, '', RPCErrorCode.BANNED_OR_THROTTLED_PAYMASTER)
    elif action[0] == '4':
        # special case for wallet: allow 4 entries in mempool (different nonces)
        for i in range(0, 4):
            UserOperation(sender=senders[0], signature=sig, paymasterAndData=paymasterAndData, nonce=i).send().result
        # the next will fail:
        err = UserOperation(sender=senders[0], signature=sig, paymasterAndData=paymasterAndData, nonce=5).send().error
        assertRpcError(err, '', RPCErrorCode.BANNED_OR_THROTTLED_PAYMASTER)
    else:
        assert False, "unknown action" + action[0]

    # todo: validate mempool contains needed items?!

    # todo: validate we build bundle based on rule action[1]
