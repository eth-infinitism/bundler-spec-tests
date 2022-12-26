"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest

from tests.types import UserOperation, RPCErrorCode
from tests.utils import assertRpcError, getSenderAddress


def stringToPrefixedHex(s):
    return "0x" + stringToHex(s)


def stringToHex(s):
    return s.encode().hex()


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
]


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_banned_opcode(rules_account_contract, banned_op):
    response = UserOperation(
        sender=rules_account_contract.address, signature=stringToPrefixedHex(banned_op)
    ).send()
    assertRpcError(
        response, "account uses banned opcode: " + banned_op, RPCErrorCode.BANNED_OPCODE
    )


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_paymaster_banned_opcode(paymaster_contract, wallet_contract, banned_op):
    response = UserOperation(
        sender=wallet_contract.address,
        paymasterAndData=paymaster_contract.address + stringToHex(banned_op),
    ).send()
    assertRpcError(
        response,
        "paymaster uses banned opcode: " + banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_factory_banned_opcode(w3, factory_contract, entrypoint_contract, banned_op):
    initCode = (
        factory_contract.address
        + factory_contract.functions.create(
            123, banned_op, entrypoint_contract.address
        ).build_transaction()["data"][2:]
    )
    sender = getSenderAddress(w3, initCode)
    entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    response = UserOperation(sender=sender, initCode=initCode).send()
    assertRpcError(
        response,
        "factory",
        RPCErrorCode.BANNED_OPCODE,
    )
    assertRpcError(
        response,
        banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
