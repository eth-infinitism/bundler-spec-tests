from dataclasses import dataclass, asdict

from eth_typing import HexStr

from tests.rip7560.types import remove_nulls
from tests.types import RPCRequest


@dataclass
class TupleEIP7702:
    chainId: HexStr
    address: HexStr
    nonce: HexStr
    yParity: HexStr
    r: HexStr
    s: HexStr


@dataclass
class TransactionEIP7702:
    # pylint: disable=too-many-instance-attributes, invalid-name
    nonce: HexStr = hex(0)
    gas: HexStr = hex(1_000_000)  # alias for callGasLimit
    maxFeePerGas: HexStr = hex(4 * 10 ** 9)
    maxPriorityFeePerGas: HexStr = hex(3 * 10 ** 9)
    chainId: HexStr = hex(1337)
    value: HexStr = hex(0)
    accessList: HexStr = ""
    authorizationList: list[TupleEIP7702] = ()

    # todo: implement
    def cleanup(self):
        return self

    def send(self, url=None):
        return RPCRequest(
            method="eth_sendTransaction", params=[remove_nulls(asdict(self.cleanup()))]
        ).send(url)
