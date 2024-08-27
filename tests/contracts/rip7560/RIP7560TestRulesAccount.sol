// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

import "../ValidationRules.sol";

import "./TestAccount.sol";
import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";
import "../Stakable.sol";

interface IRip7560EntryPointWrong {
    function acceptAccountWrongSig(uint256 validAfter, uint256 validUntil) external;
}

contract RIP7560TestRulesAccount is ValidationRulesStorage, Stakable {

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
        RIP7560Transaction memory txStruct = RIP7560Utils.decodeTransaction(version, transaction);
        string memory rule = string(txStruct.authorizationData);
        if (ValidationRules.eq(rule, "wrong-callback-method")) {
            ENTRY_POINT.call(abi.encodeCall(IRip7560EntryPointWrong.acceptAccountWrongSig, (666, 777)));
            return;
        }
        ValidationRules.runRule(rule, this, coin, this);
        RIP7560Utils.accountAcceptTransaction(1, type(uint48).max - 1);
    }
}
