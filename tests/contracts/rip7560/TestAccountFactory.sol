pragma solidity ^0.8.25;

import "../Stakable.sol";
import "./TestAccount.sol";

contract TestAccountFactory is Stakable {
    event TestFactoryEvent(uint salt);
    function createAccount(uint salt) external returns (address) {
        emit TestFactoryEvent(salt);
        return address(new TestAccount{salt: bytes32(salt)}());
    }
}
