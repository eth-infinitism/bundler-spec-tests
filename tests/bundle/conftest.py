import pytest
from tests.utils import deploy_contract


@pytest.fixture
def paymaster_contract(w3, entrypoint_contract):
    return deploy_contract(
        w3,
        "TestRulesPaymaster",
        value=2 * 10**18,
        ctrParams=[entrypoint_contract.address],
    )


@pytest.fixture
def factory_contract(w3, entrypoint_contract):
    return deploy_contract(
        w3,
        "TestRulesFactory",
        ctrParams=[entrypoint_contract.address],
    )


@pytest.fixture
def rules_account_contract(w3, entrypoint_contract):
    return deploy_contract(
        w3,
        "TestRulesAccount",
        ctrParams=[entrypoint_contract.address],
    )


@pytest.fixture(scope="session")
def helper_contract(w3, entrypoint_contract):
    return deploy_contract(w3, "Helper")


@pytest.fixture
def sender_from_initcode(w3, entrypoint_contract, helper_contract, initCode):
    return helper_contract.functions.getSenderAddress(
        entrypoint_contract.address, initCode
    ).call({"gas": 10000000})
