// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "../../@account-abstraction/contracts/interfaces/IPaymaster.sol";

/// @dev A test contract that represents a potential attack where a wallet entity is also
/// used as a Paymaster by a different PackedUserOperation.
/// This allows this couple of UserOperations to escape the sandbox and invalidate a bundle.
contract TestFakeWalletPaymaster is IAccount, IPaymaster {

    IEntryPoint entryPoint;

    constructor(address _ep) payable {
        entryPoint = IEntryPoint(_ep);
    }

    function validateUserOp(PackedUserOperation calldata userOp, bytes32, uint256 missingWalletFunds)
    public override returns (uint256 validationData) {
        validationData = 0;
    }

    function validatePaymasterUserOp(PackedUserOperation calldata userOp, bytes32 userOpHash, uint256 maxCost)
    external returns (bytes memory context, uint256 validationData){
        context = "";
        validationData = 0;
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost, uint) external {}

    receive() external payable {
        entryPoint.depositTo{value: msg.value}(address(this));
    }

    fallback() external {}
}
