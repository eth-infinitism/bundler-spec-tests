import os

from solcx import compile_source
from .types import RPCRequest, UserOperation, CommandLineArgs


def compile_contract(contract):
    current_dirname = os.path.dirname(__file__)
    contracts_dirname = current_dirname + "/contracts/"
    aa_path = os.path.realpath(current_dirname + "/../@account-abstraction")
    aa_relpath = os.path.relpath(aa_path, contracts_dirname)
    remap = "@account-abstraction=" + aa_relpath
    with open(contracts_dirname + contract + ".sol", "r", encoding="utf-8") as f:
        test_source = f.read()
        compiled_sol = compile_source(
            test_source,
            base_path=contracts_dirname,
            allow_paths=aa_relpath,
            import_remappings=remap,
            output_values=["abi", "bin"],
            solc_version="0.8.15",
        )
        return compiled_sol["<stdin>:" + contract]


def deploy_contract(w3, contractName, ctrParams=None, value=0, gas=4 * 10**6):
    if ctrParams is None:
        ctrParams = []
    interface = compile_contract(contractName)
    contract = w3.eth.contract(abi=interface["abi"], bytecode=interface["bin"])
    account = w3.eth.accounts[0]
    tx_hash = contract.constructor(*ctrParams).transact(
        {"gas": gas, "from": account, "value": hex(value)}
    )
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # print('Deployed contract. hash, receipt:', tx_hash.hex(), tx_receipt)
    # print(tx_receipt.contractAddress)
    assert tx_receipt.status == 1, "deployment of " + contractName + " failed"
    return w3.eth.contract(abi=interface["abi"], address=tx_receipt.contractAddress)


def deploy_and_deposit(w3, entrypoint_contract, contractName, staked):
    contract = deploy_contract(
        w3,
        contractName,
        ctrParams=[entrypoint_contract.address],
    )
    tx_hash = entrypoint_contract.functions.depositTo(contract.address).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)
    if staked:
        return staked_contract(w3, entrypoint_contract, contract)
    return contract


def staked_contract(w3, entrypoint_contract, contract):
    tx_hash = contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.accounts[0], "value": 1 * 10**18}
    )
    assert int(tx_hash.hex(), 16), "could not stake contract"
    w3.eth.wait_for_transaction_receipt(tx_hash)
    info = entrypoint_contract.functions.deposits(contract.address).call()
    assert info[1], "could not get deposit information"
    return contract


def deploy_wallet_contract(w3):
    return deploy_contract(
        w3, "SimpleWallet", ctrParams=[CommandLineArgs.entryPoint], value=2 * 10**18
    )


def userOpHash(wallet_contract, userOp):
    payload = (
        userOp.sender,
        int(userOp.nonce, 16),
        userOp.initCode,
        userOp.callData,
        int(userOp.callGasLimit, 16),
        int(userOp.verificationGasLimit, 16),
        int(userOp.preVerificationGas, 16),
        int(userOp.maxFeePerGas, 16),
        int(userOp.maxPriorityFeePerGas, 16),
        userOp.paymasterAndData,
        userOp.signature,
    )
    return "0x" + wallet_contract.functions.getUserOpHash(payload).call().hex()


def assertRpcError(response, message, code):
    try:
        assert response.code == code
        assert message in response.message
    except AttributeError as exc:
        raise Exception(f"expected error object, got:\n{response}") from exc


def getSenderAddress(w3, initCode):
    helper = deploy_contract(w3, "Helper")
    return helper.functions.getSenderAddress(CommandLineArgs.entryPoint, initCode).call(
        {"gas": 10000000}
    )


def sendBundleNow():
    return RPCRequest(method="debug_bundler_sendBundleNow").send()


def dumpMempool():
    mempool = (
        RPCRequest(
            method="debug_bundler_dumpMempool", params=[CommandLineArgs.entryPoint]
        )
        .send()
        .result
    )
    for i, entry in enumerate(mempool):
        mempool[i] = UserOperation(**entry)
    return mempool


def setThrottled(address):
    assert (
        RPCRequest(
            method="debug_bundler_setReputation",
            params=[
                {"address": address, "opsSeen": 1, "opsIncluded": 2},
                CommandLineArgs.entryPoint,
            ],
        )
        .send()
        .result
    )
