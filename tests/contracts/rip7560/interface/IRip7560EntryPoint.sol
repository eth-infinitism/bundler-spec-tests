// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

interface IRip7560EntryPoint {
    function acceptAccount(uint256 validAfter, uint256 validUntil) external returns (bool);
    function sigFailAccount(uint256 validAfter, uint256 validUntil) external returns (bool);
    function acceptPaymaster(uint256 validAfter, uint256 validUntil, bytes calldata context) external returns (bool);
}
