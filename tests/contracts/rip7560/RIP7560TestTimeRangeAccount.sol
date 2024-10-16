// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@rip7560/contracts/interfaces/IRip7560Account.sol";
import "@rip7560/contracts/utils/RIP7560Utils.sol";

contract RIP7560TestTimeRangeAccount is IRip7560Account {

    constructor() payable {}

    function validateTransaction(
        uint256 version,
        bytes32 txHash,
        bytes calldata transaction
    ) external {
        RIP7560Transaction memory txStruct = RIP7560Utils.decodeTransaction(version, transaction);
        (uint48 validAfter, uint48 validUntil) =
                            abi.decode(txStruct.authorizationData, (uint48, uint48));
        RIP7560Utils.accountAcceptTransaction(validAfter, validUntil);
    }
}
