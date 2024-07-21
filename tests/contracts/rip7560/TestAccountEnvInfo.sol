// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../ITestAccount.sol";

import "./RIP7560TransactionType4.sol";
import "./utils/RIP7560Utils.sol";
import "./utils/TestUtils.sol";
import {TestAccount} from "./TestAccount.sol";

contract TestAccountEnvInfo is TestAccount {

    constructor() payable {}
    TestUtils.OpcodesOutput public opcodes;

//    function validateTransaction(
//        uint256 version,
//        bytes32 txHash,
//        bytes calldata transaction
//    ) external virtual override returns (uint256) {
//
////        TestUtils.emitEvmData("validateTransaction");
//        return RIP7560Utils.accountAcceptTransaction(1, type(uint48).max - 1);
//
//    }

    function getStoredOpcodes() external view returns (TestUtils.OpcodesOutput memory) {
        return opcodes;
    }

    function saveEventOpcodes() external {
        opcodes = TestUtils.getOpcodesOutput();
    }
}
