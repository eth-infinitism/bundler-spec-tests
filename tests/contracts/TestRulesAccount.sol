// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.25;

import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";
import "./Stakable.sol";
import "./ITestAccount.sol";
import "./ValidationRules.sol";

contract TestRulesAccount is Stakable, ValidationRulesStorage, ITestAccount {

    using ValidationRules for string;

    TestCoin public coin;
    TestRulesTarget private immutable target = new TestRulesTarget();

    function setCoin(TestCoin _coin) public {
        coin = _coin;
    }

    constructor(address _ep) payable {
        entryPoint = IEntryPoint(_ep);
        if (_ep != address(0) && msg.value > 0) {
            (bool req,) = address(_ep).call{value : msg.value}("");
            require(req);
        }
        // true only when deploying through TestRulesAccountFactory, in which case the factory sets the coin
        if (msg.sender.code.length == 0) {
            coin = new TestCoin();
        }
    }

    receive() external payable {}

    function validateUserOp(PackedUserOperation calldata userOp, bytes32, uint256 missingAccountFunds)
    external override returns (uint256 deadline) {
        if (missingAccountFunds > 0) {
            /* solhint-disable-next-line avoid-low-level-calls */
            (bool success,) = msg.sender.call{value : missingAccountFunds}("");
            success;
        }
        string memory rule = string(userOp.signature);
        ValidationRules.runRule(rule, this, coin, this, target);
        return 0;
    }
}
