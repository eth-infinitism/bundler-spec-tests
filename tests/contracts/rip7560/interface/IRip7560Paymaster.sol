// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;

/**
 * @title IRip7560Paymaster
 * @dev Interface for the paymaster contract.
 */
interface IRip7560Paymaster {

	/**
	 * paymaster validation function.
	 * This method must call RIP7560Utils.paymasterAcceptTransaction to accept paying for the transaction.
	 * Any other return value (or revert) will be considered as a rejection of the transaction.
	 * @param version - transaction encoding version RIP7560Utils.VERSION
	 * @param txHash - transaction hash to check the signature against
	 * @param transaction - encoded transaction
	 */
	function validatePaymasterTransaction(
		uint256 version,
		bytes32 txHash,
		bytes calldata transaction)
	external;


	/**
	 * paymaster post transaction function.
	 * This method is called after the transaction has been executed - if the validation function returned a context
	 * @dev revert in this method will cause the account execution function to revert too
	 *	(but the reverted transaction will still get on-chain and be paid for)
	 * @param success - true if the transaction was successful, false otherwise
	 * @param actualGasCost - the actual gas cost of the transaction
	 * @param context - context data returned by validatePaymasterTransaction
	 */
	function postPaymasterTransaction(
		bool success,
		uint256 actualGasCost,
		bytes calldata context
	) external;

}
