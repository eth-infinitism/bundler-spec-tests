struct RIP7560TransactionStruct {
    address sender;
    uint256 nonce;
    uint256 validationGasLimit;
    uint256 paymasterGasLimit;
    uint256 callGasLimit;
    uint256 maxFeePerGas;
    uint256 maxPriorityFeePerGas;
    uint256 builderFee;
    bytes paymasterData;
    bytes deployerData;
    bytes callData;
    bytes signature;
}
