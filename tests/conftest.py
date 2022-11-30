import pytest
from dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware
from solcx import install_solc

from .utils import compile_contract


@dataclass()
class CommandLineArgs:
    url: str
    entry_point: str
    ethereum_node: str
    startup_script: str


def pytest_addoption(parser):
    parser.addoption(
        "--url",
        action="store"
    )
    parser.addoption(
        "--entry-point",
        action="store"
    )
    parser.addoption(
        "--ethereum-node",
        action="store"
    )
    parser.addoption(
        "--startup-script",
        action="store"
    )


@pytest.fixture
def cmd_args(request):
    return CommandLineArgs(
        url=request.config.getoption("--url"),
        entry_point=request.config.getoption("--entry-point"),
        ethereum_node=request.config.getoption("--ethereum-node"),
        startup_script=request.config.getoption("--startup-script")
    )


@pytest.fixture
def w3(cmd_args):
    w3 = Web3(Web3.HTTPProvider(cmd_args.ethereum_node))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


@pytest.fixture(autouse=True)
def wallet_contract(cmd_args, w3):
    wallet_interface = compile_contract('SimpleWallet')
    wallet = w3.eth.contract(abi=wallet_interface['abi'], bytecode=wallet_interface['bin'])
    account = w3.eth.accounts[0]
    tx_hash = wallet.constructor(cmd_args.entry_point).transact({'gas': 10000000, 'from': account, 'value': hex(2*10**18)})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # print('Deployed wallet contract. hash, receipt:', tx_hash.hex(), tx_receipt)
    # print(tx_receipt.contractAddress)
    return w3.eth.contract(abi=wallet_interface['abi'], address=tx_receipt.contractAddress)


def pytest_configure(config):
    install_solc(version='0.8.15')
