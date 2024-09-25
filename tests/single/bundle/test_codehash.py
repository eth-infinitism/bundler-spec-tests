import pytest
from tests.types import UserOperation
from tests.utils import (
    dump_mempool,
    send_bundle_now,
    deploy_contract,
)


def assert_useroperation_event(entrypoint_contract, userop, from_block):
    logs = entrypoint_contract.events.UserOperationEvent.getLogs(fromBlock=from_block)
    assert len(logs) == 1
    assert logs[0].args.sender == userop.sender


def assert_no_useroperation_event(entrypoint_contract, from_block):
    logs = entrypoint_contract.events.UserOperationEvent.getLogs(fromBlock=from_block)
    assert len(logs) == 0


def create_account(w3, codehash_factory_contract, entrypoint_contract, num):
    nonce = 123
    tx_hash = codehash_factory_contract.functions.create(
        nonce, num, entrypoint_contract.address
    ).transact({"from": w3.eth.default_account, "value": 10**18})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    logs = codehash_factory_contract.events.ContractCreated().process_receipt(receipt)
    account = logs[0].args.account
    codehash = w3.eth.get_proof(account, [])["codeHash"].hex()
    return account, codehash


@pytest.mark.usefixtures("manual_bundling_mode")
def test_codehash_changed(w3, entrypoint_contract):
    codehash_factory_contract = deploy_contract(w3, "TestCodeHashFactory")
    # Creating account with num == 0
    account0, codehash0 = create_account(
        w3, codehash_factory_contract, entrypoint_contract, 0
    )
    block_number = w3.eth.get_block_number()
    nonce = entrypoint_contract.functions.getNonce(account0, 123).call()
    userop = UserOperation(sender=account0, nonce=hex(nonce))
    response = userop.send()
    assert response.result, "userop dropped by bundler"
    assert dump_mempool() == [userop]
    # Calling SELFDESTRUCT before constructing the account on the same address with different code hash

    tx_hash = codehash_factory_contract.functions.destroy(account0).transact(
        {"from": w3.eth.default_account}
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)
    if len(w3.eth.get_code(account0)) != 0:
        pytest.skip("no self destruct. can't check code change..")
    # Creating account with num == 1
    account1, codehash1 = create_account(
        w3, codehash_factory_contract, entrypoint_contract, 1
    )
    assert account0 == account1, "could not create account on the same address"
    # assert codehash0 != codehash1, "could not create account with a different codehash"
    if codehash0 == codehash1:
        pytest.skip(
            "selfdestruct opcode removed, no need for a codehash change test anymore."
        )
    send_bundle_now()
    # Asserting that the even though second simulation passes, codehash change is sufficient to remove a userop
    # so no bundle was sent.
    assert_no_useroperation_event(entrypoint_contract, from_block=block_number)
    # Bundler should drop the op from the mempool after codehash changed
    assert dump_mempool() == []
    # Sanity check: reconstructing the accounts again to see that they can be bundled
    for i in range(2):
        tx_hash = codehash_factory_contract.functions.destroy(account0).transact(
            {"from": w3.eth.default_account}
        )
        w3.eth.wait_for_transaction_receipt(tx_hash)
        block_number = w3.eth.get_block_number()
        create_account(w3, codehash_factory_contract, entrypoint_contract, i)
        userop.nonce = hex(i)
        userop.send()
        assert dump_mempool() == [userop]
        send_bundle_now()
        assert dump_mempool() == []
        assert_useroperation_event(entrypoint_contract, userop, from_block=block_number)
