import pytest
from tests.types import CommandLineArgs
from tests.utils import deploy_contract


@pytest.fixture
def paymaster_contract(w3, entrypoint_contract):
    return deploy_contract(
        w3,
        "TestRulePaymaster",
        value=2 * 10**18,
        ctrParams=[entrypoint_contract.address],
    )
