"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest

from tests.types import UserOperation, RPCErrorCode
from tests.utils import (
    assert_rpc_error,
    deposit_to_undeployed_sender,
    to_hex,
    to_prefixed_hex,
)


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

banned_opcodes_for_undeployed = [
    "EXTCODESIZE",
    "EXTCODEHASH",
    "EXTCODECOPY",
    "EXTCODESIZE_CREATE2",
    "EXTCODEHASH_CREATE2",
    "EXTCODECOPY_CREATE2",
]


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_banned_opcode(rules_account_contract, banned_op):
    response = UserOperation(
        sender=rules_account_contract.address, signature=to_prefixed_hex(banned_op)
    ).send()
    assert_rpc_error(
        response, "account uses banned opcode: " + banned_op, RPCErrorCode.BANNED_OPCODE
    )

@pytest.mark.parametrize("banned_opcodes_for_undeployed", banned_opcodes_for_undeployed)
def test_account_banned_opcode_for_undeployed_target(rules_account_contract, banned_opcodes_for_undeployed):
    response = UserOperation(
        sender=rules_account_contract.address, signature=to_prefixed_hex(banned_opcodes_for_undeployed)
    ).send()
    assert_rpc_error(
        response, "account accesses un-deployed contract", RPCErrorCode.BANNED_OPCODE
    )

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


@pytest.mark.parametrize("banned_op", banned_opcodes + banned_opcodes_for_undeployed)
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
    banned_op = banned_op.replace('_CREATE2', '')
    assert_rpc_error(
        response,
        banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
