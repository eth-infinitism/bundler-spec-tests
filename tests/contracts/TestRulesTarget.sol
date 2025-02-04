// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./ValidationRulesStorage.sol";
import "./ValidationRules.sol";
import "./TestCoin.sol";

contract TestRulesTarget is IState {
    uint256 public state;

    function setState(uint _state) external {
        state = _state;
    }

    function runRule(string memory rule, IState account, TestCoin coin, ValidationRulesStorage self, TestRulesTarget target) external returns (uint) {
        return ValidationRules.runRule(rule, account, coin, self, target);
    }

    function funTSTORE() external returns(uint256) {
        assembly {
            tstore(0, 1)
        }
        return 0;
    }
}
