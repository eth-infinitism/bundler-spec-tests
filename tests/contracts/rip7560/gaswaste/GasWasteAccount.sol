// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../RIP7560TransactionType4.sol";
import "../utils/RIP7560Utils.sol";
import "../utils/TestUtils.sol";

contract GasWasteAccount {
    uint256 public accCounter = 0;

    function validateTransaction(
        uint256,
        bytes32,
        bytes calldata
    ) external returns (bytes32) {
        do {
            accCounter++;
        } while (gasleft() > 3000);
        return RIP7560Utils.accountAcceptTransaction(block.timestamp, block.timestamp + 10000);
    }

    function anyExecutionFunction() external {
        do {
            accCounter++;
        } while (gasleft() > 100);
    }

    receive() external payable {}
}
