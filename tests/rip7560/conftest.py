import pytest
from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    deploy_contract,
)

from tests.types import CommandLineArgs


@pytest.fixture
def wallet_contract(w3):
    return deploy_contract(
        w3,
        "rip7560/TestAccount",
        value=0 * 10**18,
    )


@pytest.fixture
def tx_7560(wallet_contract):
    return TransactionRIP7560(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="anyExecutionFunction"),
        signature="0xface",
    )
