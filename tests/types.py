import itertools
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from typing import ClassVar

import json
import jsonrpcclient
import requests
from eth_typing import (
    HexStr,
)
from eth_utils import to_checksum_address


@dataclass()
class CommandLineArgs:
    url: ClassVar[str]
    entrypoint: ClassVar[str]
    ethereum_node: ClassVar[str]
    launcher_script: ClassVar[str]
    log_rpc: ClassVar[bool]

    @classmethod
    # pylint: disable=too-many-arguments
    def configure(cls, url, entrypoint, ethereum_node, launcher_script, log_rpc):
        cls.url = url
        cls.entrypoint = entrypoint
        cls.ethereum_node = ethereum_node
        cls.launcher_script = launcher_script
        cls.log_rpc = log_rpc


@dataclass
class UserOperation:
    # pylint: disable=too-many-instance-attributes, invalid-name
    sender: HexStr
    nonce: HexStr = hex(0)
    initCode: HexStr = "0x"
    callData: HexStr = "0x"
    callGasLimit: HexStr = hex(3 * 10**5)
    verificationGasLimit: HexStr = hex(10**6)
    preVerificationGas: HexStr = hex(3 * 10**5)
    maxFeePerGas: HexStr = hex(4 * 10**9)
    maxPriorityFeePerGas: HexStr = hex(4 * 10**9)
    paymasterAndData: HexStr = "0x"
    signature: HexStr = "0x"

    def __post_init__(self):
        self.sender = to_checksum_address(self.sender)


    def send(self, entrypoint=None, url=None):
        if entrypoint is None:
            entrypoint = CommandLineArgs.entrypoint
        return RPCRequest(
            method="eth_sendUserOperation", params=[asdict(self), entrypoint]
        ).send(url)


@dataclass
class RPCRequest:
    method: str
    id: int = field(default_factory=itertools.count().__next__)
    params: list = field(default_factory=list, compare=False)
    jsonrpc: str = "2.0"

    def send(self, url=None) -> jsonrpcclient.responses.Response:
        if url is None:
            url = CommandLineArgs.url
        # return requests.post(url, json=asdict(self)).json()
        if CommandLineArgs.log_rpc:
            print(">>", url, json.dumps(asdict(self)))
        res = jsonrpcclient.responses.to_result(
            requests.post(url, json=asdict(self), timeout=10).json()
        )
        if CommandLineArgs.log_rpc:
            # https://github.com/pylint-dev/pylint/issues/7891
            # pylint: disable=no-member
            print("<<", json.dumps(res._asdict()))
        return res


class RPCErrorCode(IntEnum):
    REJECTED_BY_EP_OR_ACCOUNT = -32500
    REJECTED_BY_PAYMASTER = -32501
    BANNED_OPCODE = -32502
    SHORT_DEADLINE = -32503
    BANNED_OR_THROTTLED_PAYMASTER = -32504
    INAVLID_PAYMASTER_STAKE = -32505
    INVALID_AGGREGATOR = -32506
    INVALID_SIGNATURE = -32507

    EXECUTION_REVERTED = -32521
    INVALID_FIELDS = -32602
