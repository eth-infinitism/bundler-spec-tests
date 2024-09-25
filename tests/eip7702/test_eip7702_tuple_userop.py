import time

from tests.transaction_eip_7702 import TupleEIP7702
from tests.types import CommandLineArgs
from tests.utils import deploy_contract, userop_hash, send_bundle_now

ADDRESS = "0xbe862AD9AbFe6f22BCb087716c7D89a26051f74C"
PRIVATE_KEY = "e331b6d69882b4cb4ea581d88e0b604039a3de5967688d3dcffdd2270c0fd109"
AUTHORIZED_ACCOUNT_PREFIX = "ef0100"


def test_send_eip_7702_tx(w3, userop, wallet_contract, helper_contract):
    # fund the EOA address
    w3.eth.send_transaction(
        {"from": w3.eth.accounts[0], "to": ADDRESS, "value": 10 ** 18}
    )

    # implementation is only used as a "delegation target"
    implementation = deploy_contract(
        w3, "SimpleWallet", ctrparams=[CommandLineArgs.entrypoint]
    )

    # create an EIP-7702 authorization tuple
    nonce = w3.eth.get_transaction_count(ADDRESS)
    auth_tuple = TupleEIP7702(
        chainId=hex(1337), address=implementation.address, nonce=hex(nonce)
    )
    auth_tuple.sign(PRIVATE_KEY)

    userop.sender = ADDRESS
    userop.authorizationList = [auth_tuple]

    # note that ADDRESS used here is hard-coded so the test will only pass once!
    sender_code = w3.eth.get_code(ADDRESS)
    assert len(sender_code) == 0

    response = userop.send()
    send_bundle_now()

    assert response.result == userop_hash(helper_contract, userop)

    sender_code = w3.eth.get_code(ADDRESS)

    # delegated EOA code is always 23 bytes long
    assert len(sender_code) == 23
    expected_code = "".join(
        [AUTHORIZED_ACCOUNT_PREFIX, implementation.address[2:].lower()]
    )
    assert sender_code.hex() == expected_code

    eoa_with_authorization = w3.eth.contract(
        abi=wallet_contract.abi,
        address=ADDRESS,
    )

    # delegated EOA account can actually have a state
    state_after = eoa_with_authorization.functions.state().call()
    assert state_after == 1111111
