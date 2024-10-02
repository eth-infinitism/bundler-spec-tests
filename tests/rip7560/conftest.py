import json
import os
import time

import pytest

from tests.rip7560.types import TransactionRIP7560
from tests.types import CommandLineArgs
from tests.utils import (
    deploy_contract,
    compile_contract,
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
        value=10**18,
    )
    return contract


@pytest.fixture
def factory_contract_7560(w3):
    contract = deploy_contract(
        w3,
        "rip7560/RIP7560Deployer",
        value=0 * 10**18,
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
        value=0 * 10**18,
    )
    time.sleep(0.1)
    w3.eth.send_transaction(
        {"from": w3.eth.default_account, "to": contract.address, "value": 10**18}
    )
    return contract


@pytest.fixture
def tx_7560(wallet_contract):
    return TransactionRIP7560(
        sender=wallet_contract.address,
        nonceKey=hex(0),
        nonce=hex(1),
        maxFeePerGas=hex(100000000000),
        maxPriorityFeePerGas=hex(100000000000),
        verificationGasLimit=hex(2000000),
        executionData=wallet_contract.encode_abi(
            abi_element_identifier="anyExecutionFunction"
        ),
        authorizationData="0xface",
    )


@pytest.fixture(scope="session")
def entry_point_rip7560(w3):
    entry_point_interface = compile_contract(
        "../../@rip7560/contracts/interfaces/IRip7560EntryPoint"
    )
    entry_point = w3.eth.contract(
        abi=entry_point_interface["abi"],
        address="0x0000000000000000000000000000000000007560",
    )
    return entry_point


@pytest.fixture(scope="session")
def nonce_manager(w3):
    artifact_path = "/../../@rip7560/artifacts/contracts/predeploys/NonceManager.sol/NonceManager.json"
    return contract_from_artifact(w3, artifact_path, CommandLineArgs.nonce_manager)


@pytest.fixture(scope="session")
def stake_manager(w3):
    artifact_path = "/../../@rip7560/artifacts/contracts/predeploys/Rip7560StakeManager.sol/Rip7560StakeManager.json"
    return contract_from_artifact(w3, artifact_path, CommandLineArgs.stake_manager)


def contract_from_artifact(w3, artifact_path, contract_address):
    current_dirname = os.path.dirname(__file__)
    artifact_realpath = os.path.realpath(current_dirname + artifact_path)
    code = w3.eth.get_code(contract_address)
    assert len(code) > 2, "contract not deployed: " + contract_address
    with open(artifact_realpath, encoding="utf-8") as file:
        json_file = json.load(file)
        return w3.eth.contract(abi=json_file["abi"], address=contract_address)
