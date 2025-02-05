// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

library UserOpGetters {
    function getFactory(PackedUserOperation memory op) internal pure returns (address) {
        if (op.initCode.length < 20) {
            return address(0);
        }
        return bytesToAddress(op.initCode);
    }

    function getPaymaster(PackedUserOperation memory op) internal pure returns (address) {
        if (op.paymasterAndData.length < 20) {
            return address(0);
        }
        return bytesToAddress(op.paymasterAndData);
    }

    function bytesToAddress(bytes memory data) private pure returns (address) {
        return address(bytes20(data));
    }
}
