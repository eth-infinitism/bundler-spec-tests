// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "../Stakable.sol";
import "./TestAccount.sol";
import {IRip7560Paymaster} from "@rip7560/contracts/interfaces/IRip7560Paymaster.sol";
import "../ValidationRules.sol";

contract TestPostOpPaymaster is IRip7560Paymaster {
    using ValidationRules for string;
    uint256 public counter;
    constructor() payable {}

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external {
        RIP7560Transaction memory txStruct = RIP7560Utils.decodeTransaction(version, transaction);
        bytes memory context = txStruct.authorizationData;
        if (string(context).eq("no context")) {
            context = "";
        }
        RIP7560Utils.paymasterAcceptTransaction(context, 1, type(uint48).max - 1);
    }

    function postPaymasterTransaction(
        bool success,
        uint256 actualGasCost,
        bytes calldata context
    ) external {
        string memory rule = string(context);
        if (rule.eq("revert")) {
            revert();
        }
        counter++;
    }

}
