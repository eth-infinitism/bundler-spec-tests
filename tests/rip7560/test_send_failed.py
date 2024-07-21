import pytest
from tests.rip7560.types import TransactionRIP7560
from tests.utils import assert_rpc_error
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    deploy_contract,
    send_bundle_now
)
from tests.types import RPCErrorCode

AA_ENTRYPOINT = "0x0000000000000000000000000000000000007560"
AA_SENDER_CREATOR = "0x00000000000000000000000000000000ffff7560"


def test_send_failed():
    tx = TransactionRIP7560(
        sender='0x1111111111111111111111111111111111111111',
    )

    ret = tx.send()
    assert_rpc_error(
        ret, "invalid account return data length", RPCErrorCode.INVALID_INPUT
    )


def test_side_effects(w3):
    sender = deploy_contract(w3, "rip7560/TestAccountEnvInfo", value=1 * 10 ** 18)
    w3.eth.send_transaction(
        {"from": w3.eth.accounts[0], "to": sender.address, "value": 10 ** 18}
    )
    tx = TransactionRIP7560(
        sender=sender.address,
        nonce=hex(1),
        maxFeePerGas=hex(100000000000),
        maxPriorityFeePerGas=hex(100000000000),
        signature="0xface",
        callData=sender.encodeABI(fn_name="saveEventOpcodes"),
        # nonce = "0x1234"
    )

    # tx = tx_7560
    # assert tx_7560 == tx
    ret = tx.send()
    assert_ok(ret)
    send_bundle_now()
    opcodes = sender.functions.getStoredOpcodes().call()
    output = sender.functions.getStoredOpcodes().abi['outputs'][0]['components']
    opcodeNames = [item['name'] for item in output]

    assert len(opcodes) == len(opcodeNames), "fatal: struct length mismatch"
    struct = dict(zip(opcodeNames, opcodes))

    # TODO: need to calculate expected gas

    bal = w3.eth.get_balance(sender.address)
    block = w3.eth.get_block("latest", True)

    tx_prio = int(tx.maxPriorityFeePerGas,16)
    tx_maxfee = int(tx.maxFeePerGas,16)
    block_basefee = block.baseFeePerGas

    print("tx=", tx)
    assert struct == dict(
        TIMESTAMP=block.timestamp,
        NUMBER=block.number,
        CHAINID=1337,
        GAS=pytest.approx(int(tx.callGasLimit,16),rel=0.01),
        GASPRICE=min(tx_maxfee, tx_prio + block_basefee),
        BALANCE=bal,
        SELFBALANCE=bal,
        ORIGIN=sender.address,
        CALLER=AA_ENTRYPOINT,
        ADDRESS=sender.address,
        COINBASE=block.miner,
        BASEFEE=block.baseFeePerGas,
        CALLVALUE=0,
    )
