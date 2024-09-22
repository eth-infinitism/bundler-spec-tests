from eth_account import Account

private_key = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"


def test_devnet(w3):
    account: Account = w3.eth.account.from_key(private_key)
    transaction = {
        'to': '0xF0109fC8DF283027b6285cc889F5aA624EaC1F55',
        'value': 1000000000,
        'gas': 2000000,
        'maxFeePerGas': 2000000000,
        'maxPriorityFeePerGas': 1000000000,
        'nonce': 0,
        'chainId': 1,
        'type': '0x2',  # the type is optional and, if omitted, will be interpreted based on the provided transaction parameters
    }
    signed = w3.eth.account.sign_transaction(transaction, account.key)
    res = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(res)
