// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

import "../ValidationRules.sol";

import "./TestAccount.sol";
import "./RIP7560TransactionStruct.sol";

contract RIP7560TestRulesAccount is ValidationRulesStorage {

    using ValidationRules for string;

    TestCoin public coin;

    constructor() payable {}

    receive() external payable {}

    function setCoin(TestCoin _coin) public {
        coin = _coin;
    }


    function validateTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) external returns (bytes32) {
        RIP7560TransactionStruct memory txStruct = abi.decode(transaction, (RIP7560TransactionStruct));
        string memory rule = string(txStruct.signature);
        ValidationRules.runRule(rule, this, coin, this);
        return RIP7560Utils.accountAcceptTransaction(1, type(uint64).max - 1);
    }
}
