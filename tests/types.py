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
    nonce_manager: ClassVar[str]
    stake_manager: ClassVar[str]
    ethereum_node: ClassVar[str]
    launcher_script: ClassVar[str]
    log_rpc: ClassVar[bool]

    @classmethod
    # pylint: disable=too-many-arguments
    def configure(
        cls,
        url,
        entrypoint,
        nonce_manager,
        stake_manager,
        ethereum_node,
        launcher_script,
        log_rpc,
    ):
        cls.url = url
        cls.entrypoint = entrypoint
        cls.nonce_manager = nonce_manager
        cls.stake_manager = stake_manager
        cls.ethereum_node = ethereum_node
        cls.launcher_script = launcher_script
        cls.log_rpc = log_rpc


@dataclass
class UserOperation:
    # pylint: disable=too-many-instance-attributes, invalid-name
    sender: HexStr
    nonce: HexStr = hex(0)
    factory: HexStr = None
    factoryData: HexStr = None
    callData: HexStr = "0x"
    callGasLimit: HexStr = hex(3 * 10**5)
    verificationGasLimit: HexStr = hex(10**6)
    preVerificationGas: HexStr = hex(3 * 10**5)
    maxFeePerGas: HexStr = hex(4 * 10**9)
    maxPriorityFeePerGas: HexStr = hex(3 * 10**9)
    signature: HexStr = "0x"
    paymaster: HexStr = None
    paymasterData: HexStr = None
    paymasterVerificationGasLimit: HexStr = None
    paymasterPostOpGasLimit: HexStr = None

    def __post_init__(self):
        self.sender = to_checksum_address(self.sender)
        self.callData = self.callData.lower()
        self.signature = self.signature.lower()
        if self.paymaster is not None:
            self.paymaster = to_checksum_address(self.paymaster)
            if self.paymasterVerificationGasLimit is None:
                self.paymasterVerificationGasLimit = hex(10**5)
            if self.paymasterPostOpGasLimit is None:
                self.paymasterPostOpGasLimit = hex(10**5)
            if self.paymasterData is None:
                self.paymasterData = "0x"
            else:
                self.paymasterData = self.paymasterData.lower()
        if self.factory is not None:
            self.factory = to_checksum_address(self.factory)
            if self.factoryData is None:
                self.factoryData = "0x"
            else:
                self.factoryData = self.factoryData.lower()

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
        res = jsonrpcclient.responses.to_response(
            requests.post(url, json=asdict(self), timeout=10).json()
        )
        if CommandLineArgs.log_rpc:
            # https://github.com/pylint-dev/pylint/issues/7891
            # pylint: disable=no-member
            print("<<", json.dumps(res))
        return res


class RPCErrorCode(IntEnum):
    INVALID_INPUT = -32000
    REJECTED_BY_EP_OR_ACCOUNT = -32500
    REJECTED_BY_PAYMASTER = -32501
    BANNED_OPCODE = -32502
    SHORT_DEADLINE = -32503
    BANNED_OR_THROTTLED_PAYMASTER = -32504
    INAVLID_PAYMASTER_STAKE = -32505
    INVALID_AGGREGATOR = -32506
    INVALID_SIGNATURE = -32507
    PAYMASTER_DEPOSIT_TOO_LOW = -32508

    EXECUTION_REVERTED = -32521
    INVALID_FIELDS = -32602
