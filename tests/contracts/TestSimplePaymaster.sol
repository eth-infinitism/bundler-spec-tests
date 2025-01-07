//SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

contract TestSimplePaymaster is IPaymaster {
    IEntryPoint public entryPoint;
    constructor(address _ep) payable {
        entryPoint = IEntryPoint(_ep);
        if (_ep != address(0)) {
            (bool req,) = address(_ep).call{value : msg.value}("");
            require(req);
        }
    }

    function validatePaymasterUserOp(PackedUserOperation calldata userOp, bytes32, uint256) external returns (bytes memory context, uint256 validationData) {
        return ("", 0);
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost, uint) external {}

    function withdrawTo(address payable to, uint256 amount) external {
        entryPoint.withdrawTo(to, amount);
    }

    receive() external payable {
        entryPoint.depositTo{value: msg.value}(address(this));
    }
}

