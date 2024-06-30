// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../Create2.sol";
import "../ValidationRules.sol";

import "./RIP7560TransactionStruct.sol";
import {TestAccount} from "./TestAccount.sol";

contract RIP7560Deployer is ValidationRulesStorage  {

    TestCoin public coin;
    // uint256 public deplCounter = 0;

    event DeployerEvent(string name, uint256 counter, address deployed);

    function createAccount(address owner, uint256 salt, string memory rule) external returns (address ret) {
        ret = address(new TestAccount{salt : bytes32(salt)}());

        ValidationRules.runRule(rule, this, coin, this);

        // emit DeployerEvent("the-deployer", deplCounter, ret);
        // deplCounter++;
    }

    function getCreate2Address(address owner, uint256 salt, string memory rule) public view returns (address) {
        return Create2.computeAddress(bytes32(salt), keccak256(abi.encodePacked(
            type(TestAccount).creationCode
        )));
    }
}
