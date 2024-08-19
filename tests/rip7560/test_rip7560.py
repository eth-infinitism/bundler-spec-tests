import hexbytes
import pytest
from web3.constants import ADDRESS_ZERO

from tests.single.opbanning.test_op_banning import banned_opcodes
from tests.types import RPCErrorCode
from tests.rip7560.types import TransactionRIP7560

from tests.utils import (
    assert_ok,
    assert_rpc_error,
    fund,
    send_bundle_now,
    to_prefixed_hex,
    deploy_contract,
    compile_contract,
)


def test_eth_sendTransaction7560_valid1(w3, wallet_contract, tx_7560):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    nonce = w3.eth.get_transaction_count(tx_7560.sender)
    # created contract has nonce==1
    assert nonce == 1
    res = tx_7560.send()
    rethash = res.result
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 2
    assert nonce + 1 == w3.eth.get_transaction_count(
        tx_7560.sender
    ), "nonce not incremented"
    ev = wallet_contract.events.AccountExecutionEvent().get_logs()[0]
    evhash = ev.transactionHash.to_0x_hex()
    assert rethash == evhash
    assert wallet_contract.address == ev.address
    w3.eth.get_transaction(rethash)


def test_eth_sendTransaction7560_valid_with_paymaster_no_postop(
    w3, wallet_contract, tx_7560
):
    tx_7560.maxPriorityFeePerGas = hex(12345)
    paymaster = deploy_contract(w3, "rip7560/TestPostOpPaymaster", value=10**18)
    counter_before = paymaster.functions.counter().call()
    state_before = wallet_contract.functions.state().call()
    assert counter_before == 0
    assert state_before == 0
    tx_7560.paymaster = paymaster.address
    tx_7560.authorizationData = to_prefixed_hex("no context")
    tx_7560.executionData = wallet_contract.encodeABI(fn_name="anyExecutionFunction")
    res = tx_7560.send()
    assert_ok(res)
    send_bundle_now()
    counter_after = paymaster.functions.counter().call()
    state_after = wallet_contract.functions.state().call()
    assert counter_after == 0, "context empty but postOp was called"
    assert state_after == 2, "execution failed to change state"


def test_eth_sendTransaction7560_valid_with_paymaster_postop(
    w3, wallet_contract, tx_7560
):
    tx_7560.maxPriorityFeePerGas = hex(12345)
    paymaster = deploy_contract(w3, "rip7560/TestPostOpPaymaster", value=10**18)
    counter_before = paymaster.functions.counter().call()
    state_before = wallet_contract.functions.state().call()
    assert counter_before == 0
    assert state_before == 0
    tx_7560.paymaster = paymaster.address
    tx_7560.executionData = wallet_contract.encodeABI(fn_name="anyExecutionFunction")
    res = tx_7560.send()
    assert_ok(res)
    send_bundle_now()
    counter_after = paymaster.functions.counter().call()
    state_after = wallet_contract.functions.state().call()
    assert counter_after == 1, "postOp failed to change state"
    assert state_after == 2, "execution failed to change state"


def test_eth_sendTransaction7560_valid_with_paymaster_postop_revert(
    w3, wallet_contract, tx_7560
):
    tx_7560.maxPriorityFeePerGas = hex(12345)
    paymaster = deploy_contract(w3, "rip7560/TestPostOpPaymaster", value=10**18)
    counter_before = paymaster.functions.counter().call()
    state_before = wallet_contract.functions.state().call()
    assert counter_before == 0
    assert state_before == 0
    tx_7560.paymaster = paymaster.address
    tx_7560.executionData = wallet_contract.encodeABI(fn_name="anyExecutionFunction")
    tx_7560.authorizationData = to_prefixed_hex("revert")
    res = tx_7560.send()
    assert_ok(res)
    send_bundle_now()
    counter_after = paymaster.functions.counter().call()
    state_after = wallet_contract.functions.state().call()
    assert (
        counter_after == 0
    ), "postOp failed but paymaster postOp state change did not revert"
    assert state_after == 1, "postOp failed but execution state change did not revert"


