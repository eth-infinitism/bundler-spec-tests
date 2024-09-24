def test_devnet(w3, tx_7560):
    # account: Account = w3.eth.account.from_key(private_key)
    # print(w3.middleware_onion.middlewares[0])
    nonce = w3.eth.get_transaction_count(w3.eth.default_account)
    transaction = {
        "from": w3.eth.default_account,
        "to": "0xF0109fC8DF283027b6285cc889F5aA624EaC1F55",
        "value": 1,
        "gas": 2000000,
        "maxFeePerGas": 2000000000,
        "maxPriorityFeePerGas": 1000000000,
        "nonce": nonce,
        "chainId": 1337,
    }
    # signed = w3.eth.account.sign_transaction(transaction, account.key)
    # res = w3.eth.send_raw_transaction(signed.raw_transaction.hex())
    res = w3.eth.send_transaction(transaction)
    print("type 1 tx:", res.hex())
    res = tx_7560.send()
    print("type 4 tx:", res)
