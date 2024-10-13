import collections
import pytest
from web3 import Web3

from web3.constants import ADDRESS_ZERO
from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    assert_rpc_error,
    fund,
    get_rip7560_debug_info,
    send_bundle_now,
    to_prefixed_hex,
    deploy_contract,
    assert_ok,
    dump_mempool,
)
from tests.types import RPCErrorCode


def test_eth_send_no_gas(w3):
    contract = deploy_contract(
        w3,
        "rip7560/TestAccount",
        value=0,
    )

    tx = TransactionRIP7560(sender=contract.address, nonce=hex(1))

    ret = tx.send()
    assert_rpc_error(ret, "insufficient funds", RPCErrorCode.INVALID_INPUT)


def test_eth_send_no_code(w3):
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111113",
    )
    fund(w3, tx.sender)

    ret = tx.send()
    assert_rpc_error(
        ret,
        "account is not deployed and no deployer is specified",
        RPCErrorCode.INVALID_INPUT,
    )


def test_eth_send_wrong_nonce(tx_7560):
    tx_7560.nonce = hex(5)
    ret = tx_7560.send()
    assert_rpc_error(ret, "nonce too high", RPCErrorCode.INVALID_INPUT)

    tx_7560.nonce = hex(0)
    ret = tx_7560.send()
    assert_rpc_error(ret, "nonce too low", RPCErrorCode.INVALID_INPUT)


RevertTestCase = collections.namedtuple(
    "RevertTestCase",
    ["rule", "entity", "expected_message", "is_expected_data"],
)

cases = [
    # account standard solidity error revert
    RevertTestCase(
        "revert-msg",
        "account",
        "validation phase failed in contract account with exception: "
        "execution reverted: on-chain revert message string",
        False,
    ),
    # account custom solidity error revert
    RevertTestCase(
        "revert-custom-msg",
        "account",
        "validation phase failed in contract account with exception: execution reverted",
        True,
    ),
    # account out of gas error revert
    RevertTestCase(
        "revert-out-of-gas-msg",
        "account",
        "validation phase failed in contract account with exception: out of gas",
        False,
    ),
    # paymaster standard solidity error revert
    RevertTestCase(
        "revert-msg",
        "paymaster",
        "validation phase failed in contract paymaster with exception: "
        "execution reverted: on-chain revert message string",
        False,
    ),
    # paymaster custom solidity error revert
    RevertTestCase(
        "revert-custom-msg",
        "paymaster",
        "validation phase failed in contract paymaster with exception: execution reverted",
        True,
    ),
    # paymaster out of gas error revert
    RevertTestCase(
        "revert-out-of-gas-msg",
        "paymaster",
        "validation phase failed in contract paymaster with exception: out of gas",
        False,
    ),
]


def case_id_function(case):
    return f"[{case.entity}][{case.rule}]"


@pytest.mark.parametrize("case", cases, ids=case_id_function)
def test_eth_send_account_validation_reverts1(
    w3,
    wallet_contract_rules,
    tx_7560: TransactionRIP7560,
    paymaster_contract_7560,
    case: RevertTestCase,
):
    if case.entity == "account":
        tx_7560.nonce = hex(2)
        tx_7560.sender = wallet_contract_rules.address
        tx_7560.authorizationData = to_prefixed_hex(case.rule)
    if case.entity == "paymaster":
        tx_7560.paymaster = paymaster_contract_7560.address
        tx_7560.paymasterData = to_prefixed_hex(case.rule)

    response = tx_7560.send()

    expected_data = None
    if case.is_expected_data:
        expected_data = encode_custom_error(w3)
    assert_rpc_error(response, case.expected_message, -32000, expected_data)


@pytest.mark.parametrize("case", cases, ids=case_id_function)
def test_eth_send_account_validation_reverts_skip_validation_bundler(
    w3,
    wallet_contract_rules,
    tx_7560: TransactionRIP7560,
    paymaster_contract_7560,
    case: RevertTestCase,
):
    if case.entity == "account":
        tx_7560.nonce = hex(2)
        tx_7560.sender = wallet_contract_rules.address
        tx_7560.authorizationData = to_prefixed_hex(case.rule)
    if case.entity == "paymaster":
        tx_7560.nonce = hex(2)
        tx_7560.sender = wallet_contract_rules.address
        tx_7560.authorizationData = to_prefixed_hex("")
        tx_7560.paymaster = paymaster_contract_7560.address
        tx_7560.paymasterData = to_prefixed_hex(case.rule)

    state_before = wallet_contract_rules.functions.state().call()
    assert state_before == 0

    nonce_before = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce_before == 2

    response = tx_7560.send_skip_validation()
    send_bundle_now()

    state_after = wallet_contract_rules.functions.state().call()
    assert state_after == 0

    nonce_after = w3.eth.get_transaction_count(tx_7560.sender)
    assert nonce_after == 2

    debug_info = get_rip7560_debug_info(response.result)

    assert debug_info.result["frameReverted"] is True
    assert debug_info.result["revertEntityName"] == case.entity


