// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@rip7560/contracts/interfaces/IRip7560Paymaster.sol";
import "@rip7560/contracts/utils/RIP7560Utils.sol";

contract RIP7560TestTimeRangePaymaster is IRip7560Paymaster {

    constructor() payable {}

    function validatePaymasterTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction)
    external
    {
        RIP7560Transaction memory txStruct = RIP7560Utils.decodeTransaction(version, transaction);
        (uint48 validAfter, uint48 validUntil) =
                            abi.decode(txStruct.paymasterData, (uint48, uint48));
        RIP7560Utils.paymasterAcceptTransaction("", validAfter, validUntil);
    }
    function postPaymasterTransaction(
        bool success,
        uint256 actualGasCost,
        bytes calldata context
    ) external {}
}
