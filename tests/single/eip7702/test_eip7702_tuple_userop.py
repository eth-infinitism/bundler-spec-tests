import pytest
from tests.transaction_eip_7702 import TupleEIP7702
from tests.types import CommandLineArgs, RPCErrorCode
from tests.utils import (
    UserOperation,
    assert_ok,
    assert_rpc_error,
    userop_hash,
    send_bundle_now,
    fund,
    to_hex,
)

AUTHORIZED_ACCOUNT_PREFIX = "ef0100"


def test_send_eip_7702_tx(w3, userop, impl7702, wallet_contract, helper_contract):
    acc = w3.eth.account.create()
    fund(w3, acc.address)

    # create an EIP-7702 authorization tuple
    auth_tuple = TupleEIP7702(
        chainId=hex(1337),
        address=impl7702.address,
        nonce="0x0",
        signer_private_key=acc._private_key.hex(),
    )

    userop.sender = acc.address
    userop.eip7702Auth = auth_tuple

    sender_code = w3.eth.get_code(acc.address)
    assert len(sender_code) == 0

    response = userop.send()
    assert_ok(response)
    send_bundle_now()

    assert response.result == userop_hash(helper_contract, userop)

    sender_code = w3.eth.get_code(acc.address)

    # delegated EOA code is always 23 bytes long
    assert len(sender_code) == 23
    expected_code = "".join([AUTHORIZED_ACCOUNT_PREFIX, impl7702.address[2:].lower()])
    assert sender_code.hex() == expected_code

    eoa_with_authorization = w3.eth.contract(
        abi=wallet_contract.abi,
        address=acc.address,
    )

    # delegated EOA account can actually have a state
    state_after = eoa_with_authorization.functions.state().call()
    assert state_after == 1111111


def test_send_eip_7702_tx_with_initcode(
    w3, userop, impl7702, wallet_contract, helper_contract
):
    acc = w3.eth.account.create()
    fund(w3, acc.address)

    # create an EIP-7702 authorization tuple
    auth_tuple = TupleEIP7702(
        chainId=hex(1337),
        address=impl7702.address,
        nonce="0x0",
        signer_private_key=acc._private_key.hex(),
    )

    userop.sender = acc.address
    userop.eip7702Auth = auth_tuple
    userop.factory = "0x7702"
    # making execution frame revert to make sure 'factoryData' was applied as initCode during validation
    userop.callData = impl7702.encode_abi(abi_element_identifier="fail")
    userop.factoryData = impl7702.encode_abi(
        abi_element_identifier="setState", args=[7702]
    )

    sender_code = w3.eth.get_code(acc.address)
    assert len(sender_code) == 0

    print("userop=")
    print(userop)

    response = userop.send()
    assert_ok(response)
    send_bundle_now()

    sender_code = w3.eth.get_code(acc.address)

    # delegated EOA code is always 23 bytes long
    assert len(sender_code) == 23

    eoa_with_authorization = w3.eth.contract(
        abi=wallet_contract.abi,
        address=acc.address,
    )

    # delegated EOA account can actually have a state
    state_after = eoa_with_authorization.functions.state().call()
    assert state_after == 7702


# normal transaction, using the same sender
@pytest.mark.parametrize("chainid", [0, 1337])
def test_send_post_eip_7702_tx(
    w3, userop, impl7702, wallet_contract, helper_contract, entrypoint_contract, chainid
):
    # first deploy a EIP-7702 address
    acc = w3.eth.account.create()
    w3.eth.send_transaction(
        {"from": w3.eth.accounts[0], "to": acc.address, "value": 10**18}
    )
    nonce = w3.eth.get_transaction_count(acc.address)
    auth_tuple = TupleEIP7702(
        chainId=hex(chainid), address=impl7702.address, nonce=hex(nonce)
    )
    auth_tuple.sign(acc._private_key.hex())
    userop.sender = acc.address
    userop.eip7702Auth = auth_tuple
    response = userop.send()
    assert_ok(response)
    send_bundle_now()

    # use this address in a different UserOp
    account = w3.eth.contract(
        abi=wallet_contract.abi,
        address=acc.address,
    )

    state_before = account.functions.state().call()

    # non-7702 userop, that uses previously created account.
    userop = UserOperation(
        sender=acc.address,
        nonce=hex(entrypoint_contract.functions.getNonce(acc.address, 0).call()),
        callData=wallet_contract.encode_abi(
            abi_element_identifier="setState", args=[state_before + 1]
        ),
        signature="0xface",
    )

    response = userop.send()
    send_bundle_now()

    assert response.result == userop_hash(helper_contract, userop)
    # delegated EOA account can actually have a state
    state_after = account.functions.state().call()
    assert state_after == state_before + 1


def test_send_bad_eip_7702_drop_userop(w3, impl7702, userop):
    acc = w3.eth.account.create()
    # fund the EOA address
    w3.eth.send_transaction(
        {"from": w3.eth.accounts[0], "to": acc.address, "value": 10**18}
    )

    assert len(w3.eth.get_code(acc.address)) == 0

    # create an EIP-7702 authorization tuple, with wrong nonce
    nonce = w3.eth.get_transaction_count(acc.address)
    auth_tuple = TupleEIP7702(
        chainId=hex(1337),
        address=impl7702.address,
        nonce=hex(nonce + 2),
        signer_private_key=acc._private_key.hex(),
    )

    userop.sender = acc.address
    userop.eip7702Auth = auth_tuple

    response = userop.send()
    assert_rpc_error(response, "", RPCErrorCode.REJECTED_BY_EP_OR_ACCOUNT)


def test_send_nonsender_eip_7702_drop_userop(w3, impl7702, userop):
    another_account = w3.eth.account.create()

    # create an EIP-7702 authorization tuple, with different signer
    auth_tuple = TupleEIP7702(
        signer_private_key=another_account._private_key.hex(),
        chainId=hex(1337),
        address=impl7702.address,
        nonce="0x0",
    )
    userop.eip7702Auth = auth_tuple

    assert_rpc_error(userop.send(), "sender", RPCErrorCode.INVALID_FIELDS)


def test_send_wrongchain_eip_7702_drop_userop(
    w3, entrypoint_contract, impl7702, userop
):
    # first, create an account:
    acc = w3.eth.account.create()
    fund(w3, acc.address)

    # create an EIP-7702 authorization tuple
    auth_tuple = TupleEIP7702(
        chainId=hex(1337),
        address=impl7702.address,
        nonce="0x0",
        signer_private_key=acc._private_key.hex(),
    )

    userop.sender = acc.address
    userop.eip7702Auth = auth_tuple

    assert_ok(userop.send())
    send_bundle_now()
    assert len(w3.eth.get_code(acc.address)) == 23

    # submit a UserOp with wrong chainId:
    sender_nonce = entrypoint_contract.functions.getNonce(acc.address, 0).call()
    userop.nonce = to_hex(sender_nonce)

    auth_nonce = w3.eth.get_transaction_count(acc.address)
    # create an EIP-7702 authorization tuple, with wrong chain
    userop.eip7702Auth = TupleEIP7702(
        chainId=hex(1234),
        address=impl7702.address,
        nonce=hex(auth_nonce),
        signer_private_key=acc._private_key.hex(),
    )

    assert_rpc_error(userop.send(), "chainid", RPCErrorCode.INVALID_FIELDS)
