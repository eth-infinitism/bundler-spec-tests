from tests.eip7702.transaction_eip_7702 import TransactionEIP7702, TupleEIP7702


def test_send_eip_7702_tx(w3):
    tx = TransactionEIP7702()
    tx.authorizationList = "0xaaff"
    tx.authorizationList = [
        # todo: fill in the valid tuple
        TupleEIP7702(
            hex(0),
            hex(0),
            hex(0),
            hex(0),
            hex(0),
            hex(0),
        )
    ]
    res = tx.send()
    print(res)
