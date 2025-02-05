// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./TestRulesTarget.sol";
import "./ValidationRulesStorage.sol";
import "./ValidationRules.sol";
import "./TestCoin.sol";

contract TestRulesTarget is ValidationRulesStorage {

    receive() external payable {}

    function runFactorySpecificRule(
        uint nonce,
        string memory rule,
        address _entryPoint,
        address create2address
    ) external payable {
        return ValidationRules.runFactorySpecificRule(nonce, rule, _entryPoint, create2address);
    }

    function runRule(
        string memory rule,
        IState account,
        address paymaster,
        address factory,
        TestCoin coin,
        ValidationRulesStorage self,
        TestRulesTarget target
    ) external payable returns (uint) {
        return ValidationRules.runRule(rule, account, paymaster, factory, coin, self, target);
    }
}
