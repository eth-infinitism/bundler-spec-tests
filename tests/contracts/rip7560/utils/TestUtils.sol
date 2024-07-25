// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../RIP7560TransactionType4.sol";

library TestUtils {

    event ValidationTransactionFunctionParams(
        uint256 version,
        bytes32 txHash
    );

    event Type4TransactionParamsEvent(
        address sender,
        uint256 nonce,
        uint256 validationGasLimit,
        uint256 paymasterValidationGasLimit,
        uint256 postOpGasLimit,
        uint256 callGasLimit,
        uint256 maxFeePerGas,
        uint256 maxPriorityFeePerGas,
        uint256 builderFee,
        address paymaster,
        bytes paymasterData,
        address deployer,
        bytes deployerData,
        bytes callData,
        bytes signature
    );

    event OpcodesEvent(
        string tag,
        uint256 GAS,
        uint256 GASPRICE,
        uint256 BASEFEE,
        uint256 BALANCE,
        uint256 SELFBALANCE,
        uint256 GASLIMIT,
        uint256 TIMESTAMP,
        uint256 NUMBER,
        uint256 CHAINID,
        address ORIGIN,
        address CALLER,
        address CALLVALUE,
        address ADDRESS,
        address COINBASE
    );

    function emitValidationParams(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) internal {
        emit ValidationTransactionFunctionParams(version, txHash);

        TransactionType4 memory txStruct = abi.decode(transaction, (TransactionType4));

        /* Emit transaction details as seen on-chain */
        emit Type4TransactionParamsEvent(
            txStruct.sender,
            txStruct.nonce,
            txStruct.validationGasLimit,
            txStruct.paymasterValidationGasLimit,
            txStruct.postOpGasLimit,
            txStruct.callGasLimit,
            txStruct.maxFeePerGas,
            txStruct.maxPriorityFeePerGas,
            txStruct.builderFee,
            txStruct.paymaster,
            txStruct.paymasterData,
            txStruct.deployer,
            txStruct.deployerData,
            txStruct.callData,
            txStruct.signature
        );
    }

    function emitEvmData(string memory tag) internal {
        /* Emit values returned by some relevant opcodes on-chain */
        uint256 GAS;
        uint256 GASPRICE;
        uint256 BASEFEE;
        uint256 BALANCE;
        uint256 SELFBALANCE;
        uint256 GASLIMIT;
        uint256 TIMESTAMP;
        uint256 NUMBER;
        uint256 CHAINID;
        address ORIGIN;
        address CALLER;
        address CALLVALUE;
        address ADDRESS;
        address COINBASE;
        bytes32 BLOCKHASH;

        assembly {
            GAS := gas()
            GASPRICE := gasprice()
            BASEFEE := basefee()
            ADDRESS := address()
            BALANCE := balance(ADDRESS)
            SELFBALANCE := selfbalance()
            GASLIMIT := gaslimit()
            TIMESTAMP := timestamp()
            CHAINID := chainid()
            ORIGIN := origin()
            CALLER := caller()
            CALLVALUE := callvalue()
            COINBASE := coinbase()
            NUMBER := number()
        }

        emit OpcodesEvent(
            tag,
            GAS,
            GASPRICE,
            BASEFEE,
            BALANCE,
            SELFBALANCE,
            GASLIMIT,
            TIMESTAMP,
            NUMBER,
            CHAINID,
            ORIGIN,
            CALLER,
            CALLVALUE,
            ADDRESS,
            COINBASE
        );
    }
}
