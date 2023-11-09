// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

contract TestCoin {
    mapping(address => uint) balances;

    struct Struct {
        uint a;
        uint b;
        uint c;
    }
    mapping(address=>Struct) public structInfo;

    function setStructMember(address addr) public returns (uint){
        return structInfo[addr].c = 3;
    }

    function balanceOf(address addr) public returns (uint) {
        return balances[addr];
    }

    function mint(address addr) public returns (uint) {
        return balances[addr] += 100;
    }

    //unrelated to token: testing inner object revert
    function reverting() public returns (uint) {
        revert("inner-revert");
    }

    function wasteGas() public returns (uint) {
        string memory buffer = "string to be duplicated";
        while (true) {
            buffer = string.concat(buffer, buffer);
        }
        return 0;
    }

    function receiveValue() public payable returns (uint256) {
        require(msg.value > 0, "value is zero");
        return msg.value;
    }

    function destruct() public {
        selfdestruct(payable(msg.sender));
    }
}
