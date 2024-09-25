import os
import time
from functools import cache

from eth_utils import to_checksum_address
from eth_abi import decode
from eth_abi.packed import encode_packed
from solcx import compile_source

from .rip7560.types import TransactionRIP7560
from .types import RPCRequest, UserOperation, CommandLineArgs


@cache
def compile_contract(contract):
    contract_subdir = os.path.dirname(contract)
    contract_name = os.path.basename(contract)

    current_dirname = os.path.dirname(__file__)
    contracts_dirname = current_dirname + "/contracts/" + contract_subdir + "/"
    aa_path = os.path.realpath(current_dirname + "/../@account-abstraction")
    aa_relpath = os.path.relpath(aa_path, contracts_dirname)
    rip7560_path = os.path.realpath(current_dirname + "/../@rip7560")
    rip7560_relpath = os.path.relpath(rip7560_path, contracts_dirname)
    allow_paths = aa_relpath + "," + rip7560_relpath
    aa_remap = "@account-abstraction=" + aa_relpath
    rip7560_remap = "@rip7560=" + rip7560_relpath
    with open(
        contracts_dirname + contract_name + ".sol", "r", encoding="utf-8"
    ) as contractfile:
        test_source = contractfile.read()
        compiled_sol = compile_source(
            test_source,
            base_path=contracts_dirname,
            # pylint: disable=fixme
            # todo: only do it for 7560 folder
            include_path=os.path.abspath(os.path.join(contracts_dirname, os.pardir))
            + "/",
            allow_paths=allow_paths,
            import_remappings=[aa_remap, rip7560_remap],
            output_values=["abi", "bin"],
            solc_version="0.8.25",
            evm_version="cancun",
            via_ir=True,
        )
        return compiled_sol["<stdin>:" + contract_name]


# pylint: disable=too-many-arguments
def deploy_contract(
    w3,
    contractname,
    ctrparams=None,
    value=0,
    gas=10 * 10**6,
    gas_price=10**9,
    account=None,
):
    if ctrparams is None:
        ctrparams = []
    interface = compile_contract(contractname)
    contract = w3.eth.contract(
        abi=interface["abi"],
        bytecode=interface["bin"],
    )
    if account is None:
        account = w3.eth.default_account
    tx_hash = contract.constructor(*ctrparams).transact(
        {
            "gas": gas,
            "from": account,
            "value": hex(value),
            "maxFeePerGas": gas_price,
            "maxPriorityFeePerGas": gas_price,
        }
    )
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # print('Deployed contract. hash, receipt:', tx_hash.hex(), tx_receipt)
    # print(tx_receipt.contractAddress)
    assert tx_receipt.status == 1, (
        "deployment of " + contractname + " failed:" + str(tx_receipt)
    )
    return w3.eth.contract(abi=interface["abi"], address=tx_receipt.contractAddress)


def deploy_and_deposit(
    w3, entrypoint_contract, contractname, staked=False, deposit=10**18
):
    contract = deploy_contract(
        w3,
        contractname,
        ctrparams=[entrypoint_contract.address],
    )
    if deposit is not None and deposit > 0:
        fund(w3, contract.address, deposit)
    if staked:
        return staked_contract(w3, entrypoint_contract, contract)
    return contract


def fund(w3, addr, value=10**18):
    tx_hash = w3.eth.send_transaction(
        {"from": w3.eth.default_account, "to": addr, "value": value}
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)


def staked_contract(w3, entrypoint_contract, contract):
    tx_hash = contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.default_account, "value": 1 * 10**18}
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


def deploy_state_contract(w3):
    return deploy_contract(w3, "State")


def pack_factory(factory, factory_data):
    if factory is None:
        return "0x"
    return to_prefixed_hex(factory) + to_hex(factory_data)


def pack_uints(high128, low128):
    return ((int(str(high128), 16) << 128) + int(str(low128), 16)).to_bytes(32, "big")


def pack_paymaster(
    paymaster,
    paymaster_verification_gas_limit,
    paymaster_post_op_gas_limit,
    paymaster_data,
):
    if paymaster is None:
        return "0x"
    if paymaster_data is None:
        paymaster_data = ""
    return encode_packed(
        ["address", "uint256", "string"],
        [
            paymaster,
            pack_uints(paymaster_verification_gas_limit, paymaster_post_op_gas_limit),
            paymaster_data,
        ],
    )


def userop_hash(helper_contract, userop):
    payload = (
        userop.sender,
        int(userop.nonce, 16),
        pack_factory(userop.factory, userop.factoryData),
        userop.callData,
        pack_uints(userop.verificationGasLimit, userop.callGasLimit),
        int(userop.preVerificationGas, 16),
        pack_uints(userop.maxPriorityFeePerGas, userop.maxFeePerGas),
        pack_paymaster(
            userop.paymaster,
            userop.paymasterVerificationGasLimit,
            userop.paymasterPostOpGasLimit,
            userop.paymasterData,
        ),
        userop.signature,
    )
    return (
        "0x"
        + helper_contract.functions.getUserOpHash(CommandLineArgs.entrypoint, payload)
        .call()
        .hex()
    )


