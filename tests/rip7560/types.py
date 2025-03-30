from dataclasses import dataclass, asdict

from web3.constants import ADDRESS_ZERO
from eth_typing import HexStr
from eth_utils import to_checksum_address, to_bytes
from tests.types import RPCRequest
from tests.types import remove_nulls
from rlp import encode


def hex_to_int(h: str) -> int:
    return int(h, 16)


def hex_to_bytes(h: str) -> bytes:
    return b"" if h == "0x" else bytes.fromhex(h[2:])


@dataclass
class TransactionRIP7560:
    # pylint: disable=too-many-instance-attributes, invalid-name
    Type = 5
    sender: HexStr
    nonceKey: HexStr = hex(0)
    nonce: HexStr = hex(0)
    factory: HexStr = "0x0000000000000000000000000000000000000000"
    deployer: HexStr = None  # alias for factory
    factoryData: HexStr = "0x"
    deployerData: HexStr = None  # alias for factoryData
    executionData: HexStr = "0x"
    callGasLimit: HexStr = hex(3 * 10**5)
    gas: HexStr = None  # alias for callGasLimit
    verificationGasLimit: HexStr = hex(10**6)
    maxFeePerGas: HexStr = hex(4 * 10**9)
    maxPriorityFeePerGas: HexStr = hex(3 * 10**9)
    authorizationData: HexStr = "0x"
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
        if self.deployer is not None:
            self.factory = self.deployer
            self.deployer = None
        if self.deployerData is not None:
            self.factoryData = self.deployerData
            self.deployerData = None
        if self.gas is not None:
            self.callGasLimit = self.gas
            self.gas = None
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

    def rlp_encode(self):
        # Convert and set defaults
        encoded_tx = encode(
            [
                hex_to_int(self.chainId),
                hex_to_int(self.nonceKey),
                hex_to_int(self.nonce),
                hex_to_bytes(self.sender),
                hex_to_bytes(self.factory),
                hex_to_bytes(self.factoryData),
                hex_to_bytes(self.paymaster),
                hex_to_bytes(self.paymasterData),
                hex_to_bytes(self.executionData),
                hex_to_int(self.builderFee),
                hex_to_int(self.maxPriorityFeePerGas),
                hex_to_int(self.maxFeePerGas),
                hex_to_int(self.verificationGasLimit),
                hex_to_int(self.paymasterVerificationGasLimit),
                hex_to_int(self.paymasterPostOpGasLimit),
                hex_to_int(self.callGasLimit),
                [],
                hex_to_bytes(self.authorizationData),
                hex_to_int(self.value),
            ]
        )
        return "0x05" + encoded_tx.hex()

    def send_raw(self, url=None):
        encoded_tx = self.rlp_encode()
        print("RLP ENCODED", encoded_tx)
        return RPCRequest(method="eth_sendRawTransaction", params=[encoded_tx]).send(
            url
        )

    def send(self, url=None):
        bal = RPCRequest(
            method="eth_getBalance",
            params=["0x67b1d87101671b127f5f8714789C7192f7ad340e", "latest"],
        ).send(url)
        print("large balance here should be", bal)
        return RPCRequest(
            method="eth_sendTransaction", params=[remove_nulls(asdict(self.cleanup()))]
        ).send(url)

    def send_skip_validation(self, url=None):
        return RPCRequest(
            method="debug_bundler_sendTransactionSkipValidation",
            params=[remove_nulls(asdict(self.cleanup()))],
        ).send(url)
