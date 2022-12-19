// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "./OpcodeRules.sol";
import "./TestRulesAccount.sol";

contract TestRuleFactory {

    using OpcodeRules for string;

    TestCoin coin = new TestCoin();
    address entryPoint;

    constructor(address _entryPoint) {
        entryPoint = _entryPoint;
    }

    function create(uint nonce, string memory rule) public returns (IAccount) {
//        require(OpcodeRules.runRule(rule, coin) != OpcodeRules.UNKNOWN, string.concat("factory unknown rule: ", rule));
        TestRulesAccount ret = new TestRulesAccount{salt : bytes32(nonce)}(entryPoint);
        require(address(ret) != address(0), "create failed");
        return ret;
    }
}
