// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../TestCoin.sol";
import "../ValidationRules.sol";

import "@rip7560/contracts/utils/RIP7560Utils.sol";
import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";
import "../Stakable.sol";

interface IRip7560EntryPointWrong {
    function acceptPaymasterWrongSig(uint256 validAfter, uint256 validUntil, bytes calldata context) external;
}

contract RIP7560Paymaster is ValidationRulesStorage, Stakable {
    using ValidationRules for string;
    TestCoin immutable public coin = new TestCoin();
    TestRulesTarget private immutable target = new TestRulesTarget();

    uint256 public pmCounter = 0;

    event Funded(string id, uint256 amount);
    event PaymasterValidationEvent(string name, uint256 counter);
    event PaymasterPostTxEvent(string name, uint256 counter, bytes context);

    constructor() payable {}

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external
    {
        bytes memory context = abi.encodePacked("context here");
        RIP7560Transaction memory txStruct = RIP7560Utils.decodeTransaction(version, transaction);
        string memory rule = string(txStruct.paymasterData);
        if (ValidationRules.eq(rule, "wrong-callback-method")) {
            ENTRY_POINT.call(abi.encodeCall(IRip7560EntryPointWrong.acceptPaymasterWrongSig, (666, 777, bytes("wrong context"))));
            return;
        }
        if (!rule.eq("context")) {
            ValidationRules.runRule(rule, ITestAccount(txStruct.sender), txStruct.paymaster, txStruct.deployer, coin, this, target);
        }
        RIP7560Utils.paymasterAcceptTransaction(context, 1, type(uint48).max -1 );
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
