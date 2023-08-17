// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "@account-abstraction/contracts/interfaces/IPaymaster.sol";
import "./Stakable.sol";

contract Dummy {
    uint public value = 1;

}

contract TestCoin {
    mapping(address => uint) balances;

    struct Struct {
        uint a;
        uint b;
        uint c;
    }
    mapping(address=>Struct) public structInfo;

    function getInfo(address addr) public returns (Struct memory) {
        return structInfo[addr];
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

contract TestRulesAccount is IAccount, IPaymaster, Stakable {

    uint public state;
    TestCoin public coin;
    IEntryPoint public entryPoint;

    event State(uint oldState, uint newState);

    constructor(address _ep) payable {
        entryPoint = IEntryPoint(_ep);
        if (_ep != address(0) && msg.value > 0) {
            (bool req,) = address(_ep).call{value : msg.value}("");
            require(req);
        }
        if ( _ep != address(0)) {
            setCoin(new TestCoin());
        }
    }

    receive() external payable {}

    function setState(uint _state) external {
        emit State(state, _state);
        state = _state;
    }

    function setCoin(TestCoin _coin) public returns (uint){
        coin = _coin;
        return 0;
    }

    function eq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function runRule(string memory rule) public returns (uint) {
        if (eq(rule, "")) return 0;
        else if (eq(rule, "GAS")) return gasleft();
        else if (eq(rule, "NUMBER")) return block.number;
        else if (eq(rule, "TIMESTAMP")) return block.timestamp;
        else if (eq(rule, "COINBASE")) return uint160(address(block.coinbase));
        else if (eq(rule, "DIFFICULTY")) return uint160(block.difficulty);
        else if (eq(rule, "BASEFEE")) return uint160(block.basefee);
        else if (eq(rule, "GASLIMIT")) return uint160(block.gaslimit);
        else if (eq(rule, "GASPRICE")) return uint160(tx.gasprice);
        else if (eq(rule, "SELFBALANCE")) return uint160(address(this).balance);
        else if (eq(rule, "BALANCE")) return uint160(address(msg.sender).balance);
        else if (eq(rule, "ORIGIN")) return uint160(address(tx.origin));
        else if (eq(rule, "BLOCKHASH")) return uint(blockhash(0));
        else if (eq(rule, "CREATE")) return new Dummy().value();
        else if (eq(rule, "CREATE2")) return new Dummy{salt : bytes32(uint(0x1))}().value();
        else if (eq(rule, "EXTCODESIZE")) return address(100500).code.length;
        else if (eq(rule, "EXTCODEHASH")) return uint256(address(100600).codehash);
        else if (eq(rule, "EXTCODECOPY")) {
            bytes memory o_code;
            assembly {
                // retrieve the size of the code, this needs assembly
                // let size := extcodesize(_addr)
                let size := 0
                // allocate output byte array - this could also be done without assembly
                // by using o_code = new bytes(size)
                o_code := mload(0x40)
                // new "memory end" including padding
                mstore(0x40, add(o_code, and(add(add(size, 0x20), 0x1f), not(0x1f))))
                // store length in memory
                mstore(o_code, size)
                // actually retrieve the code, this needs assembly
                extcodecopy(100700, add(o_code, 0x20), 0, size)
            }
            return o_code.length;
        }
        else if (eq(rule, "SELFDESTRUCT")) {
            coin.destruct();
            return 0;
        }

        else if (eq(rule, "no_storage")) return 0;
        else if (eq(rule, "account_storage")) return state;
        else if (eq(rule, "account_reference_storage")) return coin.balanceOf(address(this));
        else if (eq(rule, "account_reference_storage_struct")) return coin.getInfo(address(this)).c;
        else if (eq(rule, "account_reference_storage_init_code")) return coin.balanceOf(address(this));
        else if (eq(rule, "external_storage")) return coin.balanceOf(address(0xdeadcafe));
        else if (eq(rule, "entryPoint_call_balanceOf")) return entryPoint.balanceOf(address(this));
        else if (eq(rule, "eth_value_transfer_forbidden")) return coin.receiveValue{value: 666}();
        else if (eq(rule, "eth_value_transfer_entryPoint")) {
            payable(address(entryPoint)).call{value: 777}("");
            return 777;
        }
        else if (eq(rule, "eth_value_transfer_entryPoint_depositTo")) {
            entryPoint.depositTo{value: 888}(address(this));
            return 888;
        }


        revert(string.concat("unknown rule: ", rule));
    }

    function validateUserOp(UserOperation calldata userOp, bytes32, uint256 missingAccountFunds)
    external override returns (uint256 deadline) {
        if (missingAccountFunds > 0) {
            /* solhint-disable-next-line avoid-low-level-calls */
            (bool success,) = msg.sender.call{value : missingAccountFunds}("");
            success;
        }
        runRule(string(userOp.signature));
        return 0;
    }

    function validatePaymasterUserOp(UserOperation calldata userOp, bytes32 , uint256 )
    external returns (bytes memory context, uint256 deadline) {
        //first byte after paymaster address.
        runRule(string(userOp.paymasterAndData[20:]));
        return ("", 0);
    }

    function postOp(PostOpMode mode, bytes calldata context, uint256 actualGasCost) external {}
}
