import pytest
from tests.types import CommandLineArgs
from tests.utils import deploy_contract


def deploy_and_deposit(w3, entrypoint_contract, contractName, staked):
    contract = deploy_contract(
        w3,
        contractName,
        ctrParams=[entrypoint_contract.address],
    )
    entrypoint_contract.functions.depositTo(contract.address).transact(
        {"value": 10**18, "from": w3.eth.accounts[0]}
    )
    if staked:
        return staked_contract(w3, entrypoint_contract, contract)
    return contract


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
def helper_contract(w3, entrypoint_contract):
    return deploy_contract(w3, "Helper")


def sender_from_initcode(entrypoint_contract, helper_contract, initCode):
    return helper_contract.functions.getSenderAddress(
        entrypoint_contract.address, initCode
    ).call({"gas": 10000000})


def staked_contract(w3, entrypoint_contract, contract):
    contract.functions.addStake(entrypoint_contract.address, 2).transact(
        {"from": w3.eth.accounts[0], "value": 1 * 10**18}
    )
    info = entrypoint_contract.functions.deposits(contract.address).call()
    assert info[1], "could not stake contract"
    return contract


def getSenderAddress(w3, initCode):
    helper = deploy_contract(w3, "Helper")
    return helper.functions.getSenderAddress(CommandLineArgs.entryPoint, initCode).call(
        {"gas": 10000000}
    )


def pytest_generate_tests(metafunc):
    print(
        "pytest_generate!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
        metafunc.function.__name__,
        metafunc.fixturenames,
    )
