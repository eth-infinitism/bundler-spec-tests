from dataclasses import asdict

import pytest
from eth_abi import decode

from tests.types import UserOperation
from tests.utils import (
    pack_user_op,
    to_prefixed_hex,
    to_number,
    deploy_wallet_contract,
    hex_concat,
    deploy_and_deposit,
)


global_ep = None


@pytest.fixture(scope="session", autouse=True)
def set_global_entrypoint(entrypoint_contract):
    global global_ep
    global_ep = entrypoint_contract


def resolve_revert(e):
    s = str(e)
    # "FailedOpWithRevert(uint256,string,bytes)"
    if "0x65c8fd4d" in s:
        ret = decode(["uint256", "string", "bytes"], bytes.fromhex(s[10:]))
        return ValueError(ret[1] + " data= " + ret[2].hex())
    # "FailedOp(uint256,string,bytes)"
    if "0x220266b6" in s:
        ret = decode(["uint256", "string"], bytes.fromhex(s[10:]))
        return ValueError(ret[1])
    return e


def userop_with_field(op, op_field, val, append=False):
    d = asdict(op)
    if append:
        val = hex_concat(d[op_field], val)
    d[op_field] = val
    return UserOperation(**d)


def call_userop_with_gas_field(op, op_field, val):
    op1 = userop_with_field(op, op_field, to_prefixed_hex(val))
    b = global_ep.address
    packed = pack_user_op(op1)
    try:
        global_ep.functions.handleOps((packed,), b).call()
    except Exception as e:
        return resolve_revert(e)


def find_min(op, op_field, low, high):
    e = call_userop_with_gas_field(op, op_field, high)
    if e:
        raise ValueError(f"high {high} should be high enough, but reverts with: {e}")

    e = call_userop_with_gas_field(op, op_field, low)
    if not e:
        raise ValueError(f"low {low} should be low enough, but does not revert")

    while low < high:
        #         print("low=", low, "high=", high, "diff=", high - low)
        mid = low + (high - low) // 2
        e = call_userop_with_gas_field(op, op_field, mid)
        if e is None:
            high = mid
        else:
            low = mid + 1
    return low


# modify userop field to test the affect on verificationGasLimit
# append to op_field data. op_field can be any dynamic value: factoryData, callData, signature, paymasterData
# (note that for "factoryData", the userop must have a valid factory)
def check_userop_size(op, op_field):
    min_vgl = 1e6
    max_vgl = 0

    for len in range(0, 20000, 5000):
        op1 = userop_with_field(op, op_field, "0x" + "00" * len, True)
        vgl = find_min(op1, "verificationGasLimit", 0, 200000)
        # print("check_userop_size field=", op_field, " len=", len, "vgl=", vgl)
        min_vgl = min(min_vgl, vgl)
        max_vgl = max(max_vgl, vgl)
    print("field=", op_field, "vgl range:", max_vgl, "..", min_vgl, max_vgl - min_vgl)
    return min_vgl, max_vgl


def test_gas1(w3, wallet_contract):

    # account deposits deployment gas, and thus skips the "deposit" phase
    wallet_contract = deploy_wallet_contract(w3)
    # fund(w3, wallet_contract.address)

    op = UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[123]),
        signature="0x",
    )

    print("verificationGasLimit", to_number(op.verificationGasLimit))
    vgl = find_min(op, "verificationGasLimit", 0, 100000)
    print("vgl=", vgl)

    assert vgl == 36550
    assert check_userop_size(op, "callData") == (36550, 44097)
    assert check_userop_size(op, "signature") == (36550, 39812)


def test_gas1_with_paymaster(w3, wallet_contract, entrypoint_contract):

    paymaster = deploy_and_deposit(
        w3, entrypoint_contract, "TestSimplePaymaster", deposit=5 * 10**18
    )
    op = UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[123]),
        paymaster=paymaster.address,
        signature="0x",
    )
    vgl = find_min(op, "verificationGasLimit", 0, 100000)
    print("vgl=", vgl)
    op.verificationGasLimit = vgl

    assert vgl == 31345
    pmvgl = find_min(op, "paymasterVerificationGasLimit", 0, 100000)
    print("pmvgl=", pmvgl)
    assert pmvgl == 11494

    # todo: calculate paymasterVerificationGasLimit
    assert check_userop_size(op, "callData") == (31345, 38895)
    assert check_userop_size(op, "signature") == (31345, 34610)
    assert check_userop_size(op, "paymasterData") == (
        31345,
        38912,
    )

    # assert_ok(op.debug_send())
    # send_bundle_now()
    # #
    # assert wallet_contract.functions.state().call() == 123
