from eth_typing import (
    HexStr,
)

from dataclasses import dataclass, field

@dataclass
class UserOperation:
    sender: HexStr
    nonce: HexStr
    initCode: HexStr
    calldata: HexStr
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
    id: int
    params: list = field(default_factory=list, compare=False)
    jsonrpc: str = "2.0"

