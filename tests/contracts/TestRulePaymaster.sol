// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

contract TestRulePaymaster is IPaymaster {

    event Deployed();
    //TODO: better do it externally, but need to pass value to methods in pythonn..
    constructor() {// }IEntryPoint ep, uint stake, uint32 stakeTime) payable {
        emit Deployed();
        //        if (address(ep) != address(0)) {
        //            require(stake==0, "expected no stake");
        //            uint deposit = msg.value - stake;
        //            ep.depositTo{value : deposit}(address(this));
        //            ep.addStake{value : stake}(stakeTime);
        //        }
    }

    function eq(string memory a, string memory b) internal returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function asdasd() public view returns (address) {
        return address(this);
    }

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32, uint256)
    external returns (bytes memory context, uint256 deadline) {
        //first byte after paymaster address.
//        runRule(string(userOp.paymasterAndData[20 :]));
        return ("", 0);
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost) external {}
}
