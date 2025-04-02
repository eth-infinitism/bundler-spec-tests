import subprocess

import pytest
from eth_account import Account
from solcx import install_solc
from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder, ExtraDataToPOAMiddleware
from .types import RPCRequest, CommandLineArgs

from .user_operation_erc4337 import UserOperation

from .utils import (
    assert_ok,
    compile_contract,
    deploy_and_deposit,
    deploy_contract,
    deploy_wallet_contract,
    send_bundle_now,
    set_manual_bundling_mode,
)


def pytest_configure(config):
    CommandLineArgs.configure(
        url=config.getoption("--url"),
        entrypoint=config.getoption("--entry-point"),
        query_ep=config.getoption("--query-ep"),
        nonce_manager=config.getoption("--nonce-manager"),
        stake_manager=config.getoption("--stake-manager"),
        ethereum_node=config.getoption("--ethereum-node"),
        launcher_script=config.getoption("--launcher-script"),
        log_rpc=config.getoption("--log-rpc"),
    )
    install_solc(version="0.8.19")


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
    parser.addoption("--nonce-manager", action="store")
    parser.addoption("--stake-manager", action="store")
    parser.addoption("--ethereum-node", action="store")
    parser.addoption("--launcher-script", action="store")
    parser.addoption("--log-rpc", action="store_true", default=False)
    parser.addoption("--query-ep", action="store_true", default=False)


@pytest.fixture(scope="session")
def w3():
    w3 = Web3(Web3.HTTPProvider(CommandLineArgs.ethereum_node))
    private_key = "0x26e86e45f6fc45ec6e2ecd128cec80fa1d1505e5507dcd2ae58c3130a7a97b48"
    # pylint doesn't deal with @combomethod well
    # pylint: disable = no-value-for-parameter
    account = Account.from_key(private_key)
    w3.eth.default_account = account.address
    w3.middleware_onion.add(SignAndSendRawMiddlewareBuilder.build(private_key))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


# @pytest.fixture
# def wallet_contract(w3):
#     return deploy_wallet_contract(w3)


@pytest.fixture(scope="session")
def entrypoint_contract(w3):
    entrypoint_interface = compile_contract(
        "@account-abstraction/contracts/interfaces/IEntryPoint"
    )
    return w3.eth.contract(
        abi=entrypoint_interface["abi"], address=CommandLineArgs.entrypoint
    )


@pytest.fixture
def paymaster_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesPaymaster", False)


@pytest.fixture
def staked_paymaster_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesPaymaster", True)


@pytest.fixture
def factory_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesFactory", False)


@pytest.fixture
def staked_factory_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesFactory", True)


@pytest.fixture
def rules_account_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesAccount", False)


@pytest.fixture
def rules_staked_account_contract(w3, entrypoint_contract):
    return deploy_and_deposit(w3, entrypoint_contract, "TestRulesAccount", True)


@pytest.fixture(scope="session")
def helper_contract(w3):
    return deploy_contract(w3, "Helper")


@pytest.fixture
def userop(wallet_contract):
    return UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encode_abi(
            abi_element_identifier="setState", args=[1111111]
        ),
        signature="0xface",
    )


@pytest.fixture
def execute_user_operation(userop):
    userop.send()
    send_bundle_now()


# debug apis


# applied to all tests: clear mempool, reputation before each test
# @pytest.fixture(autouse=True)
# def clear_state_before_each_test():
#     assert_ok(RPCRequest(method="debug_bundler_clearState").send())


@pytest.fixture
def manual_bundling_mode():
    return set_manual_bundling_mode()


@pytest.fixture
def auto_bundling_mode():
    assert_ok(
        RPCRequest(method="debug_bundler_setBundlingMode", params=["auto"]).send()
    )


@pytest.fixture
def set_reputation(reputations):
    assert_ok(
        RPCRequest(
            method="debug_bundler_setReputation",
            params=[reputations, CommandLineArgs.entrypoint],
        ).send()
    )


@pytest.fixture
def impl7702(w3):
    return deploy_contract(w3, "SimpleWallet", ctrparams=[CommandLineArgs.entrypoint])
