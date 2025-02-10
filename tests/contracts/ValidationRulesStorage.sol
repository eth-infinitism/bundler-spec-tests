// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./ITestAccount.sol";

contract ValidationRulesStorage is IState {
    IEntryPoint public entryPoint;
    uint256 public state;

    function funTSTORE() external override returns(uint256) {
        assembly {
            tstore(0, 1)
        }
        return 0;
    }

    function funSSTORE() external returns(uint256) {
        assembly {
            sstore(0, 1)
        }
        return 0;
    }


    function funTLOAD() external returns(uint256) {
        uint256 tval;
        assembly {
            tval := tload(0)
        }
        emit State(tval, tval);
        return tval;
    }

    event State(uint oldState, uint newState);

    function setState(uint _state) public {
        emit State(state, _state);
        state = _state;
    }

    function revertOOG() public {
        uint256 i = 0;
        while(true) {
            keccak256(abi.encode(i++));
        }
    }

    function revertOOGSSTORE() public {
        state += 1;
    }
}
