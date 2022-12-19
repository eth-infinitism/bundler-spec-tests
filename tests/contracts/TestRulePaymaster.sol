// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./OpcodeRules.sol";
import "./SimpleWallet.sol";

contract TestRulePaymaster is IPaymaster {

    using OpcodeRules for string;

    TestCoin immutable coin = new TestCoin();
    uint something;

    constructor(address _ep) payable {
        if (_ep != address(0)) {
            (bool req,) = address(_ep).call{value : msg.value}("");
            require(req);
        }
    }

    function addStake(IEntryPoint ep, uint32 delay) public payable {
        ep.addStake{value: msg.value}(delay);
    }

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32, uint256)
    external returns (bytes memory context, uint256 deadline) {

        //first byte after paymaster address.
        string memory rule = string(userOp.paymasterAndData[20:]);
        if (rule.eq("no_storage")) {
            return ("", 0);
        }
        if (rule.eq("account_reference_storage")) {
            return ("", coin.balanceOf(userOp.sender));
        }
        if (rule.eq("account_reference_storage_init_code")) {
            return ("", coin.balanceOf(userOp.sender));
        }
        if (rule.eq("account_storage")) {
            return ("", SimpleWallet(userOp.sender).state());
        }
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
