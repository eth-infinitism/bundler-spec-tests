from tests.rip7560.types import TransactionRIP7560
from tests.utils import assert_ok, deploy_contract, send_bundle_now

AA_ENTRYPOINT = "0x0000000000000000000000000000000000007560"
AA_SENDER_CREATOR = "0x00000000000000000000000000000000ffff7560"


def test_gas_usage_no_paymaster(w3, tx_7560):
    send_and_check_payment(w3, tx_7560)


def test_gas_usage_with_paymaster(w3, wallet_contract):
    paymaster = deploy_contract(w3, "rip7560/TestPaymaster", value=1 * 10**18)
    tx = TransactionRIP7560(
        sender=wallet_contract.address,
        nonceKey=hex(0),
        nonce=hex(1),
        paymaster=paymaster.address,
        maxFeePerGas=hex(100000000000),
        maxPriorityFeePerGas=hex(12345),
        authorizationData="0xface",
        executionData=wallet_contract.encode_abi(
            abi_element_identifier="anyExecutionFunction"
        ),
        # nonce = "0x1234"
    )
    send_and_check_payment(w3, tx)


# check transaction payments:
# - paymaster (or account) pays the gas
# - coinbase gets the tip
def send_and_check_payment(w3, tx: TransactionRIP7560):

    if tx.paymaster is not None:
        paymaster_pre_balance = w3.eth.get_balance(tx.paymaster)

    wallet_pre_balance = w3.eth.get_balance(tx.sender)
    coinbase_pre_balance = w3.eth.get_balance(w3.eth.get_block("latest").miner)
    ret = tx.send()
    assert_ok(ret)
    send_bundle_now()

    if tx.paymaster is not None:
        assert (
            w3.eth.get_balance(tx.sender) == wallet_pre_balance
        ), "wallet balance should not change"
    block = w3.eth.get_block("latest")

    coinbase_post_balance = w3.eth.get_balance(block.miner)
    coinbase_diff = coinbase_post_balance - coinbase_pre_balance
    # coinbase is paid for every tx in the block, and for each just the tip, not the full gas
    total_tx_tips = 0
    total_tx_cost = 0
    for txhash in block.transactions:
        rcpt = w3.eth.get_transaction_receipt(txhash)
        actual_priority = rcpt.effectiveGasPrice - block.baseFeePerGas
        used = rcpt.gasUsed

        if used > rcpt.cumulativeGasUsed:
            print(
                f"::warning {__file__} : gas_used field is BROKEN for 2nd TX. Workaround until AA-438 is fixed"
            )
            used = 21000

        if rcpt.type == 4:
            tx_cost = used * rcpt.effectiveGasPrice
            total_tx_cost = total_tx_cost + tx_cost

        print(f"{txhash.hex()} used {used} cumulative {rcpt.cumulativeGasUsed}")
        tip = actual_priority * used
        total_tx_tips += tip

    assert coinbase_diff == total_tx_tips

    if tx.paymaster is not None:
        paymaster_paid = paymaster_pre_balance - w3.eth.get_balance(tx.paymaster)
        assert paymaster_paid == total_tx_cost
    else:
        wallet_paid = wallet_pre_balance - w3.eth.get_balance(tx.sender)
        assert wallet_paid == total_tx_cost
