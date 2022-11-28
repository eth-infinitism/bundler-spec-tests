// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.11;

import "./IWallet.sol";
import "./UserOperation.sol";
import "./IEntryPoint.sol";

contract SimpleWallet is IWallet {

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
    external override {
        if (missingWalletFunds>0) {
            msg.sender.call{value:missingWalletFunds}("");
        }
        bytes2 dead = bytes2(userOp.signature);
        require(dead != 0xdead, "testWallet: dead signature");
    }

    // todo move
    function getRequestId(UserOperation calldata userOp) public view returns (bytes32) {
        return IEntryPoint(ep).getRequestId(userOp);
    }
}
