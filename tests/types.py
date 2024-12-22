import itertools
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from typing import ClassVar

import json
import jsonrpcclient
import requests


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
        postres = requests.post(url, json=asdict(self), timeout=10).json()
        if CommandLineArgs.log_rpc:
            # https://github.com/pylint-dev/pylint/issues/7891
            # pylint: disable=no-member
            print("<<", postres)
        res = jsonrpcclient.responses.to_response(postres)
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


def remove_nulls(obj):
    return {k: v for k, v in obj.items() if v is not None}
