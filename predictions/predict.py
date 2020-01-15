#!/usr/bin/env python

from datetime import date
import pandas as pd
import numpy as np
import pyflux as pf
import click
import json
import uuid
import os

from SPARQLWrapper import SPARQLWrapper, JSON

GRAPHDB_CLIENT = SPARQLWrapper("http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys/statements")
FUSEKI_CLIENT = SPARQLWrapper("http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7201/crys/update")


INSERT_PREDICTION_TEMPLATE = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
INSERT DATA {{
crys:{prediction_id} rdf:type crys:Prediction ;
    crys:for crys:{symbol} ;
    crys:predicted_date "{predicted_date}"^^xsd:date ;
    crys:predicted_price "{price}"^^xsd:float ;
    crys:generated_at "{generated_at}"^^xsd:date .
}}
"""


@click.command()
@click.option('--symbol', '-s', help='Symbol of cryptocurrency to retrieve '
                                     'price history for', multiple=True)
@click.option('--from-coinmarketcap', help='Use coinmarketcap json to get '
                                           'symbols to retrieve price info for',
              type=click.File(), required=False)
@click.option('--historical-price-directory', help='Path to directory containing'
                                                   ' CSVs with historic data',
              type=click.Path(file_okay=False), required=True)
@click.option('--publish/--no-publish', is_flag=True, default=False, help='If True, it will '
                                                             'insert the predictions '
                                                             'in the GraphDB database')
def cli(symbol, from_coinmarketcap, historical_price_directory, publish):
    # full coinmarketcap json passed, ignore -s passed and parse symbols

    if from_coinmarketcap:
        coinmarketcap = json.load(from_coinmarketcap)
        symbol = [coin['symbol'] for coin in sorted(coinmarketcap.values(),
                                                    key=lambda x: x['cmc_rank'])]
    for indx, s in enumerate(symbol):
        print('Predicting values for {} ({}/{})'.format(s, indx + 1, len(symbol)))
        price_file_path = os.path.join(historical_price_directory,
                                       s + '_daily.csv')

        data = pd.read_csv(price_file_path)
        data.index = data['timestamp'].values
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')

        training = data.iloc[:, [0, 1]]
        # uncomment if you need to check performance
        # training = data.iloc[:-7, [0, 1]]
        # actual = data.iloc[-7:, [0, 1]]

        model = pf.ARIMA(data=training, ar=4, ma=4, target='high',
                         family=pf.Normal())

        x = model.fit("MLE")

        predicted = model.predict(h=7)
        predicted['timestamp'] = pd.to_datetime(predicted.index.values,
                                                unit='s')
        predicted = predicted[['timestamp', 'high']]
        # uncomment if you need to check performance
        # mape = np.mean(np.abs(predicted['high'] - actual['high']) / np.abs(
        #     actual['high'])) * 100  # MAPE
        # print(s, mape)

        for index, series in predicted.iterrows():
            id = "predictions-" + str(uuid.uuid4())
            predicted_date = str(series['timestamp']).split()[0]
            price = float("{0:.2f}".format(series['high']))
            generated_at = date.today()
            query = INSERT_PREDICTION_TEMPLATE.format(prediction_id=id, symbol=s,
                                                    predicted_date=predicted_date,
                                                    price=price,
                                                    generated_at=generated_at)
            if publish:
                # insert in grapdb
                GRAPHDB_CLIENT.setQuery(query)
                GRAPHDB_CLIENT.queryType = "INSERT"
                GRAPHDB_CLIENT.method = "POST"
                GRAPHDB_CLIENT.setReturnFormat(JSON)
                results = GRAPHDB_CLIENT.query().convert()
                # insert in fuseki
                FUSEKI_CLIENT.setQuery(query)
                FUSEKI_CLIENT.queryType = "INSERT"
                FUSEKI_CLIENT.method = "POST"
                FUSEKI_CLIENT.setReturnFormat(JSON)
                results = FUSEKI_CLIENT.query().convert()
            else:
                print(query)


if __name__ == '__main__':
    cli()

