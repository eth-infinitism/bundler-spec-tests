import pytest
from dataclasses import dataclass
from web3 import Web3, IPCProvider
from web3.middleware import geth_poa_middleware
# from web3.auto.gethdev import w3
from solcx import install_solc, compile_source
import os

@pytest.fixture
def opban_contract(w3):
    print('opban_contract')


# def pytest_configure(config):
#     install_solc(version='latest')
#     print(os.getcwd())
#     test_source = open(os.getcwd()+"/tests/contracts/OpcodeTestContract.sol", "r").read()
#     compiled_sol = compile_source(test_source, output_values=['abi', 'bin'])
#     user_operation_lib_id, user_operation_lib_interface = compiled_sol.popitem()
#     test_deployer_id, test_deployer_interface = compiled_sol.popitem()
#     opcode_test_contract_id, opcode_test_contract_interface = compiled_sol.popitem()
#     dummy_id, dummy_interface = compiled_sol.popitem()
#     w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
#     w3.middleware_onion.inject(geth_poa_middleware, layer=0)
#     opcode_test_contract = w3.eth.contract(abi=opcode_test_contract_interface['abi'], bytecode=opcode_test_contract_interface['bin'])
#     print(w3.eth.accounts[0])
#     account = w3.eth.accounts[0]
#     tx_hash = opcode_test_contract.constructor(0).transact({'gas': 10000000, 'from': account})
#     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#     print('hash, receipt:', tx_hash.hex(), tx_receipt)
