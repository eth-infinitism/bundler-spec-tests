// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";

library TestUtils {

    event ValidationTransactionFunctionParams(
        uint256 version,
        bytes32 txHash
    );

    event Type4TransactionParamsEvent(
        address sender,
        uint256 nonceKey,
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

    struct OpcodesOutput {
        uint256 GAS;
        uint256 GASPRICE;
        uint256 BASEFEE;
        uint256 BALANCE;
        uint256 SELFBALANCE;
        uint256 GASLIMIT;
        uint256 TIMESTAMP;
        uint256 NUMBER;
        uint256 CHAINID;
        uint256 CALLVALUE;
        address ORIGIN;
        address CALLER;
        address ADDRESS;
        address COINBASE;
    }

    event OpcodesEvent(
        string tag,
        OpcodesOutput opcodes
    );

    function emitValidationParams(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) internal {
        emit ValidationTransactionFunctionParams(version, txHash);

        RIP7560Transaction memory txStruct = abi.decode(transaction, (RIP7560Transaction));

        /* Emit transaction details as seen on-chain */
        emit Type4TransactionParamsEvent(
            txStruct.sender,
            txStruct.nonceKey,
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
            txStruct.executionData,
            txStruct.authorizationData
        );
    }

    function emitEvmData(string memory tag) internal {
        emit OpcodesEvent(tag, getOpcodesOutput());
    }

    function getOpcodesOutput() internal returns (OpcodesOutput memory) {
        uint256 GAS;
        uint256 GASPRICE;
        uint256 BASEFEE;
        uint256 BALANCE;
        uint256 SELFBALANCE;
        uint256 GASLIMIT;
        uint256 TIMESTAMP;
        uint256 NUMBER;
        uint256 CHAINID;
        uint256 CALLVALUE;
        address ORIGIN;
        address CALLER;
        address ADDRESS;
        address COINBASE;

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

        return OpcodesOutput(
            GAS,
            GASPRICE,
            BASEFEE,
            BALANCE,
            SELFBALANCE,
            GASLIMIT,
            TIMESTAMP,
            NUMBER,
            CHAINID,
            CALLVALUE,
            ORIGIN,
            CALLER,
            ADDRESS,
            COINBASE
        );
    }
}
