pragma solidity ^0.8.25;

import "./OpcodesTestAccount.sol";

contract OpcodesTestAccountFactory {
    event TestFactoryEvent(uint salt);
    function createAccount(uint salt) external returns (address) {
        TestUtils.emitEvmData("factory-validation");
        return address(new OpcodesTestAccount{salt: bytes32(salt)}());
    }
}
