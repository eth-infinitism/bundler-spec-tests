// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IAccount.sol";

contract TestCodeHashAccount is IAccount {
    uint public immutable num;

    constructor(address ep, TestCodeHashFactory factory) payable {
        (bool req,) = address(ep).call{value : msg.value}("");
        require(req);
        num = factory.num();
    }

    function destruct() public {
        selfdestruct(payable(msg.sender));
    }
    function validateUserOp(UserOperation calldata userOp, bytes32, uint256 missingWalletFunds)
    external override returns (uint256 deadline) {
        if (missingWalletFunds>0) {
            msg.sender.call{value:missingWalletFunds}("");
        }
//        require(num == userOp.nonce, "Reverting second simulation");
    }
}


contract TestCodeHashFactory {
    uint public num;
    event ContractCreated(address account);
    function destroy(TestCodeHashAccount account) public {
        account.destruct();
    }
    function getNums(TestCodeHashAccount account) public view returns (uint, uint) {
        return (num, account.num());
    }
    function create(uint nonce, uint _num, address entrypoint) public payable returns (TestCodeHashAccount) {
        num = _num;
        TestCodeHashAccount newAccount = new TestCodeHashAccount{salt : bytes32(nonce), value: msg.value}(entrypoint, this);
        emit ContractCreated(address(newAccount));
        return newAccount;
    }
}
