// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "./OpcodeRules.sol";
contract TestRuleFactory {

    using OpcodeRules for string;

    TestCoin coin = new TestCoin();
    address entryPoint;

    constructor(address _entryPoint) {
        entryPoint = _entryPoint;
    }


    function create(uint nonce, string memory rule) public returns (IAccount) {
        if (eq(rule, 'TestOpcodeAccount')) return new TestRulesAccount{salt : bytes32(nonce)}(entryPoint);
        revert(string.concat("unknown rule: ", rule));
    }
}
