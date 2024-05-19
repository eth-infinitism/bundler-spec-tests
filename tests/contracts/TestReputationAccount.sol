// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./State.sol";
import "./ITestAccount.sol";
import "./Stakable.sol";

contract TestReputationAccount is ITestAccount, Stakable {

    IEntryPoint ep;
    uint256 public state;

    constructor(address _ep) payable {
        ep = IEntryPoint(_ep);
        (bool req,) = address(ep).call{value : msg.value}("");
        require(req);
    }

    function setState(uint _state) external {
        state=_state;
    }

    function validateUserOp(PackedUserOperation calldata userOp, bytes32, uint256 missingWalletFunds)
    public override virtual returns (uint256 validationData) {
        require(state != 0xdead, "No bundle for you");
        if (missingWalletFunds>0) {
            msg.sender.call{value:missingWalletFunds}("");
        }
        return 0;
    }
    function funTSTORE() external returns(uint256) {
        return 0;
    }

    receive() external payable {
    }
}
