pragma solidity ^0.8.15;
// SPDX-License-Identifier: MIT

import "./TestRulesAccount.sol";

contract TestRulesAccountFactory is Stakable {
    TestCoin public immutable coin = new TestCoin();
    address immutable ep;

    constructor(address _ep) {
        ep = _ep;
    }

    function create(uint nonce, string memory rule, address _ep) public returns (TestRulesAccount) {
        TestRulesAccount a = new TestRulesAccount{salt : bytes32(nonce)}(address(0));
        a.setCoin(coin);
        bool runRuleInFactory = false;
        if (runRuleInFactory) {
            a.runRule(rule);
        }
        return a;
    }
}

