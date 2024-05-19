# extended reputation rules
import json
from dataclasses import dataclass

from tests.types import UserOperation
from tests.utils import deploy_contract, deploy_and_deposit, assert_ok, dump_reputation, \
    clear_reputation, set_reputation, to_number, send_bundle_now, dump_mempool
from eth_utils import to_hex

@dataclass
class Reputation:
    address: str
    opsSeen: str
    opsIncluded: str
    status: str


def get_reputation(addr):
    return Reputation(**[rep for rep in dump_reputation() if rep['address'] == addr][0])


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



# xEREP-020 A staked factory is "accountable" for account breaking the rules. \
# xEREP-030 A Staked Account is accountable for failures in other entities (`paymaster`, `aggregator`) even if they are staked.
# xEREP-040 An `aggregator` must be staked, regardless of storage usage.
