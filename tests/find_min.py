from dataclasses import asdict

import pytest
from eth_abi import decode

from tests.user_operation_erc4337 import UserOperation
from tests.utils import (
    pack_user_op,
    to_prefixed_hex,
    hex_concat
)

_global_ep = None


@pytest.fixture(scope="session", autouse=True)
def set_global_entrypoint(entrypoint_contract):
    global _global_ep
    _global_ep = entrypoint_contract


def global_entrypoint():
    global _global_ep
    assert _global_ep is not None, "global_entrypoint() called before set_global_entrypoint()"
    return _global_ep

def resolve_revert(e):
    s = str(e)
    # "FailedOpWithRevert(uint256,string,bytes)"
    if "0x65c8fd4d" in s:
        ret = decode(["uint256", "string", "bytes"], bytes.fromhex(e.data[10:]))
        return ValueError(ret[1] + " data= " + ret[2].hex())
    # "FailedOp(uint256,string)"
    if "0x220266b6" in s:
        ret = decode(["uint256", "string"], bytes.fromhex(e.data[10:]))
        return ValueError(ret[1])
    return e


def userop_with_field(op, op_field, val, append=False):
    d = asdict(op)
    if append:
        val = hex_concat(d[op_field], val)
    d[op_field] = val
    return UserOperation(**d)


# submit userop with given field.
# return exception (with error message), or None if success
# This method works directly with entrypoint, bypassing the bundler.
def call_userop_with_gas_field(op, op_field, val, prefix_user_op=None):
    """
    Call userop with given field.
    :param op: userop to check
    :param op_field: field to change
    :param val: new value for op_field
    :param prefix_user_op: if not None, place that UserOp before the actual tested UserOp
            note that prefix_user_op should not revert.
    :return: None if success, or exception (with error message) on failure
    """
    op1 = userop_with_field(op, op_field, to_prefixed_hex(val))
    b = global_entrypoint()
    packedArray = []
    if prefix_user_op:
        packedArray.append(pack_user_op(prefix_user_op))

        # (address,uint256,bytes,bytes,bytes32,uint256,bytes32,bytes,bytes)
        # op='0xCE94FEaFfE47a210De8BfB12409d3d617754e125', '0x1', '0x', '0x3b6a02f6', '0x00000000000000000000000000030d40000000000000000000000000000f4240', '0x61a80', '0x000000000000000000000000b2d05e00000000000000000000000000ee6b2800', '0x', '0x'

    packedArray.append(pack_user_op(op1))
    try:
        global_entrypoint().functions.handleOps(packedArray, b.address).call({"gas": 10 ** 7})
    except Exception as e:
        return resolve_revert(e)


def find_min_func(func, low, high):
    """
    Find the minimum value that reverts with the given function.
    :param func: function to call, with current value as argument. Returns None if success
    :param low: minimum value. function should fail with this value
    :param high: maximum value. function should succeed with this value
    :return: minimum value that succeeds
    """
    e = func(high)
    if e:
        raise ValueError(f"high {high} should be high enough, but reverts with: {e}")

    e = func(low)
    if not e:
        raise ValueError(f"low {low} should be low enough, but does not revert")

    while low < high:
        mid = low + (high - low) // 2
        e = func(mid)
        if e is None:
            high = mid
        else:
            low = mid + 1
    return low

def find_min_userop_with_field(op, op_field, low, high, prefix_user_op=None):
    return find_min_func(lambda val: call_userop_with_gas_field(op, op_field, val, prefix_user_op), low, high)

# def waste_context_userop():
#     """
#     ceate a userOp that "wastes" memory, by using a paymaster that return a large context.
#     :return:
#     """
#     return UserOperation(
#         sender: dummy_account(),
#         data="0x",
#         value=0,
#         paymaster: dummy_context_paymaster(),
#         paymasterData="0x",
#         paymasterVerificationGasLimit=100_000,
#         verificationGasLimit=100_000,
#     )

def find_verification_limits(op, prefix_user_op=None):
    """
    find minimum verificationGasLimit, paymasterVerificationGasLimit for this userop.
    :param op:
    :param prefix_user_op:
    :return:
    """
    has_paymaster = op.paymaster is not None
    if has_paymaster:
        op = userop_with_field(op, "paymasterVerificationGasLimit", 100_000)
    vgl = find_min_userop_with_field(op, "verificationGasLimit", 0, 10 ** 6, prefix_user_op)
    if has_paymaster:
        op = userop_with_field(op, "verificationGasLimit", vgl)
        pmvgl = find_min_userop_with_field(op, "paymasterVerificationGasLimit", 0, 10 ** 6, prefix_user_op)
    else:
        pmvgl = None

    return vgl, pmvgl
