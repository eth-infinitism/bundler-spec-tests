// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "../../Stakable.sol";
import "../TestAccount.sol";
import {IRip7560Paymaster} from "@rip7560/contracts/interfaces/IRip7560Paymaster.sol";

contract OpcodesTestPaymaster is IRip7560Paymaster {

    constructor() payable {}

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external
    {
        TestUtils.emitEvmData("paymaster-validation");
        RIP7560Utils.paymasterAcceptTransaction("!hello hello hello!", 1, type(uint48).max - 1);
    }

    function postPaymasterTransaction(
        bool success,
        uint256 actualGasCost,
        bytes calldata context
    ) external {
        TestUtils.emitEvmData("paymaster-postop");
    }

}
