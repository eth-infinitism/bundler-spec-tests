pragma solidity ^0.8.15;
//SPDX-License-Identifier: MIT

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

contract Helper {

    //helper to return address (ep.getSenderAddress returns the address as an exception, which is hard to catch)
    function getSenderAddress(IEntryPoint ep, bytes memory initCode) public returns (address ret) {
        try ep.getSenderAddress(initCode) {
            revert("expected to revert with SenderAddressResult");
        }
        catch(bytes memory ret) {
            require(ret.length == 32 + 4, "wrong thrown data");
            assembly {
            //skip length, 4-byte error methodsig.
                ret := mload(add(ret, 36))
            }
        }
    }
}

