// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "../ITestAccount.sol";

import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";
import "@rip7560/contracts/utils/RIP7560Utils.sol";
import "./utils/TestUtils.sol";
import {TestAccount} from "./TestAccount.sol";

contract TestAccountEnvInfo is TestAccount {

    constructor() payable {}

    //todo: emit opcodes from validationTransaction too

    function saveEventOpcodes() external {
        TestUtils.emitEvmData("exec");
    }
}
