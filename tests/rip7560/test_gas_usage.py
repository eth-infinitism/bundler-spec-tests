import pytest
from tests.rip7560.types import TransactionRIP7560
from tests.utils import assert_ok, deploy_contract, send_bundle_now

AA_ENTRYPOINT = "0x0000000000000000000000000000000000007560"
AA_SENDER_CREATOR = "0x00000000000000000000000000000000ffff7560"


def test_gas_usage(w3, wallet_contract):
    paymaster = deploy_contract(w3, "rip7560/TestPaymaster", value=1 * 10**18)
    tx = TransactionRIP7560(
        sender=wallet_contract.address,
        nonceKey=hex(0),
        nonce=hex(1),
        paymaster=paymaster.address,
        maxFeePerGas=hex(100000000000),
        maxPriorityFeePerGas=hex(12345),
        authorizationData="0xface",
        executionData=wallet_contract.encodeABI(fn_name="anyExecutionFunction"),
        # nonce = "0x1234"
    )

    coinbase_pre_balance = w3.eth.get_balance(w3.eth.get_block("latest").miner)
    # tx = tx_7560
    # assert tx_7560 == tx
    ret = tx.send()
    assert_ok(ret)
    send_bundle_now()

    bal = w3.eth.get_balance(wallet_contract.address)
    block = w3.eth.get_block("latest")

    tx_prio = int(tx.maxPriorityFeePerGas, 16)
    tx_max_fee = int(tx.maxFeePerGas, 16)
    block_base_fee = block.baseFeePerGas

    tx_gas_price = min(tx_max_fee, tx_prio + block_base_fee)

    coinbase_post_balance = w3.eth.get_balance(block.miner)
    coinbase_diff = coinbase_post_balance - coinbase_pre_balance
    # coinbase is paid for every tx in the block, and for each just the tip, not the full gas
    total_tx_tips = 0
    for txhash in block.transactions:
        rcpt = w3.eth.get_transaction_receipt(txhash)
        actual_priority = rcpt.effectiveGasPrice - block.baseFeePerGas
        used = rcpt.gasUsed
        cum = rcpt.cumulativeGasUsed
        # TODO: gas_used field is broken for NORMAL tx (ok for type 4)
        if used > rcpt.cumulativeGasUsed:
            used = 21000
        tip = actual_priority * used
        print(
            "== tx gas",
            used,
            cum,
            "tip",
            tip,
            "actual_priority",
            actual_priority,
            "basefee",
            block.baseFeePerGas,
        )
        total_tx_tips += tip

    # total_tx_tips = sum([tx.maxPriorityFeePerGas for tx in block.transactions])

    assert coinbase_diff == total_tx_tips
