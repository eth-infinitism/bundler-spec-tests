from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    assert_rpc_error,
    fund,

)
from tests.types import (
    RPCErrorCode
)


def test_eth_send_no_gas(w3):
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111112",
    )

    ret = tx.send()
    assert_rpc_error(
        ret, "insufficient funds", RPCErrorCode.INVALID_INPUT
    )


def test_eth_send_no_code(w3):
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111113",
    )
    fund(w3, tx.sender)

    ret = tx.send()
    assert_rpc_error(
        ret, "invalid account return data length", RPCErrorCode.INVALID_INPUT
    )


def test_eth_send_no_code_wrong_nonce(w3):
    tx = TransactionRIP7560(
        sender="0x1111111111111111111111111111111111111113",
        nonce=hex(5),
    )
    fund(w3, tx.sender)

    ret = tx.send()
    assert_rpc_error(
        ret, "nonce too high", RPCErrorCode.INVALID_INPUT
    )
