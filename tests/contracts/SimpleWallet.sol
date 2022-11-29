// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

contract SimpleWallet is IAccount {

    address ep;
    uint256 public state;

    constructor(address _ep) payable {
        ep = _ep;
        (bool req,) = address(ep).call{value : msg.value}("");
        require(req);
    }

    function setState(uint _state) external {
        state=_state;
    }

    function validateUserOp(UserOperation calldata userOp, bytes32, address, uint256 missingWalletFunds)
    external override returns (uint256 deadline) {
        if (missingWalletFunds>0) {
            msg.sender.call{value:missingWalletFunds}("");
        }
        bytes2 dead = bytes2(userOp.signature);
        require(dead != 0xdead, "testWallet: dead signature");
        return 0;
    }

    // todo move
    function getUserOpHash(UserOperation calldata userOp) public view returns (bytes32) {
        return IEntryPoint(ep).getUserOpHash(userOp);
    }
}
