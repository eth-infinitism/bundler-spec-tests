from tests.rip7560.types import TransactionRIP7560
from tests.utils import (
    assert_rpc_error,
)
from tests.types import RPCErrorCode


def test_send_failed():
    tx = TransactionRIP7560(
        sender='0x1111111111111111111111111111111111111111',
    )

    ret = tx.send()
    assert_rpc_error(
        ret, "invalid account return data length", RPCErrorCode.INVALID_INPUT
    )
