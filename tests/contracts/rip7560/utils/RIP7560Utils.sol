// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

bytes4 constant MAGIC_VALUE_SENDER = 0xbf45c166;
bytes4 constant MAGIC_VALUE_PAYMASTER = 0xe0e6183a;

library RIP7560Utils {

    function accountAcceptTransaction(
        uint64 validAfter,
        uint64 validUntil
    ) internal returns (
        bytes32
    ){
        return bytes32(abi.encodePacked(MAGIC_VALUE_SENDER, validAfter, validUntil));
    }

    function paymasterAcceptTransaction(
        bytes memory context,
        uint256 validAfter,
        uint256 validUntil
    ) internal returns (
        bytes memory
    ){
        bytes memory ret = abi.encodeWithSelector(MAGIC_VALUE_PAYMASTER, context, validAfter, validUntil);
        uint256 len = ret.length;
        // avoid wrapping return value as a byte array here
        assembly {
            return(add(ret, 0x20), len)
        }
    }
}
