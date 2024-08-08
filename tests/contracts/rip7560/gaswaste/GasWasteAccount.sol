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
    ) external {
        do {
            accCounter++;
        } while (gasleft() > 3000);
        RIP7560Utils.accountAcceptTransaction(1, type(uint48).max - 1);
    }

    function anyExecutionFunction() external {
        do {
            accCounter++;
        } while (gasleft() > 100);
    }

    receive() external payable {}
}
