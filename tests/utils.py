import os

from solcx import compile_source
from .types import UserOperation


def compile_contract(contract):
    current_dirname = os.path.dirname(__file__)
    contracts_dirname = current_dirname + "/contracts/"
    aa_path = os.path.realpath(current_dirname + '/../@account-abstraction')
    aa_relpath = os.path.relpath(aa_path, contracts_dirname)
    remap = '@account-abstraction=' + aa_relpath
    # print('what is dirname', contracts_dirname, aa_path, remap, aa_relpath)
    test_source = open(contracts_dirname + contract + '.sol', "r").read()
    compiled_sol = compile_source(test_source, base_path=contracts_dirname, allow_paths=aa_relpath, import_remappings=remap, output_values=['abi', 'bin'], solc_version='0.8.15')
    return compiled_sol['<stdin>:' + contract]


def userOpHash(wallet_contract, userOp):
    payload = (
        userOp.sender,
        int(userOp.nonce, 16),
        userOp.initCode,
        userOp.callData,
        int(userOp.callGasLimit, 16),
        int(userOp.verificationGasLimit, 16),
        int(userOp.preVerificationGas, 16),
        int(userOp.maxFeePerGas, 16),
        int(userOp.maxPriorityFeePerGas, 16),
        userOp.paymasterAndData,
        userOp.signature
    )
    return '0x' + wallet_contract.functions.getUserOpHash(payload).call().hex()


def assertRpcError(response, message, code):
    assert response.code == code
    assert message in response.message


def assertFieldsTypes(obj, names=[], types=[]):
    for n, t in zip(names, types):
        assert isinstance(obj[n], t)


# def getUserOp(contract, overrides):
#     fn_name = overrides['callData'] and overrides['callData'][0]
#     args = []
#     if fn_name is None:
#         fn_name = 'setState'
#         args = [0]
#     elif len(overrides['callData']) > 1:
#         args = overrides['callData'][1]
#     op = UserOperation(
#     sender=contract.address,
#     signature='0xface',
#     callData=contract.encodeABI(fn_name=fn_name, args=args)
#     )
#     for k, v in overrides.items():
#         k != 'callData' and setattr(op, k, v)
#     return op
