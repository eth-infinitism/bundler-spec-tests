import time
import pytest

from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    deploy_contract,
)


@pytest.fixture
def wallet_contract(w3):
    contract = deploy_contract(
        w3,
        "rip7560/TestAccount",
        value=10**18,
    )
    return contract


@pytest.fixture
def paymaster_contract_7560(w3):
    contract = deploy_contract(
        w3,
        "rip7560/RIP7560Paymaster",
        value=10 ** 18,
    )
    return contract


@pytest.fixture
def factory_contract_7560(w3):
    contract = deploy_contract(
        w3,
        "rip7560/RIP7560Deployer",
        value=0 * 10 ** 18,
    )
    time.sleep(0.1)
    return contract


# pylint: disable=fixme
# TODO: deduplicate
@pytest.fixture
def wallet_contract_rules(w3):
    contract = deploy_contract(
        w3,
        "rip7560/RIP7560TestRulesAccount",
        value=0 * 10 ** 18,
    )
    time.sleep(0.1)
    w3.eth.send_transaction(
        {"from": w3.eth.accounts[0], "to": contract.address, "value": 10 ** 18}
    )
    return contract


@pytest.fixture
def tx_7560(wallet_contract):
    return TransactionRIP7560(
        sender=wallet_contract.address,
        nonce=hex(1),
        maxFeePerGas=hex(100000000000),
        maxPriorityFeePerGas=hex(100000000000),
        verificationGasLimit=hex(2000000),
        callData=wallet_contract.encodeABI(fn_name="anyExecutionFunction"),
        signature="0xface",
    )
