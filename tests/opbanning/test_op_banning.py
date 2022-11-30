"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
from dataclasses import asdict

from tests.types import UserOperation, RPCRequest, RPCErrorCode
from tests.utils import userOpHash, assertRpcError

def stringToPrefixedHex(s):
    return '0x' + s.encode().hex()


def get_userOp(opban_contract, rule=''):
    return UserOperation(
        sender=opban_contract.address,
        nonce=hex(0),
        initCode='0x',
        callData=opban_contract.encodeABI(fn_name='setState', args=[0]),
        callGasLimit=hex(2*10**5),
        verificationGasLimit=hex(1213945),
        preVerificationGas=hex(47124),
        maxFeePerGas=hex(2107373890),
        maxPriorityFeePerGas=hex(1500000000),
        paymasterAndData='0x',
        signature=stringToPrefixedHex(rule)
    )

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
    userOp = get_userOp(opban_contract, allowed_op)
    response = RPCRequest(method="eth_sendUserOperation",
                          params=[asdict(userOp), cmd_args.entry_point]).send(cmd_args.url)
    # assert response["result"] == userOpHash(wallet_contract, userOp)
    assert int(response.result, 16)


@pytest.mark.parametrize('banned_op', banned_opcodes)
def test_banned_opcode(cmd_args, opban_contract, banned_op):
    userOp = get_userOp(opban_contract, banned_op)
    response = RPCRequest(method="eth_sendUserOperation",
                         params=[asdict(userOp), cmd_args.entry_point]).send(cmd_args.url)
    assertRpcError(response, 'account uses banned opcode: '+ banned_op, RPCErrorCode.BANNED_OPCODE)
