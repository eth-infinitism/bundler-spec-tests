from eth_typing import (
    HexStr,
)

from dataclasses import dataclass, field
from enum import IntEnum

@dataclass
class UserOperation:
    sender: HexStr
    nonce: HexStr
    initCode: HexStr
    callData: HexStr
    callGasLimit: HexStr
    verificationGasLimit: HexStr
    preVerificationGas: HexStr
    maxFeePerGas: HexStr
    maxPriorityFeePerGas: HexStr
    paymasterAndData: HexStr
    signature: HexStr


@dataclass
class RPCRequest:
    method: str
    id: int = 1234
    params: list = field(default_factory=list, compare=False)
    jsonrpc: str = "2.0"


class RPCErrorCode(IntEnum):
    REJECTED_BY_EP = -32500
    BANNED_OPCODE = -32501
