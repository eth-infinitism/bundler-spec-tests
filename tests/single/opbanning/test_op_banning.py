"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest

from tests.types import UserOperation, RPCErrorCode
from tests.utils import (
    assert_ok,
    assert_rpc_error,
    deposit_to_undeployed_sender,
    to_hex,
    to_prefixed_hex,
)


# All opcodes are part of the OP-011 rule
banned_opcodes = [
    "GAS",
    "NUMBER",
    "TIMESTAMP",
    "COINBASE",
    "DIFFICULTY",
    "BASEFEE",
    "GASLIMIT",
    "GASPRICE",
    "SELFBALANCE",
    "BALANCE",
    "ORIGIN",
    "BLOCKHASH",
    "CREATE",
    "CREATE2",
    # "SELFDESTRUCT",
]

# the "OP-052" tested elsewhere
allowed_opcode_sequences = ["GAS CALL", "GAS DELEGATECALL"]


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_banned_opcode(rules_account_contract, banned_op):
    response = UserOperation(
        sender=rules_account_contract.address, signature=to_prefixed_hex(banned_op)
    ).send()
    assert_rpc_error(
        response, "account uses banned opcode: " + banned_op, RPCErrorCode.BANNED_OPCODE
    )


# OP-012
@pytest.mark.parametrize("allowed_op_sequence", allowed_opcode_sequences)
def test_account_allowed_opcode_sequence(rules_account_contract, allowed_op_sequence):
    response = UserOperation(
        sender=rules_account_contract.address,
        signature=to_prefixed_hex(allowed_op_sequence),
    ).send()
    assert_ok(response)


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_paymaster_banned_opcode(paymaster_contract, wallet_contract, banned_op):
    response = UserOperation(
        sender=wallet_contract.address,
        paymaster=paymaster_contract.address,
        paymasterData="0x" + to_hex(banned_op),
        paymasterVerificationGasLimit=hex(200000),
    ).send()
    assert_rpc_error(
        response,
        "paymaster uses banned opcode: " + banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_factory_banned_opcode(w3, factory_contract, entrypoint_contract, banned_op):
    factoryData = factory_contract.functions.create(
        123, banned_op, entrypoint_contract.address
    ).build_transaction()["data"]
    sender = deposit_to_undeployed_sender(
        w3, entrypoint_contract, factory_contract.address, factoryData
    )
    response = UserOperation(
        sender=sender, factory=factory_contract.address, factoryData=factoryData
    ).send()
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
