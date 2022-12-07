"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from dataclasses import asdict

from tests.types import UserOperation, RPCRequest, RPCErrorCode
from tests.utils import userOpHash, assertRpcError

def stringToPrefixedHex(s):
    return '0x' + stringToHex(s)


def stringToHex(s):
    return s.encode().hex()

banned_opcodes = [
    'GAS',
    'NUMBER',
    'TIMESTAMP',
    'COINBASE',
    'DIFFICULTY',
    'BASEFEE',
    'GASLIMIT',
    'GASPRICE',
    'SELFBALANCE',
    'BALANCE',
    'ORIGIN',
    'BLOCKHASH',
    'CREATE',
    'CREATE2',
    'OTHERSLOAD',
    'OTHERSSTORE'
]

allowed_opcodes = [
    '',
    'SELFSSLOAD',
    'SELFSSTORE',
    'SELFREFSLOAD',
    'SELFREFSSTORE',

]

@pytest.mark.parametrize('allowed_op', allowed_opcodes)
def test_allowed_opcode(cmd_args, opban_contract, allowed_op):
    userOp = UserOperation(sender=opban_contract.address, signature=stringToPrefixedHex(allowed_op))
    response = RPCRequest(method="eth_sendUserOperation",
                          params=[asdict(userOp), cmd_args.entry_point]).send(cmd_args.url)
    # assert response["result"] == userOpHash(wallet_contract, userOp)
    assert int(response.result, 16)


@pytest.mark.parametrize('banned_op', banned_opcodes)
def test_account_banned_opcode(cmd_args, opban_contract, banned_op):
    userOp = UserOperation(sender=opban_contract.address, signature=stringToPrefixedHex(banned_op))
    response = RPCRequest(method="eth_sendUserOperation",
                          params=[asdict(userOp), cmd_args.entry_point]).send(cmd_args.url)
    assertRpcError(response, 'account uses banned opcode: '+ banned_op, RPCErrorCode.BANNED_OPCODE)


@pytest.mark.skip
@pytest.mark.parametrize('banned_op', banned_opcodes)
def test_paymaster_banned_opcode(cmd_args, opban_contract, banned_op):
    userOp = UserOperation(sender=opban_contract.address, paymasterAndData=opban_contract.address + stringToHex(banned_op))
    print('what is paymasterAndData', userOp.paymasterAndData)
    response = RPCRequest(method="eth_sendUserOperation",
                          params=[asdict(userOp), cmd_args.entry_point]).send(cmd_args.url)
    assertRpcError(response, 'paymaster uses banned opcode: '+ banned_op, RPCErrorCode.BANNED_OPCODE)

