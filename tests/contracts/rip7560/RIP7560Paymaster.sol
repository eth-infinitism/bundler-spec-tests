// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../TestCoin.sol";
import "../ValidationRules.sol";

import "./utils/RIP7560Utils.sol";
import "./RIP7560TransactionStruct.sol";

contract RIP7560Paymaster is ValidationRulesStorage {

    TestCoin public coin;

    uint256 public pmCounter = 0;

    event Funded(string id, uint256 amount);
    event PaymasterValidationEvent(string name, uint256 counter);
    event PaymasterPostTxEvent(string name, uint256 counter, bytes context);

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external
    returns (
        bytes memory validationData
    ){
        emit PaymasterValidationEvent("the-paymaster", pmCounter);
        bytes memory context = abi.encodePacked("context here", pmCounter);
        pmCounter++;
        RIP7560TransactionStruct memory txStruct = abi.decode(transaction, (RIP7560TransactionStruct));
        string memory rule = string(txStruct.signature);
        ValidationRules.runRule(rule, this, coin, this);
        return RIP7560Utils.paymasterAcceptTransaction("", block.timestamp, block.timestamp + 1000);
    }

    function postPaymasterTransaction(
        bool success,
        uint256 actualGasCost,
        bytes calldata context
    ) external {
        emit PaymasterPostTxEvent("the-paymaster", pmCounter, context);
    }

    receive() external payable {
        emit Funded("account", msg.value);
    }
}
