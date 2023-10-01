import pytest
from tests.types import UserOperation
from tests.utils import (
    dump_mempool,
    deploy_and_deposit,
    dump_reputation,
    deposit_to_undeployed_sender,
)

MIN_INCLUSION_RATE_DENOMINATOR = 10
THROTTLING_SLACK = 10
BAN_SLACK = 50


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


def assert_reputation_status(address, status):
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


@pytest.mark.parametrize("bundling_mode", ["manual"], ids=[""])
@pytest.mark.usefixtures("clear_state", "set_bundling_mode")
@pytest.mark.parametrize("case", ["with_factory", "without_factory"])
def test_staked_entity_reputation_threshold(
    w3, entrypoint_contract, paymaster_contract, factory_contract, case
):
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
                paymasterAndData=paymaster_contract.address,
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
                paymasterAndData=paymaster_contract.address,
            )
            for i in range(banning_threshold + 1)
        ]

    # Sending ops until the throttling threshold
    for i, userop in enumerate(wallet_ops[:throttling_threshold]):
        userop.send()
    mempool = dump_mempool()
    assert mempool == wallet_ops[:throttling_threshold]
    if case == "with_factory":
        assert_reputation_status(factory_contract.address, ReputationStatus.OK)
    else:
        assert_reputation_status(paymaster_contract.address, ReputationStatus.OK)
        assert_reputation_status(wallet.address, ReputationStatus.OK)

    # Going over throttling threshold
    wallet_ops[throttling_threshold].send()
    mempool = dump_mempool()
    assert mempool == wallet_ops[: throttling_threshold + 1]
    if case == "with_factory":
        assert_reputation_status(factory_contract.address, ReputationStatus.THROTTLED)
    else:
        assert_reputation_status(paymaster_contract.address, ReputationStatus.THROTTLED)
        assert_reputation_status(wallet.address, ReputationStatus.THROTTLED)

    # Sending the rest until banning threshold
    for i, userop in enumerate(
        wallet_ops[throttling_threshold + 1 : banning_threshold]
    ):
        userop.send()
    mempool = dump_mempool()
    assert mempool == wallet_ops[:banning_threshold]
    if case == "with_factory":
        assert_reputation_status(factory_contract.address, ReputationStatus.THROTTLED)
    else:
        assert_reputation_status(paymaster_contract.address, ReputationStatus.THROTTLED)
        assert_reputation_status(wallet.address, ReputationStatus.THROTTLED)

    # Going over banning threshold
    wallet_ops[banning_threshold].send()
    mempool = dump_mempool()
    assert mempool == wallet_ops
    if case == "with_factory":
        assert_reputation_status(factory_contract.address, ReputationStatus.BANNED)
    else:
        assert_reputation_status(paymaster_contract.address, ReputationStatus.BANNED)
        assert_reputation_status(wallet.address, ReputationStatus.BANNED)

    # tx_hash = wallet.functions.setState(0xdead).transact({"from": w3.eth.accounts[0]})
    # w3.eth.wait_for_transaction_receipt(tx_hash)
    # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # assert tx_receipt.status == 1, "Test error: could not call TestReputationAccount.setState() directly"
