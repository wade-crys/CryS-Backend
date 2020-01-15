import blockchain
import datetime

url = 'https://blockchain.info/rawtx/{}'


btc_to_usd = blockchain.exchangerates.get_ticker('btc')['USD']

transactions = {}
while len(transactions) < 100:
    txs = blockchain.blockexplorer.get_unconfirmed_tx(api_code='ETH')
    for t in txs:
        time = t.time
        input = t.inputs[0]
        output = t.outputs[0]
        if 'address' not in dir(input):
            continue
        if output.address is None:
            continue
        btc_value = input.value * 0.00000001
        if t not in transactions:
            transactions[t.hash] = [t.hash, input.address, output.address,
                                    btc_value, btc_value * btc_to_usd.p15min,
                                    datetime.datetime.fromtimestamp(time).isoformat()]

for _, transaction in transactions.items():
    print(transaction)

with open('btc_transactions.csv', 'w') as f:
    f.write('Hash,From,To,Amount_BTC,Amount_USD,Time\n')
    for _, transaction in transactions.items():
        f.write(",".join(str(elt) for elt in transaction) + '\n')
