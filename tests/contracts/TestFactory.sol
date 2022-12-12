// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;


import "./TestRulesAccount.sol";

contract TestFactory {

    TestCoin coin = new TestCoin();
    address entryPoint;

    constructor(address _entryPoint) {
        entryPoint = _entryPoint;
    }

    function eq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function create(string memory rule) public returns (IAccount) {
        if (eq(rule, 'TestOpcodeAccount')) return new TestRulesAccount{salt : bytes32(0)}(entryPoint);
        revert(string.concat("unknown rule: ", rule));
    }
}
