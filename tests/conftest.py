import json
import os
import subprocess

import pytest
from solcx import install_solc
from web3 import Web3
from web3.middleware import geth_poa_middleware
from .types import UserOperation, RPCRequest, CommandLineArgs
from .utils import (
    deploy_wallet_contract,
    deploy_and_deposit,
    deploy_contract,
    send_bundle_now,
)


def pytest_configure(config):
    CommandLineArgs.configure(
        url=config.getoption("--url"),
        entrypoint=config.getoption("--entry-point"),
        ethereum_node=config.getoption("--ethereum-node"),
        launcher_script=config.getoption("--launcher-script"),
        log_rpc=config.getoption("--log-rpc")
    )
    install_solc(version="0.8.15")


def pytest_sessionstart():
    if CommandLineArgs.launcher_script is not None:
        subprocess.run(
            [CommandLineArgs.launcher_script, "start"], check=True, text=True
        )


def pytest_sessionfinish():
    if CommandLineArgs.launcher_script is not None:
        subprocess.run([CommandLineArgs.launcher_script, "stop"], check=True, text=True)


def pytest_addoption(parser):
    parser.addoption("--url", action="store")
    parser.addoption("--entry-point", action="store")
    parser.addoption("--ethereum-node", action="store")
    parser.addoption("--launcher-script", action="store")
    parser.addoption("--log-rpc", action="store_true", default=False)


@pytest.fixture(scope="session")
def w3():
    w3 = Web3(Web3.HTTPProvider(CommandLineArgs.ethereum_node))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


@pytest.fixture
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
            abi=entrypoint["abi"], address=CommandLineArgs.entrypoint
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
def userop(wallet_contract):
    return UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[1111111]),
        signature="0xface",
    )


@pytest.fixture
def execute_user_operation(userop):
    userop.send()
    send_bundle_now()


# debug apis


@pytest.fixture
def clear_state():
    return RPCRequest(method="debug_bundler_clearState").send()


@pytest.fixture
def set_bundling_mode(mode):
    response = RPCRequest(method="debug_bundler_setBundlingMode", params=[mode]).send()
    return response


@pytest.fixture
def set_reputation(reputations):
    return RPCRequest(
        method="debug_bundler_setReputation",
        params=[reputations, CommandLineArgs.entrypoint],
    ).send()


@pytest.fixture
def dump_reputation():
    return RPCRequest(
        method="debug_bundler_dumpReputation", params=[CommandLineArgs.entrypoint]
    ).send()
