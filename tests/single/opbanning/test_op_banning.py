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
    "SELFDESTRUCT",
]

# the "OP-052" tested elsewhere
allowed_opcode_sequences = ["GAS CALL", "GAS DELEGATECALL"]

# All opcodes as part of the OP-080 rule
allowed_opcodes_when_staked = ["BALANCE", "SELFBALANCE"]


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_banned_opcode(rules_account_contract, banned_op):
    response = UserOperation(
        sender=rules_account_contract.address, signature=to_prefixed_hex(banned_op)
    ).send()
    assert_rpc_error(
        response, "account uses banned opcode: " + banned_op, RPCErrorCode.BANNED_OPCODE
    )


@pytest.mark.parametrize("op", allowed_opcodes_when_staked)
def test_account_allowed_opcode_when_staked(rules_staked_account_contract, op):
    response = UserOperation(
        sender=rules_staked_account_contract.address,
        signature=to_prefixed_hex(op),
    ).send()
    assert_ok(response)


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
        paymasterAndData=paymaster_contract.address + to_hex(banned_op),
    ).send()
    assert_rpc_error(
        response,
        "paymaster uses banned opcode: " + banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )


@pytest.mark.parametrize("op", allowed_opcodes_when_staked)
def test_paymaster_allowed_opcode_when_staked(
    staked_paymaster_contract, wallet_contract, op
):
    response = UserOperation(
        sender=wallet_contract.address,
        paymasterAndData=staked_paymaster_contract.address + to_hex(op),
    ).send()
    assert_ok(response)


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_factory_banned_opcode(w3, factory_contract, entrypoint_contract, banned_op):
    initcode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, banned_op, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = deposit_to_undeployed_sender(w3, entrypoint_contract, initcode)
    response = UserOperation(sender=sender, initCode=initcode).send()
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


@pytest.mark.parametrize("op", allowed_opcodes_when_staked)
def test_factory_allowed_opcode_when_staked(
    w3, staked_factory_contract, entrypoint_contract, op
):
    initcode = (
        staked_factory_contract.address
        + staked_factory_contract.functions.create(
            123, op, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = deposit_to_undeployed_sender(w3, entrypoint_contract, initcode)
    response = UserOperation(sender=sender, initCode=initcode).send()
    assert_ok(response)
