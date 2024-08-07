// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../Create2.sol";
import "../ValidationRules.sol";

import "./RIP7560TransactionStruct.sol";
import {TestAccount} from "./TestAccount.sol";

contract RIP7560Deployer is ValidationRulesStorage  {
    using ValidationRules for string;
    TestCoin immutable public coin = new TestCoin();

    event DeployerEvent(string name, uint256 counter, address deployed);
    event Uint(uint);

    constructor () payable {}

    function createAccount(address owner, uint256 salt, string memory rule) external returns (address ret) {
        address create2address = getCreate2Address(owner, salt, rule);
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
            emit Uint(uint256(keccak256(create2address.code)));
            if (create2address == address(0)) revert();
            // EXTCODEHASH
            emit Uint(uint256(create2address.codehash));
            // EXTCODECOPY
            assembly {
                extcodecopy(create2address, 0, 0, 2)
            }
        }
        if (ValidationRules.eq(rule, "skip-deploy-msg")){
            return address(0);
        }
        ret = address(new TestAccount{salt : bytes32(salt)}());
        if (!rule.eq("EXTCODEx_CALLx_undeployed_sender")) {
            ValidationRules.runRule(rule, ITestAccount(ret), coin, this);
        }
    }

    function getCreate2Address(address owner, uint256 salt, string memory rule) public view returns (address) {
        return Create2.computeAddress(bytes32(salt), keccak256(abi.encodePacked(
            type(TestAccount).creationCode
        )));
    }
}
