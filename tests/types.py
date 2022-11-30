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

    def send(self, url) -> jsonrpcclient.responses.Response:
        return jsonrpcclient.responses.to_result(requests.post(url, json=asdict(self)).json())


class RPCErrorCode(IntEnum):
    REJECTED_BY_EP = -32500
    BANNED_OPCODE = -32501
