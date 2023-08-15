// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

import "@account-abstraction/contracts/interfaces/IAccount.sol";
import "@account-abstraction/contracts/interfaces/IEntryPoint.sol";

/// @dev A test contract that represents a potential attack where a wallet entity is also
/// used as an associated storage by a different UserOperation.
/// This allows this couple of UserOperations to escape the sandbox and invalidate a bundle.
contract TestFakeWalletToken is IAccount {

    mapping(address => uint256) private balances;
    TestFakeWalletToken public anotherWallet;
    IEntryPoint ep;

    constructor(address _ep) payable {
        ep = IEntryPoint(_ep);
    }

    function balanceOf(address _owner) public view returns (uint256 balance) {
        return balances[_owner];
    }

    function sudoSetBalance(address _owner, uint256 balance) public {
        balances[_owner] = balance;
    }

    function sudoSetAnotherWallet(TestFakeWalletToken _anotherWallet) public {
        anotherWallet = _anotherWallet;
    }

    function validateUserOp(UserOperation calldata userOp, bytes32, uint256 missingWalletFunds)
    public override returns (uint256 validationData) {
        if (missingWalletFunds>0) {
            msg.sender.call{value:missingWalletFunds}("");
        }
        if (userOp.callData.length == 20) {
            // the first UserOperation sets the second sender's "associated" balance to 0
            address senderToDrain = address(bytes20(userOp.callData[:20]));
            balances[senderToDrain] = 0;
        } else {
            // the second UserOperation will hit this only if included in a bundle with the first one
            require(anotherWallet.balanceOf(address(this)) > 0, "no balance");
        }
        return 0;
    }

    receive() external payable {
    }

    fallback() external {

    }
}
