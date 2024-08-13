from web3.constants import ADDRESS_ZERO
from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    assert_rpc_error,
    fund,
    to_prefixed_hex,
)
from tests.types import RPCErrorCode


def test_eth_send_no_gas():
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111112",
    )

    ret = tx.send()
    assert_rpc_error(ret, "insufficient funds", RPCErrorCode.INVALID_INPUT)


def test_eth_send_no_code(w3):
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111113",
    )
    fund(w3, tx.sender)

    ret = tx.send()
    assert_rpc_error(
        ret, "account is not deployed and no factory is specified", RPCErrorCode.INVALID_INPUT
    )


def test_eth_send_no_code_wrong_nonce(w3):
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111113",
        nonce=hex(5),
    )
    fund(w3, tx.sender)

    ret = tx.send()
    assert_rpc_error(ret, "nonce too high", RPCErrorCode.INVALID_INPUT)


def test_eth_send_account_validation_reverts(wallet_contract_rules, tx_7560):
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.nonce = hex(2)
    tx_7560.signature = to_prefixed_hex("revert-msg")

    response = tx_7560.send()
    assert_rpc_error(response, "validation phase reverted in contract account: on-chain revert message string", -32000)


def test_eth_send_account_validation_reverts_custom(w3, wallet_contract_rules, tx_7560):
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.nonce = hex(2)
    tx_7560.signature = to_prefixed_hex("revert-custom-msg")

    response = tx_7560.send()
    # manually encoding the custom error message with "encodeABI" here
    c = w3.eth.contract(abi='[{"type":"function","name":"CustomError",'
                            '"inputs":[{"name": "error","type": "string"},{"name": "code","type": "uint256"}]}]')
    abi_encoding = c.encodeABI(fn_name="CustomError", args=["on-chain custom error", 777])
    assert_rpc_error(response, "validation phase reverted in contract account", -32000, abi_encoding)


def test_eth_send_paymaster_validation_reverts(paymaster_contract_7560, tx_7560):
    tx_7560.paymaster = paymaster_contract_7560.address
    tx_7560.paymasterData = to_prefixed_hex("revert-msg")

    response = tx_7560.send()

    assert_rpc_error(
        response,
        "validation phase reverted in contract paymaster: on-chain revert message string",
        -32000)


def test_eth_send_account_validation_calls_invalid_callback(wallet_contract_rules, tx_7560):
    tx_7560.sender = wallet_contract_rules.address
    tx_7560.nonce = hex(2)
    tx_7560.signature = to_prefixed_hex("wrong-callback-method")

    response = tx_7560.send()
    assert_rpc_error(
        response,
        "account validation did call the EntryPoint but not the 'acceptAccount' callback",
        -32000
    )


def test_eth_send_paymaster_validation_calls_invalid_callback(paymaster_contract_7560, tx_7560):
    tx_7560.paymaster = paymaster_contract_7560.address
    tx_7560.paymasterData = to_prefixed_hex("wrong-callback-method")

    response = tx_7560.send()
    assert_rpc_error(
        response,
        "paymaster validation did call the EntryPoint but not the 'acceptPaymaster' callback",
        -32000
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
    ).build_transaction({
        "gas": 1000000
    })["data"]
    response = tx_7560.send()
    assert_rpc_error(response, "validation phase reverted in contract deployer: on-chain revert message string", -32000)


def test_eth_send_deployment_does_not_create_account(w3, factory_contract_7560, tx_7560):
    new_sender_address = factory_contract_7560.functions.getCreate2Address(
        ADDRESS_ZERO, 123, "skip-deploy-msg"
    ).call()
    tx_7560.sender = new_sender_address
    fund(w3, new_sender_address)
    tx_7560.nonce = hex(0)
    tx_7560.factory = factory_contract_7560.address
    tx_7560.factoryData = factory_contract_7560.functions.createAccount(
        ADDRESS_ZERO, 123, "skip-deploy-msg"
    ).build_transaction({
        "gas": 1000000
    })["data"]
    response = tx_7560.send()
    assert_rpc_error(response, "account was not deployed by a factory", -32000)
