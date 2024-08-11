from dataclasses import dataclass, asdict

from web3.constants import ADDRESS_ZERO
from eth_typing import HexStr
from eth_utils import to_checksum_address
from tests.types import RPCRequest


@dataclass
class TransactionRIP7560:
    # pylint: disable=too-many-instance-attributes, invalid-name
    sender: HexStr
    nonce: HexStr = hex(0)
    factory: HexStr = "0x0000000000000000000000000000000000000000"
    factoryData: HexStr = "0x"
    callData: HexStr = "0x"
    callGasLimit: HexStr = hex(3 * 10**5)
    verificationGasLimit: HexStr = hex(10**6)
    maxFeePerGas: HexStr = hex(4 * 10**9)
    maxPriorityFeePerGas: HexStr = hex(3 * 10**9)
    signature: HexStr = "0x"
    paymaster: HexStr = "0x0000000000000000000000000000000000000000"
    paymasterData: HexStr = "0x"
    paymasterVerificationGasLimit: HexStr = hex(0)
    paymasterPostOpGasLimit: HexStr = hex(0)
    chainId: HexStr = hex(1337)
    value: HexStr = hex(0)
    accessList = "0x"
    builderFee: HexStr = hex(0)

    def __post_init__(self):
        # pylint: disable=duplicate-code
        self.sender = to_checksum_address(self.sender)
        if self.paymaster is not None:
            if (
                self.paymasterVerificationGasLimit is None
                or self.paymasterVerificationGasLimit == "0x0"
            ):
                self.paymasterVerificationGasLimit = hex(10**6)
            if (
                self.paymasterPostOpGasLimit is None
                or self.paymasterPostOpGasLimit == "0x0"
            ):
                self.paymasterPostOpGasLimit = hex(10**6)
            if self.paymasterData is None:
                self.paymasterData = "0x"

    # clean paymaster and factory fields if they are None
    def cleanup(self):
        if self.paymaster is None or self.paymaster == ADDRESS_ZERO:
            self.paymaster = None
            self.paymasterPostOpGasLimit = None
            self.paymasterVerificationGasLimit = None
            self.paymasterData = None
        if self.factory is None or self.factory == ADDRESS_ZERO:
            self.factory = None
            self.factoryData = None
        return self

    def send(self, url=None):
        return RPCRequest(method="eth_sendTransaction", params=[remove_nulls(asdict(self.cleanup()))]).send(url)


def remove_nulls(obj):
    return {k: v for k, v in obj.items() if v is not None}
