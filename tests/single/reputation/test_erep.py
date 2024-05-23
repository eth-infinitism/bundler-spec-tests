# extended reputation rules

import pytest
from dataclasses import dataclass

from tests.single.bundle.test_storage_rules import deploy_staked_rule_factory
from tests.types import UserOperation
from tests.utils import deploy_contract, deploy_and_deposit, assert_ok, dump_reputation, \
    clear_reputation, set_reputation, to_number, send_bundle_now, dump_mempool, to_prefixed_hex, compile_contract
from eth_utils import to_hex

@dataclass
class Reputation:
    address: str
    opsSeen: int
    opsIncluded: int
    status: str

    def __post_init__(self):
        self.address = self.address.lower()
        self.opsSeen = to_number(self.opsSeen)
        self.opsIncluded = to_number(self.opsIncluded)


def get_reputation(addr):
    return Reputation(**[rep for rep in dump_reputation() if rep['address'].lower() == addr.lower()][0])


# EREP-015 A `paymaster` should not have its opsSeen incremented on failure of factory or account
def test_paymaster_on_account_failure(w3, entrypoint_contract, manual_bundling_mode):
    """
    - paymaster with some reputation value (nonezero opsSeen/opsIncluded)
    - submit userop that passes validation
    - paymaster's opsSeen incremented in-memory
    - 2nd validation fails (because of account/factory)
    - paymaster's opsSeen should remain the same
    """
    account = deploy_contract(w3, 'TestReputationAccount', [entrypoint_contract.address], 10 ** 18)
    paymaster = deploy_and_deposit(w3, entrypoint_contract, "TestRulesPaymaster", staked=True)
    clear_reputation()
    set_reputation(paymaster.address, ops_seen=5, ops_included=2)
    pre = get_reputation(paymaster.address)
    assert_ok(UserOperation(
        sender=account.address,
        paymaster=paymaster.address,
        paymasterVerificationGasLimit=50000,
        paymasterData=to_hex(text="nothing"),
    ).send())
    print("== mempool=",dump_mempool())
    # userop in mempool opsSeen was advanced
    post_submit = get_reputation(paymaster.address)
    assert to_number(pre.opsSeen) == to_number(post_submit.opsSeen) - 1

    # make OOB state change to make UserOp in mempool to fail
    account.functions.setState(0xdead).transact({"from": w3.eth.accounts[0]})
    send_bundle_now()
    post = get_reputation(paymaster.address)
    assert post == pre


# EREP-020: A staked factory is "accountable" for account breaking the rules.
def test_staked_factory_on_account_failure(w3, entrypoint_contract, manual_bundling_mode):
    factory = deploy_and_deposit(w3, entrypoint_contract, "TestReputationAccountFactory", staked=True)
    factory_data = factory.functions.create(123).buildTransaction()['data']
    account = w3.eth.call({"to": factory.address, "data": factory_data})[12:]

    w3.eth.send_transaction({"from": w3.eth.accounts[0], "to": account, "value": 10 ** 18})
    clear_reputation()
    set_reputation(factory.address, ops_seen=5, ops_included=2)
    pre = get_reputation(factory.address)

    assert_ok(UserOperation(
        sender=account,
        verificationGasLimit=to_hex(5000000),
        factory=factory.address,
        factoryData=factory_data,
        signature=to_prefixed_hex("revert"),
    ).send())

    # cause account to revert its validation:
    factory.functions.setAccountState(0xdead).transact({"from": w3.eth.accounts[0]})
    send_bundle_now()
    post = get_reputation(factory.address)
    assert post.opsSeen == pre.opsSeen+1
    assert post.opsIncluded == pre.opsIncluded

