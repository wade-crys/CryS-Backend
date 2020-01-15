#!/usr/bin/env python

from config.api_keys import CRYPTOCOMPARE_API_KEY
from collections import namedtuple
from itertools import groupby
import requests
import datetime
import click
import json
import csv
import os

DAILY = "daily"
MONTHLY = "monthly"

CSV_HEADERS = {
    DAILY: 'timestamp high low open close'.split(),
    MONTHLY: 'timestamp high'.split()
}

PriceData = namedtuple('PriceData', 'timestamp high low open close')

# TODO: make everything else nicer

URL_BASE = 'https://min-api.cryptocompare.com/data/v2/histoday?api_key=' \
           '{api_key}&fsym={cryptocoin_symbol}&tsym={price_currency}&limit={limit}'


def extract_daily_data(cryptocoin_symbol, limit=10, price_currency='USD'):
    url = URL_BASE.format(api_key=CRYPTOCOMPARE_API_KEY,
                          cryptocoin_symbol=cryptocoin_symbol.upper(),
                          limit=limit, price_currency=price_currency)
    response = requests.get(url)
    data = response.json()['Data']['Data']
    daily_data = [
       PriceData(d['time'], d['high'], d['low'], d['open'], d['close'])
       for d in sorted(data, key=lambda x: x['time'])
    ]

    return daily_data


def aggregate(data, aggregation_period):
    # pass thru
    if aggregation_period == DAILY:
        return data
    if aggregation_period == MONTHLY:
        key = lambda x: datetime.datetime.fromtimestamp(x.timestamp).strftime(
            '%Y-%m-%d').rpartition('-')[0]

        grouped = sorted(data, key=key)
        grouped = groupby(grouped, key=key)
        aggregated_data = []
        for k, g in grouped:
            g = sorted(list(g), key=lambda x: x.timestamp)
            aggregated_data.append([g[0].timestamp, max(item.high for item in g)])
        return aggregated_data

    raise NotImplementedError("Unkown aggregation period: {}".format(aggregation_period))


def save_to_csv(data, path, header=None):
    with open(path, 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        if header:
            csv_writer.writerow(header)
        for line in data:
            csv_writer.writerow(line)

@click.command()
@click.option('--symbol', '-s', help='Symbol of cryptocurrency to retrieve '
                                     'price history for', multiple=True)
@click.option('--from-coinmarketcap', help='Use coinmarketcap json to get '
                                           'symbols to retrieve price info for',
              type=click.File(), required=False)
@click.option('--days', '-d', help='Number of days in the past to get price',
              default=10)
@click.option('--aggregation-period', '-a', help='Period to aggregate data over',
              type=click.Choice([DAILY, MONTHLY], case_sensitive=False),
              default=DAILY)
@click.option('--output-directory', '-o', help='Output directory where individual '
                                               'csv files will be saved',
              type=click.Path(file_okay=False), required=True)
def cli(symbol, from_coinmarketcap, days, aggregation_period, output_directory):
    # full coinmarketcap json passed, ignore -s passed and parse symbols
    if from_coinmarketcap:
        coinmarketcap = json.load(from_coinmarketcap)
        symbol = [coin['symbol'] for coin in sorted(coinmarketcap.values(),
                                                    key=lambda x: x['cmc_rank'])]
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for s in symbol:
        output_file = os.path.join(output_directory, s.upper() + '_' +
                                   aggregation_period + '.csv')
        daily_data = extract_daily_data(s, days)
        aggregated_data = aggregate(daily_data, aggregation_period)
        save_to_csv(aggregated_data, output_file, CSV_HEADERS[aggregation_period])


if __name__ == '__main__':
    cli()