def test_getTransaction(w3, wallet_contract, tx_7560):
    res = tx_7560.send()
    rethash = res.result
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 2
    tx = dict(w3.eth.get_transaction(rethash))
    block = w3.eth.get_block("latest")

    expected_ret_fields = dict(
        type=4,
        blockHash=block["hash"],
        blockNumber=block["number"],
        gasPrice=min(
            int(tx_7560.maxFeePerGas, 16),
            block["baseFeePerGas"] + int(tx_7560.maxPriorityFeePerGas, 16),
        ),
        transactionIndex=0,
        hash=hexbytes.HexBytes(rethash),
        chainId=int(tx_7560.chainId, 16),
        sender=tx_7560.sender.lower(),
        nonceKey=tx_7560.nonceKey,
        nonce=int(tx_7560.nonce, 16),
        maxFeePerGas=int(tx_7560.maxFeePerGas, 16),
        maxPriorityFeePerGas=int(tx_7560.maxPriorityFeePerGas, 16),
        verificationGasLimit=tx_7560.verificationGasLimit,
        value=int(tx_7560.value, 16),
        builderFee=tx_7560.builderFee,
        paymaster=tx_7560.paymaster,
        paymasterData=tx_7560.paymasterData,
        paymasterVerificationGasLimit=tx_7560.paymasterVerificationGasLimit,
        paymasterPostOpGasLimit=tx_7560.paymasterPostOpGasLimit,
        factory=tx_7560.factory,
        factoryData=tx_7560.factoryData,
        authorizationData=tx_7560.authorizationData,
        executionData=tx_7560.executionData,
        # stopped filling in the unrelated "input" filed to be consistent with renaming "calldata" to "executionData"
        input=hexbytes.HexBytes(""),
        # mapped fields (use standard TX names, not rip7560 names)
        gas=int(tx_7560.callGasLimit, 16),
    )
    # remove "nulls"
    expected_ret_fields = {
        k: v for k, v in expected_ret_fields.items() if v is not None
    }

    # "from" field: there is no good value for it, and it is mandatory.
    assert tx["from"] == ADDRESS_ZERO
    del tx["from"]

    assert expected_ret_fields == tx


# assert the account is charged by the gas used in the tx
def test_eth_send_gas_usage(w3, tx_7560):
    tx_7560.maxPriorityFeePerGas = hex(12345)
    balance = w3.eth.get_balance(tx_7560.sender)
    res = tx_7560.send()
    assert_ok(res)
    send_bundle_now()
    rcpt = w3.eth.get_transaction_receipt(res.result)
    balance_after = w3.eth.get_balance(tx_7560.sender)
    rcpt_effective_gas_price = rcpt.effectiveGasPrice
    block = w3.eth.get_block(rcpt.blockHash)
    tx_max_fee_per_gas = int(tx_7560.maxFeePerGas, 16)
    tx_max_priority_fee_per_gas = int(tx_7560.maxPriorityFeePerGas, 16)
    block_base_fee = block.baseFeePerGas

    print("effectiveGasPrice", rcpt_effective_gas_price, "baseFee", block_base_fee)
    assert rcpt.gasUsed > 0
    assert rcpt_effective_gas_price == min(
        block_base_fee + tx_max_priority_fee_per_gas, tx_max_fee_per_gas
    )
    assert balance - balance_after == rcpt.gasUsed * rcpt_effective_gas_price


# assert the paymaster is charged for the gas used by the tx
def test_eth_send_gas_usage_with_paymaster(w3, tx_7560):
    tx_7560.maxPriorityFeePerGas = hex(12345)
    paymaster = deploy_contract(w3, "rip7560/TestPaymaster", value=10**18)
    tx_7560.paymaster = paymaster.address
    balance = w3.eth.get_balance(tx_7560.sender)
    pm_balance = w3.eth.get_balance(paymaster.address)
    res = tx_7560.send()
    assert_ok(res)
    send_bundle_now()
    rcpt = w3.eth.get_transaction_receipt(res.result)
    balance_after = w3.eth.get_balance(tx_7560.sender)
    pm_balance_after = w3.eth.get_balance(paymaster.address)
    assert balance_after == balance
    rcpt_effective_gas_price = rcpt.effectiveGasPrice
    block = w3.eth.get_block(rcpt.blockHash)
    tx_max_fee_per_gas = int(tx_7560.maxFeePerGas, 16)
    tx_max_priority_fee_per_gas = int(tx_7560.maxPriorityFeePerGas, 16)
    block_base_fee = block.baseFeePerGas

    assert rcpt.gasUsed > 0
    assert rcpt_effective_gas_price == min(
        block_base_fee + tx_max_priority_fee_per_gas, tx_max_fee_per_gas
    )
    assert pm_balance - pm_balance_after == rcpt.gasUsed * rcpt_effective_gas_price


def test_eth_sendTransaction7560_valid_with_factory(w3, tx_7560):
    factory = deploy_contract(w3, "rip7560/TestAccountFactory")

    create_account_func = factory.functions.createAccount(1)

    tx_7560.sender = create_account_func.call()
    tx_7560.authorizationData = "0x"
    tx_7560.factory = factory.address
    tx_7560.factoryData = create_account_func.build_transaction()["data"]
    tx_7560.nonce = hex(0)

    assert len(w3.eth.get_code(tx_7560.sender)) == 0
    nonce = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce == 0
    fund(w3, tx_7560.sender)
    response = tx_7560.send()
    assert_ok(response)
    send_bundle_now()
    assert len(w3.eth.get_code(tx_7560.sender)) > 0
    nonce_after = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce_after == 1


