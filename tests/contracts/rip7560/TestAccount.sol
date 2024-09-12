// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@rip7560/contracts/interfaces/IRip7560Transaction.sol";
import "@rip7560/contracts/utils/RIP7560Utils.sol";
import "./utils/TestUtils.sol";
import "@rip7560/contracts/interfaces/IRip7560Account.sol";

contract TestAccount is IRip7560Account {
    uint256 public accCounter = 0;
    uint256 public state = 0;

    event Funded(string id, uint256 amount);

    event AccountValidationEvent(uint256 state, uint256 counter);

    event AccountExecutionEvent(uint256 state, uint256 counter, bytes data);

    constructor() payable {
    }

    function validateTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) public virtual {

        emit AccountValidationEvent(state, accCounter);

        /* Modify account state */
        accCounter++;
        state = 1;

        RIP7560Utils.accountAcceptTransaction(1, type(uint48).max - 1);
    }

    function anyExecutionFunction() external {
        TestUtils.emitEvmData("anyExecutionFunction");

        emit AccountExecutionEvent(state, accCounter, msg.data);

        state = 2;
    }

    function revertingFunction() external {
        revert("reverting");
    }

    function reset() external {
        state = 0;
        accCounter = 0;
    }

    receive() external payable {
        emit Funded("account", msg.value);
    }

    fallback(bytes calldata) external returns (bytes memory) {
//        accCounter++;
//        emit AccountEvent("account", string(msg.data));
        return "account-returned-data-here";
    }

    function funTSTORE() external returns(uint256) {
        assembly {
            tstore(0, 1)
        }
        return 0;
    }
}
