from dataclasses import dataclass, asdict
from typing import Optional

import rlp
from eth_keys import keys
from eth_typing import HexStr
from eth_utils import to_bytes
from web3 import Web3

from tests.rip7560.types import remove_nulls
from tests.types import RPCRequest


@dataclass
class TupleEIP7702:
    # pylint: disable=invalid-name
    chainId: HexStr
    address: HexStr
    nonce: HexStr
    # pylint: disable=invalid-name
    yParity: Optional[HexStr] = None
    r: Optional[HexStr] = None
    s: Optional[HexStr] = None
    signer_private_key: Optional[HexStr] = None

    def __post_init__(self):
        if self.signer_private_key:
            self._sign(self.signer_private_key)
            self.signer_private_key = None

    def _sign(self, private_key: str):
        pk = keys.PrivateKey(bytes.fromhex(private_key))
        nonce = self.nonce
        if nonce == "0x0":
            nonce = "0x"

        chain_id = self.chainId
        if chain_id == "0x0":
            chain_id = "0x"

        rlp_encode = bytearray(
            rlp.encode(
                [
                    to_bytes(hexstr=chain_id),
                    to_bytes(hexstr=self.address),
                    to_bytes(hexstr=nonce),
                ]
            )
        )
        rlp_encode.insert(0, 5)
        rlp_encode_hash = Web3.keccak(hexstr=rlp_encode.hex())
        signature = pk.sign_msg_hash(rlp_encode_hash)
        self.yParity = hex(signature.v)
        self.r = hex(signature.r)
        self.s = hex(signature.s)


# pylint: disable=fixme
# TODO: Will we have any tests sending EIP-7702 transactions directly?
#  If not, this class can be removed.
@dataclass
class TransactionEIP7702:
    # pylint: disable=too-many-instance-attributes, invalid-name
    to: HexStr = "0x0000000000000000000000000000000000000000"
    data: HexStr = "0x00"
    nonce: HexStr = hex(0)
    gasLimit: HexStr = hex(1_000_000)  # alias for callGasLimit
    maxFeePerGas: HexStr = hex(4 * 10**9)
    maxPriorityFeePerGas: HexStr = hex(3 * 10**9)
    chainId: HexStr = hex(1337)
    value: HexStr = hex(0)
    # pylint: disable=fixme
    accessList: list[HexStr] = ()  # todo: type is not correct, must always be empty!
    authorizationList: list[TupleEIP7702] = ()

    # pylint: disable=fixme
    # todo: implement
    def cleanup(self):
        return self

    def send(self, url=None):
        return RPCRequest(
            method="eth_sendTransaction", params=[remove_nulls(asdict(self.cleanup()))]
        ).send(url)
