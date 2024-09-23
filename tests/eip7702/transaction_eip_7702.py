from dataclasses import dataclass, asdict
from eth_keys import keys
from eth_typing import HexStr
from eth_utils import to_bytes

from tests.rip7560.types import remove_nulls
from tests.types import RPCRequest
from typing import Optional
from web3 import Web3

import rlp


@dataclass
class TupleEIP7702:
    chainId: HexStr
    address: HexStr
    nonce: HexStr
    yParity: Optional[HexStr] = None
    r: Optional[HexStr] = None
    s: Optional[HexStr] = None

    def sign(self, private_key: str):
        pk = keys.PrivateKey(bytes.fromhex(private_key))
        rlp_encode = bytearray(rlp.encode([
            to_bytes(hexstr=self.chainId),
            to_bytes(hexstr=self.address),
            to_bytes(hexstr=self.nonce)
        ]))
        rlp_encode.insert(0, 5)
        rlp_encode_hash = Web3.keccak(hexstr=rlp_encode.hex())
        signature = pk.sign_msg_hash(rlp_encode_hash)
        self.yParity = hex(signature.v)
        self.r = hex(signature.r)
        self.s = hex(signature.s)


@dataclass
class TransactionEIP7702:
    # pylint: disable=too-many-instance-attributes, invalid-name
    to: HexStr = "0x0000000000000000000000000000000000000000"
    data: HexStr = "0x00"
    nonce: HexStr = hex(0)
    gasLimit: HexStr = hex(1_000_000)  # alias for callGasLimit
    maxFeePerGas: HexStr = hex(4 * 10 ** 9)
    maxPriorityFeePerGas: HexStr = hex(3 * 10 ** 9)
    chainId: HexStr = hex(1337)
    value: HexStr = hex(0)
    accessList: list[HexStr] = ()  # todo: type is not correct, must always be empty!
    authorizationList: list[TupleEIP7702] = ()

    # todo: implement
    def cleanup(self):
        return self

    def send(self, url=None):
        return RPCRequest(
            method="eth_sendTransaction", params=[remove_nulls(asdict(self.cleanup()))]
        ).send(url)
