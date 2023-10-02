// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./State.sol";
import "./Stakable.sol";

contract TestReputationPaymaster is IPaymaster, Stakable {

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

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32, uint256)
    external returns (bytes memory context, uint256 deadline) {
        require(state != 0xdead, "No bundle for you");
        return ("", 0);
    }

    receive() external payable {
    }
}
