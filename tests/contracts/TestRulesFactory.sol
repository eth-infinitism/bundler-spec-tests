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
        // note that the 'EXT*'/'CALL*' opcodes are allowed on the zero code address if it is later deployed
        address create2address = getAddress(nonce, _entryPoint);
        if (rule.eq("EXTCODEx_CALLx_undeployed_sender")) {
            // CALL
            create2address.call("");
            // CALLCODE
            assembly {
                let res := callcode(5000, create2address, 0, 0, 0, 0, 0)
            }
            // DELEGATECALL
            create2address.delegatecall("");
            // STATICCALL
            create2address.staticcall("");
            // EXTCODESIZE
            emit Uint(create2address.code.length);
            // EXTCODEHASH
            emit Uint(uint256(create2address.codehash));
            // EXTCODECOPY
            assembly {
                extcodecopy(create2address, 0, 0, 2)
            }
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
        else if (rule.eq("CALL_undeployed_contract")) {
            address(100100).call("");
        }
        else if (rule.eq("CALLCODE_undeployed_contract")) {
            assembly {
                let res := callcode(5000, 100200, 0, 0, 0, 0, 0)
            }
        }
        else if (rule.eq("DELEGATECALL_undeployed_contract")) {
            address(100300).delegatecall("");
        }
        else if (rule.eq("STATICCALL_undeployed_contract")) {
            address(100400).staticcall("");
        }
        else if (rule.eq("EXTCODESIZE_undeployed_contract")) {
            emit Uint(address(100500).code.length);
        }
        else if (rule.eq("EXTCODEHASH_undeployed_contract")) {
            emit Uint(uint256(address(100600).codehash));
        }
        else if (rule.eq("EXTCODECOPY_undeployed_contract")) {
            assembly {
                extcodecopy(100700, 0, 0, 2)
            }
        }
        // do not revert on rules checked before account creation
        else if (rule.eq("EXTCODEx_CALLx_undeployed_sender")) {}
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
