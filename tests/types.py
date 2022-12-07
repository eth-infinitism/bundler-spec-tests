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

    def send(self, cmd_args):
        return RPCRequest(method="eth_sendUserOperation",
                              params=[asdict(self), cmd_args.entry_point]).send(cmd_args.url)




@dataclass
class RPCRequest:
    method: str
    id: int = 1234
    params: list = field(default_factory=list, compare=False)
    jsonrpc: str = "2.0"

    def send(self, url) -> jsonrpcclient.responses.Response:
        # return requests.post(url, json=asdict(self)).json()
        return jsonrpcclient.responses.to_result(requests.post(url, json=asdict(self)).json())


class RPCErrorCode(IntEnum):
    REJECTED_BY_EP_OR_ACCOUNT = -32500
    REJECTED_BY_PAYMASTER = -32501
    BANNED_OPCODE = -32502
    SHORT_DEADLINE = -32503
    BANNED_OR_THROTTLED_PAYMASTER = -32504
    INAVLID_PAYMASTER_STAKE = -32505
    INVALID_AGGREGATOR = -32506

    INVALID_USEROP_STRUCT = -32602
