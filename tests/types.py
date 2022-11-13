from eth_typing import (
    HexStr,
)


class UserOperation:

    def __init__(self,
                 sender: HexStr,
                 nonce: int,
                 initCode: HexStr,
                 calldata: HexStr,
                 callGasLimit: int,
                 verificationGasLimit: int,
                 preVerificationGas: int,
                 maxFeePerGas: int,
                 maxPriorityFeePerGas: int,
                 paymasterAndData: HexStr,
                 signature: HexStr):
        self.sender = sender
        self.nonce = nonce
        self.initCode = initCode
        self.calldata = calldata
        self.callGasLimit = callGasLimit
        self.verificationGasLimit = verificationGasLimit
        self.preVerificationGas = preVerificationGas
        self.maxFeePerGas = maxFeePerGas
        self.maxPriorityFeePerGas = maxPriorityFeePerGas
        self.paymasterAndData = paymasterAndData
        self.signature = signature