def encode_solidity_error(w3, value):
    # manually encoding the custom error message with "encode_abi" here
    c = w3.eth.contract(
        abi='[{"type":"function","name":"Error",'
        '"inputs":[{"name": "error","type": "string"}]}]'
    )
    abi_encoding = c.encode_abi(abi_element_identifier="Error", args=[value])
    return abi_encoding


def encode_custom_error(w3):
    # manually encoding the custom error message with "encode_abi" here
    c = w3.eth.contract(
        abi='[{"type":"function","name":"CustomError",'
        '"inputs":[{"name": "error","type": "string"},{"name": "code","type": "uint256"}]}]'
    )
    abi_encoding = c.encode_abi(
        abi_element_identifier="CustomError", args=["on-chain custom error", 777]
    )
    return abi_encoding


def test_eth_send_account_validation_calls_invalid_callback(
    wallet_contract_rules, tx_7560
):
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.nonce = hex(2)
    tx_7560.authorizationData = to_prefixed_hex("wrong-callback-method")

    response = tx_7560.send()
    assert_rpc_error(
        response,
        "validation phase failed with exception: unable to decode acceptAccount: no method with id: 0xd3ae1743",
        -32000,
    )


def test_eth_send_paymaster_validation_calls_invalid_callback(
    paymaster_contract_7560, tx_7560
):
    tx_7560.paymaster = paymaster_contract_7560.address
    tx_7560.paymasterData = to_prefixed_hex("wrong-callback-method")

    response = tx_7560.send()
    assert_rpc_error(
        response,
        "validation phase failed with exception: unable to decode acceptPaymaster: no method with id: 0x9a0e28f8",
        -32000,
    )


def test_eth_send_deployment_reverts(w3, factory_contract_7560, tx_7560):
    new_sender_address = factory_contract_7560.functions.getCreate2Address(
        ADDRESS_ZERO, 123, "revert-msg"
    ).call()
    tx_7560.sender = new_sender_address
    fund(w3, new_sender_address)
    tx_7560.nonce = hex(0)
    tx_7560.factory = factory_contract_7560.address
    tx_7560.factoryData = factory_contract_7560.functions.createAccount(
        ADDRESS_ZERO, 123, "revert-msg"
    ).build_transaction({"gas": 1000000})["data"]
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "validation phase failed in contract deployer with exception: "
        "execution reverted: on-chain revert message string",
        -32000,
    )


def test_eth_send_deployment_does_not_create_account(
    w3, factory_contract_7560, tx_7560
):
    new_sender_address = factory_contract_7560.functions.getCreate2Address(
        ADDRESS_ZERO, 123, "skip-deploy-msg"
    ).call()
    tx_7560.sender = new_sender_address
    fund(w3, new_sender_address)
    tx_7560.nonce = hex(0)
    tx_7560.factory = factory_contract_7560.address
    tx_7560.factoryData = factory_contract_7560.functions.createAccount(
        ADDRESS_ZERO, 123, "skip-deploy-msg"
    ).build_transaction({"gas": 1000000})["data"]
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "validation phase failed with exception: sender not deployed by the deployer",
        -32000,
    )


def test_insufficient_pre_transaction_gas(tx_7560):
    tx_7560.verificationGasLimit = hex(30000)
    tx_7560.authorizationData = "0x" + ("ff" * 1000)
    tx_7560.executionData = "0x"
    response = tx_7560.send()
    assert_rpc_error(
        response,
        "insufficient ValidationGasLimit(30000) to cover PreTransactionGasCost(31000)",
        -32000,
    )


# pylint: disable=duplicate-code
def test_overflow_block_gas_limit(w3: Web3, tx_7560: TransactionRIP7560):
    count = 3
    wallets = []
    hashes = []
    for i in range(count):
        wallets.append(
            deploy_contract(w3, "rip7560/gaswaste/GasWasteAccount", value=20**18)
        )

    for i in range(count):
        wallet = wallets[i]
        new_op = TransactionRIP7560(
            sender=wallet.address,
            nonce="0x1",
            executionData=wallet.encode_abi("anyExecutionFunction"),
            callGasLimit=hex(10_000_000),
            maxPriorityFeePerGas=tx_7560.maxPriorityFeePerGas,
            maxFeePerGas=tx_7560.maxFeePerGas,
        )
        # GasWasteAccount uses 'GAS' opcode to leave 100 gas
        res = new_op.send_skip_validation()
        hashes.append(res.result)
        assert_ok(res)

    mempool = dump_mempool()
    print(mempool)
    assert len(mempool) == count
    send_bundle_now()
    block = w3.eth.get_block("latest")
    tx_len = len(block.transactions)
    # note: two 7560 transactions and a zero-value legacy transaction from 'send_bundle_now'
    assert tx_len == count

    debug_info = get_rip7560_debug_info(hashes[2])

    assert debug_info.result["revertEntityName"] == "block gas limit"
