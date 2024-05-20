import pytest
from tests.utils import (
    deploy_contract,
)

from tests.types import CommandLineArgs


@pytest.fixture
def wallet_contract(w3):
    return deploy_contract(
        w3,
        "rip7560/TestAccount",
        ctrparams=[CommandLineArgs.entrypoint],
        value=2 * 10**18,
    )
