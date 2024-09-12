// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@rip7560/contracts/interfaces/IRip7560Account.sol";
import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";
import "@rip7560/contracts/utils/RIP7560Utils.sol";

import "../utils/TestUtils.sol";

contract OpcodesTestAccount is IRip7560Account {

    constructor() payable {}

    function validateTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) public override {
        TestUtils.emitEvmData("account-validation");
        RIP7560Utils.accountAcceptTransaction(1, type(uint48).max - 1);
    }

    function saveEventOpcodes() external {
        TestUtils.emitEvmData("account-execution");
    }
}
