import requests
from eth_typing import (
    HexStr,
)

from dataclasses import dataclass, field, asdict
from enum import IntEnum
import jsonrpcclient
from typing import Dict, Union, Tuple, Any

@dataclass
class UserOperation:
    sender: HexStr
    nonce: HexStr = hex(0)
    initCode: HexStr = '0x'
    callData: HexStr = '0x'
    callGasLimit: HexStr = hex(2*10**5)
    verificationGasLimit: HexStr = hex(10**6)
    preVerificationGas: HexStr = hex(10**5)
    maxFeePerGas: HexStr = hex(2*10**9)
    maxPriorityFeePerGas: HexStr = hex(1*10**9)
    paymasterAndData: HexStr = '0x'
    signature: HexStr = '0x'




@dataclass
class RPCRequest:
    method: str
    id: int = 1234
    params: list = field(default_factory=list, compare=False)
    jsonrpc: str = "2.0"

    def send(self, url) -> jsonrpcclient.responses.Response:
        return jsonrpcclient.responses.to_result(requests.post(url, json=asdict(self)).json())


class RPCErrorCode(IntEnum):
    REJECTED_BY_EP = -32500
    BANNED_OPCODE = -32501
