import pytest
from dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware
from solcx import install_solc

from .utils import compile_contract, deploy_wallet_contract
from .types import UserOperation, RPCRequest


@dataclass()
class CommandLineArgs:
    url: str
    entry_point: str
    ethereum_node: str
    startup_script: str


def pytest_configure(config):
    install_solc(version='0.8.15')


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
    return deploy_wallet_contract(cmd_args, w3)



@pytest.fixture
def userOp(wallet_contract):
    return UserOperation(
        wallet_contract.address,
        hex(0),
        '0x',
        wallet_contract.encodeABI(fn_name='setState', args=[1111111]),
        hex(30000),
        hex(1213945),
        hex(47124),
        hex(2107373890),
        hex(1500000000),
        '0x',
        '0xface'
    )


@pytest.fixture
def sendUserOperation(cmd_args, userOp):
    return userOp.send(cmd_args)


# debug apis

@pytest.fixture
def sendBundleNow(cmd_args):
    return RPCRequest(method="aa_sendBundleNow").send(cmd_args.url)


@pytest.fixture
def clearState(cmd_args):
    print('clearing bundler state')
    return RPCRequest(method="aa_clearState").send(cmd_args.url)


@pytest.fixture
def setBundleInterval(cmd_args):
    return RPCRequest(method="aa_setBundleInterval", params=['manual']).send(cmd_args.url)

