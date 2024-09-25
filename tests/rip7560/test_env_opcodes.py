import pytest
from eth_utils import to_checksum_address

from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    assert_ok,
    deploy_contract,
    send_bundle_now,
    get_rip7560_tx_max_cost,
)

AA_ENTRYPOINT = "0x0000000000000000000000000000000000007560"
AA_SENDER_CREATOR = "0x00000000000000000000000000000000ffff7560"


def test_environment_introspection_opcodes(w3):
    account_abi = deploy_contract(w3, "rip7560/OpcodesTestAccount")
    factory = deploy_contract(w3, "rip7560/OpcodesTestAccountFactory")
    paymaster = deploy_contract(w3, "rip7560/OpcodesTestPaymaster", value=1 * 10**18)

    create_account_func = factory.functions.createAccount(1)
    sender = create_account_func.call()
    sender_contract = w3.eth.contract(abi=account_abi.abi, address=sender)

    tx = TransactionRIP7560(
        sender=sender,
        nonceKey=hex(0),
        nonce=hex(0),
        factory=factory.address,
        factoryData=create_account_func.build_transaction()["data"],
        paymaster=paymaster.address,
        maxFeePerGas=hex(400000000),
        maxPriorityFeePerGas=hex(400000000),
        authorizationData="0xface",
        executionData=account_abi.encode_abi(abi_element_identifier="saveEventOpcodes"),
    )

    paymaster_balance_before = w3.eth.get_balance(paymaster.address)

    ret = tx.send_skip_validation()
    assert_ok(ret)
    send_bundle_now()

    account_opcode_events = sender_contract.events.OpcodesEvent().get_logs()
    paymaster_opcode_events = paymaster.events.OpcodesEvent().get_logs()
    factory_opcode_events = factory.events.OpcodesEvent().get_logs()
    assert len(account_opcode_events) == 2
    assert len(paymaster_opcode_events) == 2
    assert len(factory_opcode_events) == 1

    tmp_deployment_gas_cost = (
        540000  # we should expose these values in the receipt and use the real ones
    )
    pre_charge = get_rip7560_tx_max_cost(tx)
    # paymaster balance should not change within the transaction runtime
    expected_paymaster_balance = paymaster_balance_before - pre_charge
    tmp_remaining_account_validation_gas = hex(
        int(str(tx.verificationGasLimit), 0) - tmp_deployment_gas_cost
    )
    validate_event(
        w3,
        tx,
        "factory-validation",
        factory.address,
        AA_SENDER_CREATOR,
        tx.verificationGasLimit,
        factory_opcode_events[0].args,
    )
    validate_event(
        w3,
        tx,
        "account-validation",
        sender,
        AA_ENTRYPOINT,
        tmp_remaining_account_validation_gas,
        account_opcode_events[0].args,
    )
    validate_event(
        w3,
        tx,
        "paymaster-validation",
        paymaster.address,
        AA_ENTRYPOINT,
        tx.paymasterVerificationGasLimit,
        paymaster_opcode_events[0].args,
        expected_paymaster_balance,
    )
    validate_event(
        w3,
        tx,
        "account-execution",
        sender,
        AA_ENTRYPOINT,
        tx.callGasLimit,
        account_opcode_events[1].args,
    )
    validate_event(
        w3,
        tx,
        "paymaster-postop",
        paymaster.address,
        AA_ENTRYPOINT,
        tx.paymasterPostOpGasLimit,
        paymaster_opcode_events[1].args,
        expected_paymaster_balance,
    )


# pylint: disable=too-many-arguments
def validate_event(
    w3, tx, tag, entity_address, caller, gas, event_args, expected_balance=None
):
    assert event_args.tag == tag
    struct = dict(event_args.opcodes)

    if expected_balance is None:
        expected_balance = w3.eth.get_balance(entity_address)
    block = w3.eth.get_block("latest", True)

    tx_prio = int(tx.maxPriorityFeePerGas, 16)
    tx_maxfee = int(tx.maxFeePerGas, 16)
    block_basefee = block.baseFeePerGas

    assert struct == {
        "TIMESTAMP": block.timestamp,
        "NUMBER": block.number,
        "CHAINID": 1337,
        "GAS": pytest.approx(int(gas, 16), rel=0.05),
        "GASLIMIT": block.gasLimit,
        "GASPRICE": min(tx_maxfee, tx_prio + block_basefee),
        "BALANCE": expected_balance,
        "SELFBALANCE": expected_balance,
        "ORIGIN": tx.sender,
        "CALLER": to_checksum_address(caller),
        "ADDRESS": entity_address,
        "COINBASE": block.miner,
        "BASEFEE": block.baseFeePerGas,
        "CALLVALUE": 0,
    }
