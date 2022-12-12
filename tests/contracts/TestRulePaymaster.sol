// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./OpcodeRules.sol";

contract TestRulePaymaster is IPaymaster {

    TestCoin immutable coin = new TestCoin();

    //TODO: better do it externally, but need to pass value to methods in pythonn..
    constructor() {// }IEntryPoint ep, uint stake, uint32 stakeTime) payable {
        //        if (address(ep) != address(0)) {
        //            require(stake==0, "expected no stake");
        //            uint deposit = msg.value - stake;
        //            ep.depositTo{value : deposit}(address(this));
        //            ep.addStake{value : stake}(stakeTime);
        //        }
    }

    function addStake(IEntryPoint ep, uint32 delay) public payable {
        ep.addStake{value: msg.value}(delay);
    }

    function eq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function asdasd() public view returns (address) {
        return address(this);
    }

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32, uint256)
    external returns (bytes memory context, uint256 deadline) {

        //first byte after paymaster address.
        string memory rule = string(userOp.paymasterAndData[20 :]);
        if (OpcodeRules.eq(rule, "expiredd")) {
            return ("", 1);
        }
        require(OpcodeRules.runRule(rule, coin) != OpcodeRules.UNKNOWN, string.concat("unknown rule: ", rule));
        return ("", 0);
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost) external {}
}
