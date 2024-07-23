// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

uint160 constant MAGIC_VALUE_SENDER = 0xbf45c166;
uint160 constant MAGIC_VALUE_PAYMASTER = 0xe0e6183a;

library RIP7560Utils {

    function accountAcceptTransaction(
        uint48 validAfter,
        uint48 validUntil
    ) internal returns (
        uint256
    ){
//        return MAGIC_VALUE_SENDER | (uint256(validUntil)<<160) | (uint256(validAfter) << (160+48));
        return (uint256(MAGIC_VALUE_SENDER) << (48+48)) | (uint256(validUntil)<<48) | validAfter ;
    }

    function paymasterAcceptTransaction(
        bytes memory context,
        uint256 validAfter,
        uint256 validUntil
    ) internal returns (
        bytes memory
    ){
        uint256 validationData = (uint256(MAGIC_VALUE_PAYMASTER) << (48+48)) | (uint256(validUntil)<<48) | validAfter;
        bytes memory ret = abi.encode(validationData, context);
        uint256 len = ret.length;
        // avoid wrapping return value as a byte array here
        assembly {
            return(add(ret, 0x20), len)
        }
    }
}
