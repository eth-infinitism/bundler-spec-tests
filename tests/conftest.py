import json
import os
import subprocess

import pytest
from solcx import install_solc
from web3 import Web3
from web3.middleware import geth_poa_middleware
from .types import UserOperation, RPCRequest, CommandLineArgs
from .utils import deploy_wallet_contract, deploy_and_deposit, deploy_contract


def pytest_configure(config):
    CommandLineArgs.configure(
        url=config.getoption("--url"),
        entryPoint=config.getoption("--entry-point"),
        ethereumNode=config.getoption("--ethereum-node"),
        launcherScript=config.getoption("--launcher-script"),
    )
    install_solc(version="0.8.15")


def pytest_sessionstart():
    if CommandLineArgs.launcherScript is not None:
        subprocess.run([CommandLineArgs.launcherScript, "start"], check=True, text=True)


def pytest_sessionfinish():
    if CommandLineArgs.launcherScript is not None:
        subprocess.run([CommandLineArgs.launcherScript, "stop"], check=True, text=True)


def pytest_addoption(parser):
    parser.addoption("--url", action="store")
    parser.addoption("--entry-point", action="store")
    parser.addoption("--ethereum-node", action="store")
    parser.addoption("--launcher-script", action="store")


@pytest.fixture(scope="session")
def w3():
    w3 = Web3(Web3.HTTPProvider(CommandLineArgs.ethereumNode))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


@pytest.fixture(autouse=True)
def wallet_contract(w3):
    return deploy_wallet_contract(w3)


@pytest.fixture(scope="session")
def entrypoint_contract(w3):
    current_dirname = os.path.dirname(__file__)
    entrypoint_path = os.path.realpath(
        current_dirname
        + "/../@account-abstraction/artifacts/contracts/core/EntryPoint.sol/EntryPoint.json"
    )
    with open(entrypoint_path, encoding="utf-8") as file:
        entrypoint = json.load(file)
        return w3.eth.contract(
            abi=entrypoint["abi"], address=CommandLineArgs.entryPoint
        )


@pytest.fixture
def paymaster_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesPaymaster", False)


@pytest.fixture
def factory_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesFactory", False)


@pytest.fixture
def rules_account_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesAccount", False)


@pytest.fixture(scope="session")
def helper_contract(w3):
    return deploy_contract(w3, "Helper")


@pytest.fixture
def userOp(wallet_contract):
    return UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[1111111]),
        signature="0xface",
    )


@pytest.fixture
def sendUserOperation(userOp):
    return userOp.send()


# debug apis


@pytest.fixture
def sendBundleNow():
    return RPCRequest(method="debug_bundler_sendBundleNow").send()


@pytest.fixture
def clearState():
    return RPCRequest(method="debug_bundler_clearState").send()


@pytest.fixture
def setBundlingMode(mode):
    response = RPCRequest(method="debug_bundler_setBundlingMode", params=[mode]).send()
    return response


@pytest.fixture
def setReputation(reputations):
    return RPCRequest(
        method="debug_bundler_setReputation",
        params=[reputations, CommandLineArgs.entryPoint],
    ).send()


@pytest.fixture
def dumpReputation():
    return RPCRequest(
        method="debug_bundler_dumpReputation", params=[CommandLineArgs.entryPoint]
    ).send()
