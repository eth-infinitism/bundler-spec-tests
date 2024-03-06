from dataclasses import dataclass
import pytest
from tests.types import UserOperation
from tests.utils import (
    assert_ok,
    clear_mempool,
    deploy_and_deposit,
    dump_reputation,
    deposit_to_undeployed_sender,
)

MIN_INCLUSION_RATE_DENOMINATOR = 10
THROTTLING_SLACK = 10
BAN_SLACK = 50

THROTTLED_ENTITY_MEMPOOL_COUNT = 4


@dataclass()
class ReputationStatus:
    OK = 0
    THROTTLED = 1
    BANNED = 2


def get_max_seen(ops_seen):
    return ops_seen / MIN_INCLUSION_RATE_DENOMINATOR


def is_banned(max_seen, ops_included):
    return max_seen > ops_included + BAN_SLACK


def is_throttled(max_seen, ops_included):
    return max_seen > ops_included + THROTTLING_SLACK


def assert_reputation_status(address, status, ops_seen=None, ops_included=None):
    reputations = dump_reputation()
    reputation = next(
        (
            rep
            for rep in reputations
            if rep.get("address", "").lower() == address.lower()
        ),
        None,
    )
    assert reputation is not None, "Could not find reputation of " + address.lower()
    assert int(reputation.get("status", "-0x1"), 16) == status, (
        "Incorrect reputation status of " + address.lower()
    )
    assert ops_seen is None or ops_seen == int(
        reputation.get("opsSeen"), 16
    ), "opsSeen mismatch"
    assert ops_included is None or ops_included == int(
        reputation.get("opsIncluded"), 16
    ), "opsIncluded mismatch"


@pytest.mark.usefixtures("clear_state", "manual_bundling_mode")
@pytest.mark.parametrize("case", ["with_factory", "without_factory"])
def test_staked_entity_reputation_threshold(w3, entrypoint_contract, case):
    if case == "with_factory":
        factory_contract = deploy_and_deposit(
            w3, entrypoint_contract, "TestRulesFactory", True
        )
    paymaster_contract = deploy_and_deposit(
        w3, entrypoint_contract, "TestRulesPaymaster", True
    )
    reputations = dump_reputation()
    ops_included = next(
        (rep for rep in reputations if rep.address == paymaster_contract.address), {}
    ).get("opsIncluded", 0)
    throttling_threshold = (
        (ops_included + THROTTLING_SLACK) * MIN_INCLUSION_RATE_DENOMINATOR
        + MIN_INCLUSION_RATE_DENOMINATOR
        - 1
    )
    banning_threshold = (
        (ops_included + BAN_SLACK) * MIN_INCLUSION_RATE_DENOMINATOR
        + MIN_INCLUSION_RATE_DENOMINATOR
        - 1
    )

    if case == "with_factory":
        initcodes = [
            (
                factory_contract.address
                + factory_contract.functions.create(
                    i, "", entrypoint_contract.address
                ).build_transaction()["data"][2:]
            )
            for i in range(banning_threshold + 1)
        ]
        wallet_ops = [
            UserOperation(
                sender=deposit_to_undeployed_sender(
                    w3, entrypoint_contract, initcodes[i]
                ),
                nonce=hex(i << 64),
                paymaster=paymaster_contract.address,
                initCode=initcodes[i],
            )
            for i in range(banning_threshold + 1)
        ]
    else:
        wallet = deploy_and_deposit(
            w3, entrypoint_contract, "TestReputationAccount", True
        )
        # Creating enough user operations until banning threshold
        wallet_ops = [
            UserOperation(
                sender=wallet.address,
                nonce=hex(i << 64),
                paymaster=paymaster_contract.address,
            )
            for i in range(banning_threshold + 1)
        ]

    # Sending ops until the throttling threshold
    for i, userop in enumerate(wallet_ops[:throttling_threshold]):
        if i % THROTTLED_ENTITY_MEMPOOL_COUNT == 0:
            clear_mempool()
        assert_ok(userop.send())

    if case == "with_factory":
        assert_reputation_status(
            factory_contract.address,
            ReputationStatus.OK,
            ops_seen=throttling_threshold,
            ops_included=0,
        )
    else:
        assert_reputation_status(
            paymaster_contract.address,
            ReputationStatus.OK,
            ops_seen=throttling_threshold,
            ops_included=0,
        )
        assert_reputation_status(
            wallet.address,
            ReputationStatus.OK,
            ops_seen=throttling_threshold,
            ops_included=0,
        )

    # Going over throttling threshold
    wallet_ops[throttling_threshold].send()

    if case == "with_factory":
        assert_reputation_status(
            factory_contract.address,
            ReputationStatus.THROTTLED,
            ops_seen=throttling_threshold + 1,
            ops_included=0,
        )
    else:
        assert_reputation_status(
            paymaster_contract.address,
            ReputationStatus.THROTTLED,
            ops_seen=throttling_threshold + 1,
            ops_included=0,
        )
        assert_reputation_status(
            wallet.address,
            ReputationStatus.THROTTLED,
            ops_seen=throttling_threshold + 1,
            ops_included=0,
        )

    # Sending the rest until banning threshold
    for i, userop in enumerate(
        wallet_ops[throttling_threshold + 1 : banning_threshold]
    ):
        if i % THROTTLED_ENTITY_MEMPOOL_COUNT == 0:
            clear_mempool()
        assert_ok(userop.send())

    if case == "with_factory":
        assert_reputation_status(
            factory_contract.address,
            ReputationStatus.THROTTLED,
            ops_seen=banning_threshold,
            ops_included=0,
        )
    else:
        assert_reputation_status(
            paymaster_contract.address,
            ReputationStatus.THROTTLED,
            ops_seen=banning_threshold,
            ops_included=0,
        )
        assert_reputation_status(
            wallet.address,
            ReputationStatus.THROTTLED,
            ops_seen=banning_threshold,
            ops_included=0,
        )

    # Going over banning threshold
    wallet_ops[banning_threshold].send()

    if case == "with_factory":
        assert_reputation_status(
            factory_contract.address,
            ReputationStatus.BANNED,
            ops_seen=banning_threshold + 1,
            ops_included=0,
        )
    else:
        assert_reputation_status(
            paymaster_contract.address,
            ReputationStatus.BANNED,
            ops_seen=banning_threshold + 1,
            ops_included=0,
        )
        assert_reputation_status(
            wallet.address,
            ReputationStatus.BANNED,
            ops_seen=banning_threshold + 1,
            ops_included=0,
        )

    # tx_hash = wallet.functions.setState(0xdead).transact({"from": w3.eth.accounts[0]})
    # w3.eth.wait_for_transaction_receipt(tx_hash)
    # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # assert tx_receipt.status == 1, "Test error: could not call TestReputationAccount.setState() directly"