def assert_ok(response):
    try:
        assert response.result
    except AttributeError as exc:
        raise AttributeError(f"expected result object, got:\n{response}") from exc


def assert_rpc_error(response, message, code, data=None):
    try:
        assert response.code == code
        assert message.lower() in response.message.lower()
        if data is not None:
            assert response.data == data
    except AttributeError as exc:
        raise AttributeError(f"expected error object, got:\n{response}") from exc


def get_sender_address(w3, factory, factory_data):
    ret = w3.eth.call({"to": factory, "data": factory_data})
    # pylint: disable=unsubscriptable-object
    return to_checksum_address(decode(["address"], ret)[0])


def deposit_to_undeployed_sender(w3, entrypoint_contract, factory, factory_data):
    sender = get_sender_address(w3, factory, factory_data)
    tx_hash = entrypoint_contract.functions.depositTo(sender).transact(
        {"value": 10**18, "from": w3.eth.default_account}
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return sender


def send_bundle_now(url=None):
    assert_ok(RPCRequest(method="debug_bundler_sendBundleNow").send(url))


def set_manual_bundling_mode(url=None):
    assert_ok(
        RPCRequest(method="debug_bundler_setBundlingMode", params=["manual"]).send(url)
    )


def get_rip7560_debug_info(tx_hash, url=None):
    return RPCRequest(
        method="eth_getRip7560TransactionDebugInfo", params=[tx_hash]
    ).send(url)


def dump_mempool(url=None):
    mempool = (
        RPCRequest(
            method="debug_bundler_dumpMempool", params=[CommandLineArgs.entrypoint]
        )
        .send(url)
        .result
    )
    for i, entry in enumerate(mempool):
        if "executionData" in entry:
            mempool[i] = TransactionRIP7560(**entry)
        else:
            mempool[i] = UserOperation(**entry)
    return mempool


# wait for mempool propagation.
# ref_dump - a "dump_mempool" taken from that bundler before the tested operation.
# wait for the `dump_mempool(url)` to change before returning it.
def p2p_mempool(ref_dump, url=None, timeout=5):
    count = timeout * 2
    while True:
        new_dump = dump_mempool(url)
        if ref_dump != new_dump:
            return new_dump
        count = count - 1
        if count <= 0:
            raise TimeoutError(f"timed-out waiting mempool change propagate to {url}")
        time.sleep(0.5)


def clear_mempool(url=None):
    return RPCRequest(method="debug_bundler_clearMempool").send(url)


def get_stake_status(address, entry_point):
    return (
        RPCRequest(method="debug_bundler_getStakeStatus", params=[address, entry_point])
        .send()
        .result
    )


def dump_reputation(url=None):
    return (
        RPCRequest(
            method="debug_bundler_dumpReputation", params=[CommandLineArgs.entrypoint]
        )
        .send(url)
        .result
    )


def clear_reputation(url=None):
    assert_ok(RPCRequest(method="debug_bundler_clearReputation").send(url))


def set_reputation(address, ops_seen=1, ops_included=2, url=None):
    res = RPCRequest(
        method="debug_bundler_setReputation",
        params=[
            [
                {
                    "address": address,
                    "opsSeen": hex(ops_seen),
                    "opsIncluded": hex(ops_included),
                }
            ],
            CommandLineArgs.entrypoint,
        ],
    ).send(url)

    assert res.result


def to_prefixed_hex(s):
    return "0x" + to_hex(s)


def to_hex(s):
    return s.encode().hex()


def to_number(num_or_hex):
    return num_or_hex if isinstance(num_or_hex, (int, float)) else int(num_or_hex, 16)


def sum_hex(*args):
    return sum(to_number(i) for i in args if i is not None)


def get_userop_max_cost(user_op):
    return sum_hex(
        user_op.preVerificationGas,
        user_op.verificationGasLimit,
        user_op.callGasLimit,
        user_op.paymasterVerificationGasLimit,
        user_op.paymasterPostOpGasLimit,
    ) * to_number(user_op.maxFeePerGas)


def get_rip7560_tx_max_cost(tx):
    tx_max_gas_limit = sum_hex(
        15000,
        tx.verificationGasLimit,
        tx.callGasLimit,
        tx.paymasterVerificationGasLimit,
        tx.paymasterPostOpGasLimit,
    )
    max_cost = tx_max_gas_limit * to_number(tx.maxFeePerGas)
    print(
        "get_rip7560_tx_max_cost",
        tx_max_gas_limit,
        to_number(tx.maxFeePerGas),
        max_cost,
    )
    return max_cost
