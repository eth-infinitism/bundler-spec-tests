// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "../Stakable.sol";
import "./TestAccount.sol";
import {IRip7560Paymaster} from "./interface/IRip7560Paymaster.sol";

contract TestPaymaster is IRip7560Paymaster {

    constructor() payable {}

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external
    {
        RIP7560Utils.paymasterAcceptTransaction("!hello hello hello!", 1, type(uint48).max - 1);
    }

    function postPaymasterTransaction(
        bool success,
        uint256 actualGasCost,
        bytes calldata context
    ) external {}

}
