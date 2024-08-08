// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

/**
 * @title IRip7560Account
 * @dev Interface for the account contract.
 */
interface IRip7560Account {
	/**
	 * account validation function.
	 * This method must call RIP7560Utils.accountAcceptTransaction to accept the transaction.
	 * Any other return value (or revert) will be considered as a rejection of the transaction.
	 * @param version - transaction encoding version RIP7560Utils.VERSION
	 * @param txHash - transaction hash to check the signature against
	 * @param transaction - encoded transaction
	 */
	function validateTransaction(
		uint256 version,
		bytes32 txHash,
		bytes calldata transaction
	) external;
}
