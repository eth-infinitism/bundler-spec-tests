// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

import "../ValidationRules.sol";

import "./TestAccount.sol";
import "./RIP7560TransactionStruct.sol";

contract RIP7560TestRulesAccount is ValidationRulesStorage {

    using ValidationRules for string;

    TestCoin public coin;

    constructor() payable {
        // true only when deploying through TestRulesAccountFactory, in which case the factory sets the coin
        if (msg.sender.code.length == 0) {
            coin = new TestCoin{salt:bytes32(0)}();
        }
    }

    receive() external payable {}

    function setCoin(TestCoin _coin) public {
        coin = _coin;
    }


    function validateTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) external {
        RIP7560TransactionStruct memory txStruct = RIP7560Utils.decodeTransaction(version, transaction);
        string memory rule = string(txStruct.signature);
        ValidationRules.runRule(rule, this, coin, this);
        RIP7560Utils.accountAcceptTransaction(1, type(uint48).max - 1);
    }
}
