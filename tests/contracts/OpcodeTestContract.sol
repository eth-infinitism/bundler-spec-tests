// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.11;

import "./UserOperation.sol";
import "./IPaymaster.sol";

contract Dummy  {}

/**
 * helper contract for testing banned opcodes.
 * rule - the opcode "rule" to ban. zero == not banned
 * 3 running modes:
 * - trigger rule during contract creation
 * - trigger rule during contract validation
 * - as a paymaster, trigger rule during paymater validation
 */
contract OpcodeTestContract is IPaymaster {

    uint rule;
    constructor(uint _rule) {
        rule = _rule;
    }

    //executed when initCode is TestDeployer.setup
    function init() public returns (uint _rule) {
        return checkRule(_rule);
    }

    //executed when this is a constructed wallet
    function validateUserOp(UserOperation calldata , bytes32 , address , uint256 )
    external {
        checkRule(rule);
    }

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32 , uint256 )
    external returns (bytes memory context) {
        //first byte after paymaster address.
        rule = uint8(userOp.paymasterAndData[40]);
        return ("");
    }

    function checkRule(uint _rule) internal returns (uint) {
        if (_rule == 0) return 0;
        //rule 0 is "ok"
        else if (_rule == 1) return gasleft();
        else if (_rule == 2) return block.number;
        else if (_rule == 3) return block.timestamp;
        else if (_rule == 4) return uint160(address(block.coinbase));
        else if (_rule == 5) return block.difficulty;
        else if (_rule == 6) return block.basefee;
        else if (_rule == 7) return block.gaslimit;
        //trigger keccak precompile
        else if (_rule == 10) return uint(keccak256(msg.data));
        // future precompile
        else if (_rule == 11) {
            (bool success,) = address((100)).call("");
            return success ? 1 : 0;
        }
        //un-deployed contact
        else if (_rule == 12) {
            (bool success,) = address(0xdeaddeaddead).call("xxx");
            return success ? 1 : 0;
        }
        //create a contract
        else if (_rule == 13) return uint160(address(new Dummy()));
        //create2 a contract
        else if (_rule == 14) return uint160(address(new Dummy {salt : bytes32(uint256(uint160(address(this))))}()));
        return 0;
    }

    function postOp(PostOpMode, bytes calldata, uint256) external {}

}

contract TestDeployer {
    //call the checkRule as part of init (during deployment)
    function setupAndInit(uint rule, bytes32 salt) external returns (address) {
        OpcodeTestContract a = new OpcodeTestContract{salt : salt}(rule);
        a.init();
        return address(a);
    }

    // create wallet, but don't call checkRule. will get called during validateUserOperation
    function setup(uint rule, bytes32 salt) external returns (address)  {
        OpcodeTestContract a = new OpcodeTestContract{salt : salt}(rule);
        return address(a);
    }
}
