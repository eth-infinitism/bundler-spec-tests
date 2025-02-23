// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

import "./Create2.sol";
import "./ITestAccount.sol";
import "./TestCoin.sol";
import "./TestRulesTarget.sol";
import "./ValidationRulesStorage.sol";

contract Dummy2 {}

contract Dummy {
    uint public immutable value = 1;

    function create() public returns (uint) {
        new Dummy2();
        return 0;
    }

    function create2() public returns (uint) {
        new Dummy2{salt: bytes32(uint(0x1))}();
        return 0;
    }
}


library ValidationRules {
    using ValidationRules for string;
    event Uint(uint);

    function eq(string memory a, string memory b) internal pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function startsWith(string memory str, string memory prefix) internal pure returns (bool) {
        bytes memory strBytes = bytes(str);
        bytes memory prefixBytes = bytes(prefix);
        if (prefixBytes.length > strBytes.length) {
            return false;
        }
        for (uint256 i = 0; i < prefixBytes.length; i++) {
            if (strBytes[i] != prefixBytes[i]) {
                return false;
            }
        }
        return true;
    }

    function slice(string memory str, uint256 start, uint256 length) internal pure returns (string memory) {
        bytes memory strBytes = bytes(str);
        require(start + length <= strBytes.length, "Out of bounds");
        bytes memory result = new bytes(length);
        for (uint256 i = 0; i < length; i++) {
            result[i] = strBytes[start + i];
        }
        return string(result);
    }

    function includes(string memory str, string memory substr) internal pure returns (bool) {
        bytes memory strBytes = bytes(str);
        bytes memory substrBytes = bytes(substr);
        if (substrBytes.length > strBytes.length) {
            return false;
        }
        for (uint256 i = 0; i <= strBytes.length - substrBytes.length; i++) {
            bool matchFound = true;
            for (uint256 j = 0; j < substrBytes.length; j++) {
                if (strBytes[i + j] != substrBytes[j]) {
                    matchFound = false;
                    break;
                }
            }
            if (matchFound) {
                return true;
            }
        }
        return false;
    }

    //return by runRule if string is unknown.
    uint constant public UNKNOWN = type(uint).max;

    error CustomError(string error, uint256 code);

    function runFactorySpecificRule(uint nonce, string memory rule, address _entryPoint, address create2address) internal {
        if (eq(rule, "EXTCODEx_CALLx_undeployed_sender")) {
            // CALL
            create2address.call("");
            // CALLCODE
            assembly {
                let res := callcode(5000, create2address, 0, 0, 0, 0, 0)
            }
            // DELEGATECALL
            create2address.delegatecall("");
            // STATICCALL
            create2address.staticcall("");
            // EXTCODESIZE
            emit Uint(create2address.code.length);
            // EXTCODEHASH
            emit Uint(uint256(create2address.codehash));
            // EXTCODECOPY
            assembly {
                extcodecopy(create2address, 0, 0, 2)
            }
        }
    }

    function runRule(
        string memory rule,
        IState account,
        address paymaster,
        address factory,
        TestCoin coin,
        ValidationRulesStorage self,
        TestRulesTarget target
    ) internal returns (uint) {
        if (eq(rule, "")) return 0;
        else if (eq(rule, "revert-msg")) {
            revert("on-chain revert message string");
        } else if (eq(rule, "revert-custom-msg")) {
            revert CustomError("on-chain custom error", 777);
        } else if (eq(rule, "revert-out-of-gas-msg")) {
            uint256 a = 0;
            while (true) {
                a++;
            }
        }
        else if (eq(rule, "GAS")) return gasleft();
        else if (eq(rule, "NUMBER")) return block.number;
        else if (eq(rule, "TIMESTAMP")) return block.timestamp;
        else if (eq(rule, "COINBASE")) return uint160(address(block.coinbase));
        else if (eq(rule, "DIFFICULTY")) return uint160(block.difficulty);
        else if (eq(rule, "BASEFEE")) return uint160(block.basefee);
        else if (eq(rule, "GASLIMIT")) return uint160(block.gaslimit);
        else if (eq(rule, "GASPRICE")) return uint160(tx.gasprice);
        else if (eq(rule, "BALANCE")) return uint160(address(msg.sender).balance);
        else if (eq(rule, "ORIGIN")) return uint160(address(tx.origin));
        else if (eq(rule, "BLOCKHASH")) return uint(blockhash(0));
        else if (eq(rule, "nested-CREATE")) return new Dummy().create();
        else if (eq(rule, "nested-CREATE2")) return new Dummy().create2();
        else if (eq(rule, "CREATE")) return new Dummy().value();
        else if (eq(rule, "CREATE2")) return new Dummy{salt : bytes32(uint(0x1))}().value();
        else if (eq(rule, "SELFDESTRUCT")) {
            coin.destruct();
            return 0;
        }
        else if (eq(rule, "BLOBHASH")) return uint(blobhash(0));
        else if (eq(rule, "BLOBBASEFEE")) return block.blobbasefee;
        else if (eq(rule, "CALL_undeployed_contract")) { address(100100).call(""); return 0; }
        else if (eq(rule, "CALL_undeployed_contract_allowed_precompile")) {
            for (uint160 i = 1; i < 10; i++){
                address(i).call{gas: 100000}("");
            }
            return 0;
        }
        else if (eq(rule, "SELFBALANCE")) {
            uint256 selfb;
            assembly {
                selfb := selfbalance()
            }
            return selfb;
        }
        else if (eq(rule, "CALLCODE_undeployed_contract")) {
            assembly {
                let res := callcode(5000, 100200, 0, 0, 0, 0, 0)
            }
            return 0;
        }
        else if (eq(rule, "DELEGATECALL_undeployed_contract")) { address(100300).delegatecall(""); return 0; }
        else if (eq(rule, "STATICCALL_undeployed_contract")) { address(100400).staticcall(""); return 0; }
        else if (eq(rule, "EXTCODESIZE_undeployed_contract")) return address(100500).code.length;
        else if (eq(rule, "EXTCODEHASH_undeployed_contract")) return uint256(address(100600).codehash);
        else if (eq(rule, "EXTCODECOPY_undeployed_contract")) {
            assembly {
                extcodecopy(100700, 0, 0, 2)
            }
            return 0;
        }
        else if (eq(rule, "EXTCODESIZE_entrypoint")) {
            address ep = address(self.entryPoint());
            uint len;
            assembly {
                len := extcodesize(ep)
            }
            return len;
        }
        else if (eq(rule, "EXTCODEHASH_entrypoint")) return uint256(address(self.entryPoint()).codehash);
        else if (eq(rule, "EXTCODECOPY_entrypoint")) {
            address ep = address(self.entryPoint());
            assembly {
                extcodecopy(ep, 0, 0, 2)
            }
            return 0;
        }
        else if (eq(rule, "GAS CALL")) {
            // 'GAS CALL' sequence is what solidity does anyway
            // this test makes it explicit so we know for sure nothing changes here
            address addr = address(coin);
            address acc = address(account);
            bytes4 sig = coin.balanceOf.selector;
            assembly {
                    let x := mload(0x40)
                    mstore(x, sig)
                    mstore(add(x, 0x04), acc)
                    let success := call(
                        gas(), // GAS opcode
                        addr,
                        0,
                        x,
                        0x44,
                        x,
                        0x20)
            }
            return 0;
        }
        else if (eq(rule, "GAS DELEGATECALL")) {
            address addr = address(coin);
            address acc = address(account);
            bytes4 sig = coin.balanceOf.selector;
            assembly {
                let x := mload(0x40)
                mstore(x, sig)
                mstore(add(x, 0x04), acc)
                let success := delegatecall(
                    gas(), // GAS opcode
                    addr,
                    x,
                    0x44,
                    x,
                    0x20)
            }
            return 0;
        }

        else if (eq(rule, "no_storage")) return 0;
        else if (eq(rule, "storage_read")) return self.state();
        else if (eq(rule, "storage_write")) return self.funSSTORE();
        else if (eq(rule, "account_storage")) return account.state();

        else if (eq(rule, "account_reference_storage")) return coin.balanceOf(address(account));
        else if (eq(rule, "account_reference_storage_struct")) return coin.setStructMember(address(account));
        else if (eq(rule, "account_reference_storage_init_code")) return coin.balanceOf(address(account));

        else if (eq(rule, "paymaster_reference_storage")) return coin.mint(paymaster);
        else if (eq(rule, "paymaster_reference_storage_struct")) return coin.setStructMember(paymaster);

        else if (eq(rule, "factory_reference_storage")) return coin.mint(factory);
        else if (eq(rule, "factory_reference_storage_struct")) return coin.setStructMember(factory);

        else if (eq(rule, "external_storage_read")) return coin.balanceOf(address(0xdeadcafe));
        else if (eq(rule, "external_storage_write")) return coin.mint(address(0xdeadcafe));

        else if (eq(rule, "transient_storage_tstore")) return self.funTSTORE();
        else if (eq(rule, "transient_storage_tload")) return self.funTLOAD();
        else if (eq(rule, "account_transient_storage")) return account.funTSTORE();

        else if (eq(rule, "entryPoint_call_balanceOf")) return self.entryPoint().balanceOf(address(account));
        else if (eq(rule, "eth_value_transfer_forbidden")) return coin.receiveValue{value: 666}();
        else if (eq(rule, "eth_value_transfer_entryPoint")) {
            payable(address(self.entryPoint())).call{value: 777}("");
            return 777;
        }

        else if (eq(rule, "eth_value_transfer_entryPoint_depositTo")) {
            self.entryPoint().depositTo{value: 888}(address(account));
            return 888;
        }
        else if (eq(rule, "out_of_gas")) {
            (bool success,) = address(this).call{gas:10000}(abi.encodeWithSelector(self.revertOOG.selector));
            require(!success, "reverting oog");
            return 0;
        }
        else if (eq(rule, "sstore_out_of_gas")) {
            (bool success,) = address(this).call{gas:2299}(abi.encodeWithSelector(self.revertOOGSSTORE.selector));
            require(!success, "reverting pseudo oog");
            return 0;
        }
        else if (startsWith(rule, "DELEGATECALL:>")) {
            string memory innerRule = rule.slice(14, bytes(rule).length - 14);
            bytes memory callData = abi.encodeCall(target.runRule, (innerRule, account, paymaster, factory, coin, self, TestRulesTarget(payable(0))));
            (bool success, bytes memory ret) = address(target).delegatecall(callData);
            require(success, string(abi.encodePacked("DELEGATECALL rule reverted", ret)));
            return 0;
        }
        else if (startsWith(rule, "CALL:>")) {
            string memory innerRule = rule.slice(6, bytes(rule).length - 6);
            target.runRule{value: msg.value}(innerRule, account, paymaster, factory, coin, self, TestRulesTarget(payable(0)));
            return 0;
        }
        revert(string.concat("unknown rule: ", rule));
    }
}