def test_bundle_with_events(w3, wallet_contract):
    icontract = compile_contract("rip7560/TestAccount")
    factory = deploy_contract(w3, "rip7560/TestAccountFactory")
    paymaster = deploy_contract(w3, "rip7560/TestPaymaster", value=10**18)

    txs = []
    hashes = []
    bundle_size = 3
    for i in range(bundle_size):
        create_account_func = factory.functions.createAccount(i)
        tx = TransactionRIP7560(
            sender=create_account_func.call(),
            factory=factory.address,
            factoryData=create_account_func.build_transaction()["data"],
            paymaster=paymaster.address,
            nonceKey=hex(0),
            nonce=hex(0),
            maxFeePerGas=hex(1000_000_000),
            maxPriorityFeePerGas=hex(1000000),
            verificationGasLimit=hex(3000000),
            executionData=wallet_contract.encodeABI(fn_name="anyExecutionFunction"),
        )
        # force the last tx to fail
        if i == 2:
            tx.executionData = wallet_contract.encodeABI(fn_name="revertingFunction")
        txs.append(tx)
        ret = tx.send()
        hashes.append(ret)
        assert_ok(ret)

    send_bundle_now()
    b = w3.eth.get_block("latest", full_transactions=True)

    # one extra transaction due to dev mode needing a "1 wei" trigger to produce a block
    assert len(b.transactions) == bundle_size + 1
    for i, tx in enumerate(b.transactions[:2]):
        rcpt = w3.eth.get_transaction_receipt(tx.hash)
        assert tx.blockHash == rcpt.blockHash
        assert tx.hash.hex() == hashes[i].result[2:]
        assert rcpt.transactionHash.hex() == hashes[i].result[2:]
        assert rcpt.transactionIndex == i
        assert rcpt.type == 4
        assert tx.transactionIndex == i

        c = w3.eth.contract(abi=icontract["abi"], address=txs[i].sender)

        # todo- assume all events are in the same transaction
        # (will be changed when we split validation from execution)
        factory_event = factory.events.TestFactoryEvent().get_logs()[0]
        validation_event = c.events.AccountValidationEvent().get_logs()[0]
        if i < 2:
            opcode_event = c.events.OpcodesEvent().get_logs()[0]
            exec_event = c.events.AccountExecutionEvent().get_logs()[0]
            assert c.functions.state().call() == 2
            assert rcpt.status == 1
        else:
            assert c.functions.state().call() == 1  # only passed validation
            assert rcpt.status == 0
            opcode_event = "reverted"
            exec_event = "reverted"

        assert factory_event.logIndex == 0
        assert factory_event.address == factory.address
        for index, log in enumerate([validation_event, opcode_event, exec_event]):
            # skip checking logs of deliberately reverted tx
            if log == "reverted":
                continue
            # print("checking log ", index, " for tx ", i)
            assert log.logIndex == 1 + i * 4 + index
            assert log.address == txs[i].sender


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_eth_sendTransaction7560_banned_opcode(
    wallet_contract_rules, tx_7560, banned_op
):
    state_before = wallet_contract_rules.functions.state().call()
    assert state_before == 0
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.authorizationData = to_prefixed_hex(banned_op)
    tx_7560.nonce = hex(2)
    response = tx_7560.send()
    assert_rpc_error(response, response.message, RPCErrorCode.BANNED_OPCODE)
    send_bundle_now()
    state_after = wallet_contract_rules.functions.state().call()
    assert state_after == 0


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_paymaster_eth_sendTransaction7560_banned_opcode(
    wallet_contract, tx_7560, paymaster_contract_7560, banned_op
):
    state_before = wallet_contract.functions.state().call()
    assert state_before == 0
    tx_7560.sender = wallet_contract.address
    tx_7560.paymaster = paymaster_contract_7560.address
    tx_7560.paymasterData = to_prefixed_hex(banned_op)
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "paymaster uses banned opcode: " + banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
    send_bundle_now()
    state_after = wallet_contract.functions.state().call()
    assert state_after == 0


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_factory_eth_sendTransaction7560_banned_opcode(
    w3, tx_7560, factory_contract_7560, banned_op
):
    new_sender_address = factory_contract_7560.functions.getCreate2Address(
        ADDRESS_ZERO, 123, banned_op
    ).call()
    tx_7560.sender = new_sender_address
    fund(w3, new_sender_address)
    tx_7560.nonce = hex(0)
    code = w3.eth.get_code(new_sender_address)
    assert code.hex() == ""
    tx_7560.factory = factory_contract_7560.address
    tx_7560.factoryData = factory_contract_7560.functions.createAccount(
        ADDRESS_ZERO, 123, banned_op
    ).build_transaction()["data"]
    tx_7560.authorizationData = to_prefixed_hex(banned_op)
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "factory",
        RPCErrorCode.BANNED_OPCODE,
    )
    assert_rpc_error(
        response,
        banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
    send_bundle_now()
    # no code deployed is the only check I can come up with here
    code = w3.eth.get_code(new_sender_address)
    assert code.hex() == ""
