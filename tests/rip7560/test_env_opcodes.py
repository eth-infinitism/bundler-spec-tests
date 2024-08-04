import pytest
from tests.rip7560.types import TransactionRIP7560
from tests.utils import assert_ok, deploy_contract, send_bundle_now

AA_ENTRYPOINT = "0x0000000000000000000000000000000000007560"
AA_SENDER_CREATOR = "0x00000000000000000000000000000000ffff7560"


def test_side_effects(w3):
    sender = deploy_contract(w3, "rip7560/TestAccountEnvInfo", value=1 * 10**18)
    paymaster = deploy_contract(w3, "rip7560/TestPaymaster", value=1 * 10**18)
    tx = TransactionRIP7560(
        sender=sender.address,
        nonce=hex(1),
        paymaster=paymaster.address,
        maxFeePerGas=hex(100000000000),
        maxPriorityFeePerGas=hex(12345),
        signature="0xface",
        callData=sender.encodeABI(fn_name="saveEventOpcodes"),
        # nonce = "0x1234"
    )

    # tx = tx_7560
    # assert tx_7560 == tx
    ret = tx.send()
    assert_ok(ret)
    send_bundle_now()
    event_args = sender.events.OpcodesEvent().get_logs()[0].args
    assert event_args.tag == "exec"
    struct = dict(event_args.opcodes)

    bal = w3.eth.get_balance(sender.address)
    block = w3.eth.get_block("latest", True)

    tx_prio = int(tx.maxPriorityFeePerGas, 16)
    tx_maxfee = int(tx.maxFeePerGas, 16)
    block_basefee = block.baseFeePerGas

    assert struct == {
        "TIMESTAMP": block.timestamp,
        "NUMBER": block.number,
        "CHAINID": 1337,
        "GAS": pytest.approx(int(tx.callGasLimit, 16), rel=0.01),
        "GASLIMIT": block.gasLimit,
        "GASPRICE": min(tx_maxfee, tx_prio + block_basefee),
        "BALANCE": bal,
        "SELFBALANCE": bal,
        "ORIGIN": sender.address,
        "CALLER": AA_ENTRYPOINT,
        "ADDRESS": sender.address,
        "COINBASE": block.miner,
        "BASEFEE": block.baseFeePerGas,
        "CALLVALUE": 0,
    }
