// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

contract TestAccountErigon {
    address constant ENTRY_POINT = 0x0000000000000000000000000000000000007560;
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

        accountAcceptTransaction(1, type(uint48).max - 1);
    }

    function anyExecutionFunction() external {
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

    function accountAcceptTransaction(
        uint48 validAfter,
        uint48 validUntil
    ) internal {
        (bool success,) = ENTRY_POINT.call(
            abi.encodeCall(this.acceptAccount, (validAfter, validUntil))
        );
        require(success);
    }

    function acceptAccount(uint256 validAfter, uint256 validUntil) external {}
}
