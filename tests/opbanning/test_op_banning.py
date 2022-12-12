"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from dataclasses import asdict

from tests.types import UserOperation, RPCRequest, RPCErrorCode
from tests.utils import userOpHash, assertRpcError


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
    "OTHERSLOAD",
    "OTHERSSTORE",
]

allowed_opcodes = [
    "",
    "SELFSSLOAD",
    "SELFSSTORE",
    "SELFREFSLOAD",
    "SELFREFSSTORE",
]


@pytest.mark.parametrize("allowed_op", allowed_opcodes)
def test_allowed_opcode(opban_contract, allowed_op):
    response = UserOperation(
        sender=opban_contract.address, signature=stringToPrefixedHex(allowed_op)
    ).send()
    # assert response.result == userOpHash(opban_contract, userOp)
    assert int(response.result, 16)


@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_account_banned_opcode(opban_contract, banned_op):
    response = UserOperation(
        sender=opban_contract.address, signature=stringToPrefixedHex(banned_op)
    ).send()
    assertRpcError(
        response, "account uses banned opcode: " + banned_op, RPCErrorCode.BANNED_OPCODE
    )


@pytest.mark.skip
@pytest.mark.parametrize("banned_op", banned_opcodes)
def test_paymaster_banned_opcode(opban_contract, banned_op):
    response = UserOperation(
        sender=opban_contract.address,
        paymasterAndData=opban_contract.address + stringToHex(banned_op),
    ).send()
    assertRpcError(
        response,
        "paymaster uses banned opcode: " + banned_op,
        RPCErrorCode.BANNED_OPCODE,
    )
