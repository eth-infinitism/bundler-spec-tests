pragma solidity ^0.8.15;
//SPDX-License-Identifier: MIT

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

contract Helper {

    //helper to return address (ep.getSenderAddress returns the address as an exception, which is hard to catch)
    function getSenderAddress(IEntryPoint ep, bytes memory initCode) public returns (address addr) {
        try ep.getSenderAddress(initCode) {
            revert("expected to revert with SenderAddressResult");
        }
        catch(bytes memory ret) {
            (bool success, bytes memory ret1) = address(this).call(ret);
            require(success, string.concat("wrong error sig ", string(ret)));
            addr = abi.decode(ret1, (address));
        }
    }

    //helper to parse the "error SenderAddressResult" (by exposing same inteface
    function SenderAddressResult(address sender) external returns (address){
        return sender;
    }

    function getUserOpHash(IEntryPoint ep, UserOperation calldata userOp) public view returns (bytes32) {
        return IEntryPoint(ep).getUserOpHash(userOp);
    }
}
