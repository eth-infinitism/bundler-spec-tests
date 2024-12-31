# extended reputation rules
import pytest
from dataclasses import dataclass
import pytest

from tests.single.bundle.test_storage_rules import deploy_staked_rule_factory
from tests.conftest import rules_staked_account_contract
from tests.single.bundle.test_storage_rules import deploy_staked_rule_factory
from tests.user_operation_erc4337 import UserOperation
from tests.utils import (
    deploy_contract,
    deploy_and_deposit,
    assert_ok,
    dump_reputation,
    clear_reputation,
    set_reputation,
    staked_contract,
    to_number,
    send_bundle_now,
    dump_mempool,
    to_prefixed_hex,
)
from eth_utils import to_hex


@dataclass
class Reputation:
    address: str
    opsSeen: int = 0
    opsIncluded: int = 0
    status: int = 0

    def __post_init__(self):
        self.address = self.address.lower()
        self.opsSeen = to_number(self.opsSeen)
        self.opsIncluded = to_number(self.opsIncluded)
        self.status = to_number(self.status)


def get_reputation(addr, reputations=None):
    if reputations is None:
        reputations = dump_reputation()
    addr = addr.lower()
    reps = [rep for rep in reputations if rep["address"].lower() == addr]

    if len(reps) == 0:
        rep = Reputation(address=addr, opsSeen=0, opsIncluded=0, status=0)
    else:
        rep = Reputation(**reps[0])

    return rep


def get_reputations(addrs):
    reputations = dump_reputation()
    return [get_reputation(addr, reputations) for addr in addrs]


# EREP-015 A `paymaster` should not have its opsSeen incremented on failure of factory or account
def test_paymaster_on_account_failure(w3, entrypoint_contract, manual_bundling_mode):
    """
    - paymaster with some reputation value (nonezero opsSeen/opsIncluded)
    - submit userop that passes validation
    - paymaster's opsSeen incremented in-memory
    - 2nd validation fails (because of account/factory)
    - paymaster's opsSeen should remain the same
    """
    account = deploy_contract(
        w3, "TestReputationAccount", [entrypoint_contract.address], 10**18
    )
    paymaster = deploy_and_deposit(
        w3, entrypoint_contract, "TestRulesPaymaster", staked=True
    )
    clear_reputation()
    set_reputation(paymaster.address, ops_seen=5, ops_included=2)
    pre = get_reputation(paymaster.address)
    assert_ok(
        UserOperation(
            sender=account.address,
            paymaster=paymaster.address,
            paymasterVerificationGasLimit=to_hex(50000),
            paymasterData=to_hex(text="nothing"),
        ).send()
    )
    # userop in mempool opsSeen was advanced
    post_submit = get_reputation(paymaster.address)
    assert to_number(pre.opsSeen) == to_number(post_submit.opsSeen) - 1

    # make OOB state change to make UserOp in mempool to fail
    account.functions.setState(0xDEAD).transact({"from": w3.eth.default_account})
    send_bundle_now()
    post = get_reputation(paymaster.address)
    assert post == pre


# EREP-020: A staked factory is "accountable" for account breaking the rules.
def test_staked_factory_on_account_failure(
    w3, entrypoint_contract, manual_bundling_mode
):
    factory = deploy_and_deposit(
        w3, entrypoint_contract, "TestReputationAccountFactory", staked=True
    )

    pre = get_reputation(factory.address)
    for i in range(2):
        factory_data = factory.functions.create(i).build_transaction()["data"]
        account = w3.eth.call({"to": factory.address, "data": factory_data})[12:]
        w3.eth.send_transaction(
            {"from": w3.eth.default_account, "to": account, "value": 10**18}
        )
        assert_ok(
            UserOperation(
                sender=account,
                verificationGasLimit=to_hex(5000000),
                factory=factory.address,
                factoryData=factory_data,
                signature=to_prefixed_hex("revert"),
            ).send()
        )

    # cause 2nd account to revert in bundle creation
    factory.functions.setAccountState(0xDEAD).transact({"from": w3.eth.default_account})
    send_bundle_now()
    assert get_reputation(factory.address).opsSeen >= 10000


# EREP-030 A Staked Account is accountable for failures in other entities (`paymaster`, `aggregator`) even if they are staked.
@pytest.mark.parametrize("staked_acct", ["staked", "unstaked"])
def test_account_on_entity_failure(
    w3, entrypoint_contract, manual_bundling_mode, staked_acct, rules_account_contract
):
    clear_reputation()
    # userop with staked account, and a paymaster.
    # after submission to mempool, we will make paymaster fail 2nd validation
    # (the simplest way to make the paymaster fail is withdraw its deposit)
    sender = rules_account_contract
    if staked_acct == "staked":
        print("staking account", sender)
        staked_contract(w3, entrypoint_contract, sender)
    else:
        print("unstaked account", sender)

    paymaster = deploy_and_deposit(
        w3, entrypoint_contract, "TestSimplePaymaster", False
    )

    assert get_reputations([sender.address, paymaster.address]) == [
        Reputation(address=sender.address, opsSeen=0),
        Reputation(address=paymaster.address, opsSeen=0),
    ], "pre: no reputation"

    assert_ok(UserOperation(sender=sender.address, paymaster=paymaster.address).send())

    if staked_acct == "staked":
        assert get_reputations([sender.address, paymaster.address]) == [
            Reputation(address=sender.address, opsSeen=1),
            Reputation(address=paymaster.address, opsSeen=1),
        ], "valid userop. both staked account and paymaster have opsSeen increment"
    else:
        assert get_reputations([sender.address, paymaster.address]) == [
            Reputation(address=sender.address, opsSeen=0),
            Reputation(address=paymaster.address, opsSeen=1),
        ], "valid userop. staked paymaster should have opsSeen increment"

    # drain paymaster, so it would revert
    pm_balance = entrypoint_contract.functions.balanceOf(paymaster.address).call()
    paymaster.functions.withdrawTo(sender.address, pm_balance).transact(
        {"from": w3.eth.default_account}
    )

    bn = w3.eth.block_number
    send_bundle_now()
    assert w3.eth.block_number == bn, "bundle should revert, and not submitted"

    if staked_acct == "staked":
        assert get_reputations([sender.address, paymaster.address]) == [
            Reputation(address=sender.address, opsSeen=1),
            Reputation(address=paymaster.address, opsSeen=0),
        ], "staked account should be blamed instead of paymaster"
    else:
        assert get_reputations([sender.address, paymaster.address]) == [
            Reputation(address=sender.address, opsSeen=0),
            Reputation(address=paymaster.address, opsSeen=1),
        ]
