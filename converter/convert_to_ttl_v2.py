#!/usr/bin/env python

from collections import namedtuple
from jinja2 import Template
import datetime
import pickle
import click
import json
import uuid
import csv
import os

News = namedtuple('News', 'title description source created_at currencies url')


def parse_coin(coin_data):
    description = coin_data['description'].replace('\"', '\\"')

    coin = {
        'name': coin_data['name'],
        'category': coin_data['category'],
        'circulating_supply': coin_data['circulating_supply'],
        'cmc_rank': coin_data['cmc_rank'],
        'date_added': coin_data['date_added'],
        'description': description,
        'id': coin_data['id'],
        'logo': coin_data['logo'],
        'percent_change_24h': coin_data['quote']['USD']['percent_change_24h'],
        'percent_change_7d': coin_data['quote']['USD']['percent_change_7d'],
        'price': coin_data['quote']['USD']['price'],
        'status': coin_data['status'],
        'mineable': "true" if 'mineable' in coin_data['tags'] else "false",
        'market_cap': coin_data['quote']['USD']['market_cap'],
        'symbol': coin_data['symbol'],
        'urls': {

        }
    }

    # stuff inside urls can miss and can have multiple values
    # place only the first link (if one exists) into a new dict
    # at  the same key
    for url_type, url_value in coin_data['urls'].items():
        if len(url_value):
            coin['urls'][url_type] = url_value[0]
    # coin is based on another coin
    if coin_data['platform']:
        coin['platform'] = coin_data['platform']['symbol']

    return coin


def parse_news(news_data):
    return {
        'id': "news-" + str(uuid.uuid4()),
        'title': news_data.title,
        'description': news_data.description,
        'source': news_data.source,
        'date_published': news_data.created_at,
        'url': news_data.url,
        'about': news_data.currencies
    }


def parse_transaction(transactions_data):
    return {
        'hash': transactions_data[0],
        'sender': transactions_data[1],
        'receiver': transactions_data[2],
        'amount': transactions_data[3],
        'amount_usd': transactions_data[4],
        'date_traded': transactions_data[5],
    }


def parse_price_history(price_data):
        return {
            'id': "price-history-" + str(uuid.uuid4()),
            'at_date': datetime.datetime.fromtimestamp(int(price_data[0])).strftime('%Y-%m-%d'),
            'value': price_data[1]
        }


@click.command()
@click.option('--template', '-t', help='Path to Jinja template for turtle file',
              type=click.File(), required=True)
@click.option('--coinmarketcap-json', help='Coinmarketcap combined json, as '
                                           'produced by numismatics.coinmarketcap',
              type=click.File(), required=True)
@click.option('--cryptopanic-pickle', help='Pickle file containing news from '
                                            'cryptopanic.com, as produced by '
                                            'news.cryptopanic',
              type=click.File(mode='rb'), required=True)
@click.option('--transactions-csv', help='CSV containing transaction data',
              type=click.File(), required=True)
@click.option('--historical-price-directory', help='Path to directory containing'
                                                   ' CSVs with historic data',
              type=click.Path(file_okay=False), required=True)
@click.option('--output-file', '-o', help='Path to output file',
              type=click.File(mode='w'), required=True)
def cli(template, coinmarketcap_json, cryptopanic_pickle, transactions_csv,
        historical_price_directory, output_file):
    ttl_template = Template(template.read())

    coin_data = json.load(coinmarketcap_json)
    coins = [parse_coin(coin) for coin in coin_data.values()]

    news_data = pickle.load(cryptopanic_pickle)
    news = [parse_news(news) for news in news_data]

    reader = csv.reader(transactions_csv, delimiter=',')
    transaction_data = [row for row in reader][1:]

    addresses = []
    # sender addresses
    addresses.extend(transaction[1] for transaction in transaction_data)
    # receiver addresses
    addresses.extend(transaction[2] for transaction in transaction_data)

    transactions = [parse_transaction(transaction) for transaction in transaction_data]

    price_history_by_coin = {}

    for coin in coins:
        price_file_path = os.path.join(historical_price_directory,
                                      coin['symbol'] + '_monthly.csv')
        with open(price_file_path) as f:
            reader = csv.reader(f, delimiter=',')
            price_data = [row for row in reader][1:]
        prices = [parse_price_history(price) for price in price_data]
        price_history_by_coin[coin['symbol']] = prices

    rendered_ttl = ttl_template.render(coins=coins, news=news,
                                       addresses=set(addresses),
                                       transactions=transactions,
                                       price_history_by_coin=price_history_by_coin)
    output_file.write(rendered_ttl)


    # addresses = defaultdict(int)
    # for transaction in data:
    #     addresses[transaction[1]] += 1
    #     addresses[transaction[2]] += 1
    # for addr, count in addresses.items():
    #     if count > 1:
    #         print(addr, count)


if __name__ == '__main__':
    cli()
