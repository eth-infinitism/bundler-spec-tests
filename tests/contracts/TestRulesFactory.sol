// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "./Create2.sol";
import "./SimpleWallet.sol";
import "./Stakable.sol";
import "./ValidationRules.sol";
import "@account-abstraction/contracts/interfaces/IAccount.sol";

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
            ValidationRules.runFactorySpecificRule(nonce, rule, _entryPoint, create2address);
        }
        else if (rule.eq("DELEGATECALL:>EXTCODEx_CALLx_undeployed_sender")) {
            string memory innerRule = rule.slice(14, bytes(rule).length - 14);
            bytes memory callData = abi.encodeCall(target.runFactorySpecificRule, (nonce, rule, _entryPoint, create2address));
            (bool success, bytes memory ret) = address(target).delegatecall(callData);
            require(success, string(abi.encodePacked("DELEGATECALL rule reverted", ret)));
        }
        else if (rule.eq("CALL:>EXTCODEx_CALLx_undeployed_sender")) {
            string memory innerRule = rule.slice(6, bytes(rule).length - 6);
            target.runFactorySpecificRule(nonce, rule, _entryPoint, create2address);
        }

        account = new SimpleWallet{salt: bytes32(nonce)}(_entryPoint);
        require(address(account) != address(0), "create failed");
        // do not revert on rules checked before account creation
        if (rule.includes("EXTCODEx_CALLx_undeployed_sender")) {}
        else {
            ValidationRules.runRule(rule, account, address(0), address(this), coin, this, target);
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
