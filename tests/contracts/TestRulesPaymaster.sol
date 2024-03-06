// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "@account-abstraction/contracts/core/UserOperationLib.sol";
import "./ValidationRules.sol";
import "./SimpleWallet.sol";

contract TestRulesPaymaster is IPaymaster, ValidationRulesStorage {
    using ValidationRules for string;

    TestCoin immutable coin = new TestCoin();
//    IEntryPoint public entryPoint;

    constructor(address _ep) payable {
        entryPoint = IEntryPoint(_ep);
        if (_ep != address(0)) {
            (bool req,) = address(_ep).call{value : msg.value}("");
            require(req);
        }
    }

    function addStake(IEntryPoint ep, uint32 delay) public payable {
        ep.addStake{value: msg.value}(delay);
    }

    function validatePaymasterUserOp(PackedUserOperation calldata userOp, bytes32, uint256)
    external returns (bytes memory context, uint256 deadline) {

        //first byte after paymaster address.
        string memory rule = string(userOp.paymasterAndData[UserOperationLib.PAYMASTER_DATA_OFFSET:]);
        if (rule.eq("context")) {
            return ("this is a context", 0);
        } else if (rule.eq("nothing")) {
            return ("", 0);
        } else {
            ValidationRules.runRule(rule, ITestAccount(userOp.sender), coin, this);
            return ("", 0);
        }
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost, uint) external {}

    receive() external payable {
        entryPoint.depositTo{value: msg.value}(address(this));
    }
}
