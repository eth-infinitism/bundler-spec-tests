from tests.eip7702.transaction_eip_7702 import TransactionEIP7702, TupleEIP7702


def test_send_eip_7702_tx(w3):
    auth_tuple = TupleEIP7702(
        chainId=hex(1337),
        address="0x7770000000000000000000000000000000000777",
        nonce=hex(1)
    )
    auth_tuple.sign("e331b6d69882b4cb4ea581d88e0b604039a3de5967688d3dcffdd2270c0fd109")

    tx = TransactionEIP7702()
    tx.authorizationList = [auth_tuple]
    res = tx.send()
    print(res)

    # w3.eth.send_transaction(
    #     {"from": w3.eth.accounts[0], "to": "0x2ceB5e5999417babAcdBA0C3DFC501989A53888D", "value": 10**18}
    # )


