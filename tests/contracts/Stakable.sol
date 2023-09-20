// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IStakeManager.sol";

abstract contract Stakable {

    function addStake(IStakeManager stakeManager, uint32 _unstakeDelaySec) external payable {
        stakeManager.addStake{value: msg.value}(_unstakeDelaySec);
    }
    function unlockStake(IStakeManager stakeManager) external {
        stakeManager.unlockStake();
    }
    function withdrawStake(IStakeManager stakeManager, address payable withdrawAddress) external {
        stakeManager.withdrawStake(withdrawAddress);
    }
}
