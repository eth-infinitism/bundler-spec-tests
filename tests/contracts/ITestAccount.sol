// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IAccount.sol";

interface IState {
    function state() external returns (uint256);
}

interface ITestAccount is IState, IAccount {
}
