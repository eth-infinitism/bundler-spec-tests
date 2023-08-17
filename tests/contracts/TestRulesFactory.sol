// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "./Create2.sol";
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

    receive() external payable {}

    event Address(address);
    event Uint(uint);

    function create(uint nonce, string memory rule, address _entryPoint) public returns (SimpleWallet account) {
        // note that the 'EXT*' opcodes are banned on the zero code address even if it is later deployed
        address create2address = getAddress(nonce, _entryPoint);
        if (rule.eq("EXTCODESIZE_SENDER")) {
            emit Uint(create2address.code.length);
        }
        else if (rule.eq("EXTCODEHASH_SENDER")) {
            emit Uint(uint256(create2address.codehash));
        }
        else if (rule.eq("EXTCODECOPY_SENDER")) {
            bytes memory code = create2address.code;
            emit Uint(code.length);
        }

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
        else if (rule.eq("external_storage")) {
            emit Uint(coin.balanceOf(address(0xdeadcafe)));
        }
        else if (rule.eq("account_reference_storage_struct")) {
            emit Uint(coin.getInfo(address(account)).c);
        }
        else if (rule.eq("reference_storage_struct")) {
            emit Uint(coin.getInfo(address(this)).c);
        }
        else if (rule.eq("SELFDESTRUCT")) {
            coin.destruct();
        }
        else if (rule.eq("EXTCODESIZE")) {
            emit Uint(address(100500).code.length);
        }
        else if (rule.eq("EXTCODEHASH")) {
            emit Uint(uint256(address(100600).codehash));
        }
        else if (rule.eq("EXTCODECOPY")) {
            bytes memory code = address(100700).code;
            emit Uint(code.length);
        }
        // do not revert on rules checked before account creation
        else if (rule.eq("EXTCODESIZE_SENDER")) {}
        else if (rule.eq("EXTCODEHASH_SENDER")) {}
        else if (rule.eq("EXTCODECOPY_SENDER")) {}
        else {
            require(OpcodeRules.runRule(rule, coin) != OpcodeRules.UNKNOWN, string.concat("unknown rule: ", rule));
        }
        return account;
    }


    /**
     * calculate the counterfactual address of this account as it would be returned by createAccount()
     */
    function getAddress(uint256 salt, address _entryPoint) public view returns (address) {
        return Create2.computeAddress(bytes32(salt), keccak256(abi.encodePacked(
            type(SimpleWallet).creationCode,
            abi.encode(
                address(_entryPoint)
            )
        )));
    }
}
