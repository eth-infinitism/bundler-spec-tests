// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

contract TestCounter {
    uint256 public counter = 0;

    function increment() external {
        counter++;
    }
}
