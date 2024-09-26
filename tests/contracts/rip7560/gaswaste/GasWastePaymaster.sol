// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@rip7560/contracts/utils/RIP7560Utils.sol";
import {UsedGasBreakdown} from "@rip7560/contracts/interfaces/IRIP7560Paymaster.sol";

contract GasWastePaymaster {
    uint256 public pmCounter = 0;

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external
    {
        do {
            pmCounter++;
        } while (gasleft() > 3000);
        RIP7560Utils.paymasterAcceptTransaction("", 1, type(uint48).max - 1);
    }

    function postPaymasterTransaction(
        bool success,
        bytes calldata context,
        UsedGasBreakdown calldata usedGasBreakdown
    ) external {
        do {
            pmCounter++;
        } while (gasleft() > 100);
    }

    receive() external payable {
    }
}
