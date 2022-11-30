// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;

import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "@account-abstraction/contracts/interfaces/IPaymaster.sol";

contract Dummy {
    uint public value = 1;

}

contract TestCoin {
    mapping(address => uint) balances;

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
}

contract TestRulesAccount is IAccount, IPaymaster {

    uint state;
    TestCoin public coin;

    event State(uint oldState, uint newState);

    constructor(address _ep) payable {
        if (_ep != address(0)) {
            (bool req,) = address(_ep).call{value : msg.value}("");
            require(req);
        }
        setCoin(new TestCoin());
    }

    function setState(uint _state) external {
        emit State(state, _state);
        state = _state;
    }

    function setCoin(TestCoin _coin) public returns (uint){
        coin = _coin;
        return 0;
    }

    function eq(string memory a, string memory b) internal returns (bool) {
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
        else if (eq(rule, "OTHERSLOAD")) return coin.balanceOf(address(1));
        else if (eq(rule, "OTHERSSTORE")) return coin.mint(address(1));
        else if (eq(rule, "SELFSSLOAD")) return uint160(address(coin));
        else if (eq(rule, "SELFSSTORE")) return setCoin(TestCoin(address(0xdead)));
        else if (eq(rule, "SELFREFSLOAD")) return coin.balanceOf(address(this));
        else if (eq(rule, "SELFREFSSTORE")) return coin.mint(address(this));

        else if (eq(rule, "inner-revert")) return coin.reverting();
        else if (eq(rule, "oog")) return coin.wasteGas();

        revert(string.concat("unknown rule: ", rule));
    }

    function validateUserOp(UserOperation calldata userOp, bytes32, address, uint256 missingAccountFunds)
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

contract TestRulesAccountDeployer {
    function create(string memory rule, TestCoin coin) public returns (TestRulesAccount) {
        TestRulesAccount a = new TestRulesAccount{salt : bytes32(uint(0))}(address(0));
        a.setCoin(coin);
        a.runRule(rule);
        return a;
    }

}
