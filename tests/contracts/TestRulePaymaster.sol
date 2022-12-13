// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./OpcodeRules.sol";

contract TestRulePaymaster is IPaymaster {

    using OpcodeRules for string;

    TestCoin immutable coin = new TestCoin();
    uint something;

    function addStake(IEntryPoint ep, uint32 delay) public payable {
        ep.addStake{value: msg.value}(delay);
    }

    function asdasd() public view returns (address) {
        return address(this);
    }

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32, uint256)
    external returns (bytes memory context, uint256 deadline) {

        //first byte after paymaster address.
        string memory rule = string(userOp.paymasterAndData[20 :]);
        if(rule.eq("self-storage")) {
            return ("", something);
        }
        if (rule.eq("expired")) {
            return ("", 1);
        }
        if (rule.eq("context")) {
            return ("this is a context", 0);
        }
        require(OpcodeRules.runRule(rule, coin) != OpcodeRules.UNKNOWN, string.concat("unknown rule: ", rule));
        return ("", 0);
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost) external {}
}
