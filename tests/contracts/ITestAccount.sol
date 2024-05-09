// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "@account-abstraction/contracts/interfaces/IAccount.sol";

interface IState {
    function state() external returns (uint256);

    function funTSTORE() external returns(uint256);
}

interface ITestAccount is IState, IAccount {
}
