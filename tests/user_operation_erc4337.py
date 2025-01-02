from dataclasses import asdict, dataclass

from eth_typing import HexStr
from eth_utils import to_checksum_address

from tests.transaction_eip_7702 import TupleEIP7702
from tests.types import RPCRequest, CommandLineArgs


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
    # authorizationList: list[TupleEIP7702] = None
    eip7702auth: TupleEIP7702 = None

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

    # send into the mempool without applying tracing/validations
    def debug_send(self, entrypoint=None, url=None):
        if entrypoint is None:
            entrypoint = CommandLineArgs.entrypoint
        return RPCRequest(
            method="debug_bundler_sendUserOperationSkipValidation",
            params=[asdict(self), entrypoint],
        ).send(url)
