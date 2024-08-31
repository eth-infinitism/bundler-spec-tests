// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../Create2.sol";
import "../ValidationRules.sol";
import "../Stakable.sol";

import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";
import "./RIP7560TestRulesAccount.sol";

contract RIP7560TestRulesAccountDeployer is Stakable {
    TestCoin public immutable coin = new TestCoin();
    constructor() payable {
    }

    function createAccount(address owner, uint256 salt, string memory rule) public returns (RIP7560TestRulesAccount) {
        RIP7560TestRulesAccount account = new RIP7560TestRulesAccount{salt : bytes32(salt)}();
        account.setCoin(coin);
        return account;
    }

    function getCreate2Address(address owner, uint256 salt, string memory rule) public view returns (address) {
        return Create2.computeAddress(bytes32(salt), keccak256(abi.encodePacked(
            type(RIP7560TestRulesAccount).creationCode
        )));
    }
}
