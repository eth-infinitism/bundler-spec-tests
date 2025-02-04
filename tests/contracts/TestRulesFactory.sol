// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "./Create2.sol";
import "./ValidationRules.sol";
import "./SimpleWallet.sol";
import "./Stakable.sol";

contract TestRulesFactory is Stakable, ValidationRulesStorage {

    using ValidationRules for string;

    TestCoin private immutable coin = new TestCoin();
    TestRulesTarget private immutable target = new TestRulesTarget();

    constructor(address _entryPoint) {
        entryPoint = IEntryPoint(_entryPoint);
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
        // do not revert on rules checked before account creation
        if (rule.eq("EXTCODEx_CALLx_undeployed_sender")) {}
        else {
            ValidationRules.runRule(rule, account, coin, this, target);
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
