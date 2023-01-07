import os

from solcx import compile_source
from .types import RPCRequest, UserOperation, CommandLineArgs


def compile_contract(contract):
    current_dirname = os.path.dirname(__file__)
    contracts_dirname = current_dirname + "/contracts/"
    aa_path = os.path.realpath(current_dirname + "/../@account-abstraction")
    aa_relpath = os.path.relpath(aa_path, contracts_dirname)
    remap = "@account-abstraction=" + aa_relpath
    with open(
        contracts_dirname + contract + ".sol", "r", encoding="utf-8"
    ) as contractfile:
        test_source = contractfile.read()
        compiled_sol = compile_source(
            test_source,
            base_path=contracts_dirname,
            allow_paths=aa_relpath,
            import_remappings=remap,
            output_values=["abi", "bin"],
            solc_version="0.8.15",
        )
        return compiled_sol["<stdin>:" + contract]


def deploy_contract(w3, contractname, ctrparams=None, value=0, gas=4 * 10**6):
    if ctrparams is None:
        ctrparams = []
    interface = compile_contract(contractname)
    contract = w3.eth.contract(abi=interface["abi"], bytecode=interface["bin"])
    account = w3.eth.accounts[0]
    tx_hash = contract.constructor(*ctrparams).transact(
        {"gas": gas, "from": account, "value": hex(value)}
    )
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # print('Deployed contract. hash, receipt:', tx_hash.hex(), tx_receipt)
    # print(tx_receipt.contractAddress)
    assert tx_receipt.status == 1, "deployment of " + contractname + " failed"
    return w3.eth.contract(abi=interface["abi"], address=tx_receipt.contractAddress)


def deploy_and_deposit(w3, entrypoint_contract, contractname, staked):
    contract = deploy_contract(
        w3,
        contractname,
        ctrparams=[entrypoint_contract.address],
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
        w3, "SimpleWallet", ctrparams=[CommandLineArgs.entrypoint], value=2 * 10**18
    )


def userop_hash(wallet_contract, userop):
    payload = (
        userop.sender,
        int(userop.nonce, 16),
        userop.initCode,
        userop.callData,
        int(userop.callGasLimit, 16),
        int(userop.verificationGasLimit, 16),
        int(userop.preVerificationGas, 16),
        int(userop.maxFeePerGas, 16),
        int(userop.maxPriorityFeePerGas, 16),
        userop.paymasterAndData,
        userop.signature,
    )
    return "0x" + wallet_contract.functions.getUserOpHash(payload).call().hex()


def assert_rpc_error(response, message, code):
    try:
        assert response.code == code
        assert message in response.message
    except AttributeError as exc:
        raise Exception(f"expected error object, got:\n{response}") from exc


def get_sender_address(w3, initcode):
    helper = deploy_contract(w3, "Helper")
    return helper.functions.getSenderAddress(CommandLineArgs.entrypoint, initcode).call(
        {"gas": 10000000}
    )


def deposit_to_undeployed_sender(w3, entrypoint_contract, initcode):
    sender = get_sender_address(w3, initcode)
    tx_hash = entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return sender


def send_bundle_now():
    return RPCRequest(method="debug_bundler_sendBundleNow").send()


def dump_mempool():
    mempool = (
        RPCRequest(
            method="debug_bundler_dumpMempool", params=[CommandLineArgs.entrypoint]
        )
        .send()
        .result
    )
    for i, entry in enumerate(mempool):
        mempool[i] = UserOperation(**entry)
    return mempool


def set_throttled(address):
    assert (
        RPCRequest(
            method="debug_bundler_setReputation",
            params=[
                {"address": address, "opsSeen": 1, "opsIncluded": 2},
                CommandLineArgs.entrypoint,
            ],
        )
        .send()
        .result
    )


def to_prefixed_hex(s):
    return "0x" + to_hex(s)


def to_hex(s):
    return s.encode().hex()
