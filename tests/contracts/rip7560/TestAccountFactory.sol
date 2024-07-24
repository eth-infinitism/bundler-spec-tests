pragma solidity ^0.8.25;

import "../Stakable.sol";
import "./TestAccount.sol";

contract TestAccountFactory is Stakable {
    function createAccount(uint salt) external returns (address) {
        return address(new TestAccount{salt: bytes32(salt)}());
    }
}
