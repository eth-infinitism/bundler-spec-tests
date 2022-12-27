// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "./OpcodeRules.sol";
import "./SimpleWallet.sol";
import "./Stakable.sol";

contract TestRulesFactory is Stakable {

    using OpcodeRules for string;

    TestCoin coin = new TestCoin();
    address entryPoint;

    constructor(address _entryPoint) {
        entryPoint = _entryPoint;
    }

    event Address(address);
    event Uint(uint);

    function create(uint nonce, string memory rule, address _entryPoint) public returns (SimpleWallet account) {
        account = new SimpleWallet{salt : bytes32(nonce)}(_entryPoint);
        require(address(account) != address(0), "create failed");
        if (rule.eq("")) {
        }
        else if (rule.eq("no_storage")) {
        }
        else if (rule.eq("storage")) {
            emit Address(entryPoint);
        }
        else if (rule.eq("reference_storage")) {
            emit Uint(coin.balanceOf(address(this)));
        }
        else if (rule.eq("account_storage")) {
            emit Uint(account.state());
        }
        else if (rule.eq("account_reference_storage")) {
            emit Uint(coin.balanceOf(address(account)));
        }
        else {
            require(OpcodeRules.runRule(rule, coin) != OpcodeRules.UNKNOWN, string.concat("unknown rule: ", rule));
        }
        return account;
    }
}
