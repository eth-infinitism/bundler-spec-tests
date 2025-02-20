// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "./SimpleWallet.sol";

contract Test7702Wallet is SimpleWallet {

    constructor(address _ep) payable SimpleWallet(_ep) {}

    function validateUserOp(PackedUserOperation calldata userOp, bytes32, uint256 missingWalletFunds)
    public override virtual returns (uint256 validationData) {
        require(address(this).code.length == 23, "not eip-7702 account");
        return SimpleWallet.validateUserOp(userOp, "", missingWalletFunds);
    }

}
