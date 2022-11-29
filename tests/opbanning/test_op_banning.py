"""
Test suite for `eip4337 bunlder` module.
See https://github.com/eth-infinitism/bundler
"""

import pytest
import requests
import web3
from dataclasses import asdict

from tests.types import UserOperation, RPCRequest, RPCErrorCode
from tests.utils import is_valid_jsonrpc_response, userOpHash, assertRpcError

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
    'BALANCE',
    'SELFBALANCE',
    'ORIGIN',
    'BLOCKHASH',
    'CREATE',
    'CREATE2',
]


def test_no_banned(cmd_args, opban_contract):
    userOp = get_userOp(opban_contract)
    print(opban_contract.address)
    print(userOp)
    payload = RPCRequest(method="eth_sendUserOperation",
                         params=[asdict(userOp), cmd_args.entry_point], id=1234)
    response = requests.post(cmd_args.url, json=asdict(payload)).json()
    print("response is", response)
    is_valid_jsonrpc_response(response)
    # assert response["result"] == userOpHash(wallet_contract, userOp)
    assert int(response["result"], 16)


@pytest.mark.parametrize('banned_op', banned_opcodes)
def test_banned_opcode(cmd_args, opban_contract, banned_op):
    print(banned_op)
    userOp = get_userOp(opban_contract, banned_op)
    payload = RPCRequest(method="eth_sendUserOperation",
                         params=[asdict(userOp), cmd_args.entry_point], id=1234)
    response = requests.post(cmd_args.url, json=asdict(payload)).json()
    is_valid_jsonrpc_response(response)
    assertRpcError(response, 'account uses banned opcode: '+ banned_op, RPCErrorCode.BANNED_OPCODE)
