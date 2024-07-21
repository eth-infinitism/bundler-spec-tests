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

    //todo: save opcodes from validationTransaction too

    function getStoredOpcodes() external view returns (TestUtils.OpcodesOutput memory) {
        return opcodes;
    }

    function saveEventOpcodes() external {
        opcodes = TestUtils.getOpcodesOutput();
    }
}
