import pytest
from tests.types import CommandLineArgs
from tests.utils import compile_contract


@pytest.fixture(autouse=True)
def opban_contract(w3):
    opcode_test_contract_interface = compile_contract("TestRulesAccount")
    opcode_test_contract = w3.eth.contract(
        abi=opcode_test_contract_interface["abi"],
        bytecode=opcode_test_contract_interface["bin"],
    )
    account = w3.eth.accounts[0]
    tx_hash = opcode_test_contract.constructor(CommandLineArgs.entryPoint).transact(
        {"gas": 10000000, "from": account, "value": hex(2 * 10**18)}
    )
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return w3.eth.contract(
        abi=opcode_test_contract_interface["abi"], address=tx_receipt.contractAddress
    )
