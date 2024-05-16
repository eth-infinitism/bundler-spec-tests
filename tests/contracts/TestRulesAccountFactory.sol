pragma solidity ^0.8.25;
// SPDX-License-Identifier: MIT

import "./TestRulesAccount.sol";
import "./ValidationRules.sol";

contract TestRulesAccountFactory is Stakable, ValidationRulesStorage {
    TestCoin public immutable coin = new TestCoin();
    constructor(address _ep) {
        entryPoint = IEntryPoint(_ep);
    }

    function create(uint nonce, string memory rule, address _ep) public returns (TestRulesAccount) {
        TestRulesAccount account = new TestRulesAccount{salt : bytes32(nonce)}(_ep);
        account.setCoin(coin);
        return account;
    }
}

