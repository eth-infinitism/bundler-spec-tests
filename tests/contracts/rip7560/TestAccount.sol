// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../ITestAccount.sol";

import "./RIP7560TransactionType4.sol";
import "./utils/RIP7560Utils.sol";
import "./utils/TestUtils.sol";

contract TestAccount {
    uint256 public accCounter = 0;
    string public state = "new";

    event Funded(string id, uint256 amount);

    event AccountValidationEvent(string state, uint256 counter);

    event AccountExecutionEvent(string state, uint256 counter, bytes data);

    constructor() payable {
    }

    function validateTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) external returns (bytes32) {

        TestUtils.emitEvmData("validateTransaction");
        TestUtils.emitValidationParams(version, txHash, transaction);

        emit AccountValidationEvent(state, accCounter);

        /* Modify account state */
        accCounter++;
        state = "validated";

        return RIP7560Utils.accountAcceptTransaction(block.timestamp, block.timestamp + 10000);
    }

    function anyExecutionFunction() external {
        TestUtils.emitEvmData("anyExecutionFunction");

        emit AccountExecutionEvent(state, accCounter, msg.data);


        state = "executed";
    }

    function reset() external {
        state = "new";
        accCounter = 0;
    }

    receive() external payable {
        emit Funded("account", msg.value);
    }

    fallback(bytes calldata) external returns (bytes memory) {
//        accCounter++;
//        emit AccountEvent("account", string(msg.data));
        return "account-returned-data-here";
    }
}
