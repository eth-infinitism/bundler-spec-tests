import pytest
from dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware
from solcx import install_solc
import subprocess

from .utils import deploy_wallet_contract
from .types import UserOperation, RPCRequest, CommandLineArgs

def pytest_configure(config):
    CommandLineArgs.configure(url=config.getoption('--url'),
                              entryPoint=config.getoption('--entry-point'),
                              ethereumNode=config.getoption('--ethereum-node'),
                              startupScript=config.getoption('--startup-script'))
    install_solc(version='0.8.15')


def pytest_sessionstart(session):
    startupscript = session.config.getoption('--startup-script')
    if startupscript is not None:
        subprocess.run([startupscript, 'start'], check=True, text=True)


def pytest_sessionfinish(session):
    startupscript = session.config.getoption('--startup-script')
    if startupscript is not None:
        subprocess.run([startupscript, 'stop'], check=True, text=True)


def pytest_addoption(parser):
    parser.addoption(
        '--url',
        action='store'
    )
    parser.addoption(
        '--entry-point',
        action='store'
    )
    parser.addoption(
        '--ethereum-node',
        action='store'
    )
    parser.addoption(
        '--startup-script',
        action='store'
    )


@pytest.fixture
def w3():
    w3 = Web3(Web3.HTTPProvider(CommandLineArgs.ethereumNode))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


@pytest.fixture(autouse=True)
def wallet_contract(w3):
    return deploy_wallet_contract(w3)



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
def sendUserOperation(userOp):
    return userOp.send()


# debug apis

@pytest.fixture
def sendBundleNow():
    return RPCRequest(method='aa_sendBundleNow').send()


@pytest.fixture
def clearState():
    return RPCRequest(method='aa_clearState').send()


@pytest.fixture
def setBundleInterval():
    return RPCRequest(method='aa_setBundleInterval', params=['manual']).send()


@pytest.fixture
def setReputation():
    return RPCRequest(method='aa_setReputation').send()


@pytest.fixture
def dumpReputation():
    return RPCRequest(method='aa_dumpReputation').send()
