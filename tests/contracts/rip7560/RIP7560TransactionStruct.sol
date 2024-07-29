// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

struct RIP7560TransactionStruct {
    address sender;
    uint256 nonce;
    uint256 validationGasLimit;
    uint256 paymasterValidationGasLimit;
    uint256 postOpGasLimit;
    uint256 callGasLimit;
    uint256 maxFeePerGas;
    uint256 maxPriorityFeePerGas;
    uint256 builderFee;
    address paymaster;
    bytes paymasterData;
    address deployer;
    bytes deployerData;
    bytes callData;
    bytes signature;
}
