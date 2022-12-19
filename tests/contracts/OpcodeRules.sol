// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.15;
import "./TestRulesAccount.sol";

library OpcodeRules {

    function eq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    //return by runRule if string is unknown.
    uint constant public UNKNOWN = type(uint).max;

    function runRule(string memory rule, TestCoin coin) internal returns (uint) {
//        return 0;
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
        else if (eq(rule, "CREATE")) return uint160(address(new Dummy()));
        else if (eq(rule, "CREATE2")) return uint160(address(new Dummy{salt : bytes32(uint(0x1))}()));
        else if (eq(rule, "OTHERSLOAD")) return coin.balanceOf(address(1));
        else if (eq(rule, "OTHERSSTORE")) return coin.mint(address(1));
        else if (eq(rule, "SELFSSLOAD")) {
            assembly {
                pop(sload(1000))
            }
            return 0;
        }
        else if (eq(rule, "SELFSSTORE")) {
            assembly {
                sstore(100000,1)
            }
            return 0;
        }
        else if (eq(rule, "acct-balance")) return coin.balanceOf(address(this));
        else if (eq(rule, "SELFREFSSTORE")) return coin.mint(address(this));
        else if (eq(rule, "inner-revert")) {
            revert("inner revert");
            return 0;
        }
        else if (eq(rule, "oog")) {
            while (true) {
                require(msg.sender != ecrecover("message", 27, bytes32(0), bytes32(0)));
            }
            return 0;
        }
        return UNKNOWN;
    }
}
