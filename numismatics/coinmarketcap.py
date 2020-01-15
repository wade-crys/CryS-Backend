from config.api_keys import COINMARKETCAP_API_KEY

import requests
import json


latest_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?CMC_PRO_API_KEY=f232764b-1001-4886-8ef1-16dc4f7d82d6'

r = requests.get(latest_url)
coins_response = json.loads(r.text)
coins = coins_response['data']
with open('coins.json', 'w') as f:
    json.dump(coins, f, indent=4, sort_keys=True)

ids = [coin['id'] for coin in coins]


metadata_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?CMC_PRO_API_KEY=f232764b-1001-4886-8ef1-16dc4f7d82d6'
r = requests.get(metadata_url + '&id=' + ",".join(str(elt) for elt in ids) + '&aux=urls,logo,description,tags,platform,date_added,notice,status')
metadata_response = json.loads(r.text)
coins_metadata = metadata_response['data']
with open('coins_metadata.json', 'w') as f:
    json.dump(coins_metadata, f, indent=4, sort_keys=True)

# join info together
#
# with open('coins.json', 'r') as coins_file, open('coins_metadata.json', 'r') as coins_metadata_file:
#     coins = json.load(coins_file)
#     coins_metadata = json.load(coins_metadata_file)


assert(len(coins) == len(coins_metadata))

for id, coin_metadata in coins_metadata.items():
    # find coin by id
    coin_extras = [coin for coin in coins if coin['id'] == int(id)][0]
    coin_metadata.update(coin_extras)
    coins_metadata[id] = coin_metadata

with open('coins_full.json', 'w') as f:
    json.dump(coins_metadata, f, indent=4, sort_keys=True)
