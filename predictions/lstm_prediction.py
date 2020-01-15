#!/usr/bin/env python

from sklearn.preprocessing import MinMaxScaler
from keras.layers import LSTM, Dense, Dropout
from keras.models import Sequential
import pandas as pd
import numpy as np
import click
import json
import os

def split_sequence(seq, n_steps_in, n_steps_out):
    """
    Splits the univariate time sequence
    """
    X, y = [], []

    for i in range(len(seq)):
        end = i + n_steps_in
        out_end = end + n_steps_out

        if out_end > len(seq):
            break

        seq_x, seq_y = seq[i:end], seq[end:out_end]

        X.append(seq_x)
        y.append(seq_y)

    return np.array(X), np.array(y)


def layer_maker(n_layers, n_nodes, activation, drop=None, d_rate=.5):
    """
    Creates a specified number of hidden layers for an RNN
    Optional: Adds regularization option - the dropout layer to prevent potential overfitting (if necessary)
    """

    # Creating the specified number of hidden layers with the specified number of nodes
    for x in range(1, n_layers + 1):
        model.add(LSTM(n_nodes, activation=activation, return_sequences=True))

        # Adds a Dropout layer after every Nth hidden layer (the 'drop' variable)
        try:
            if x % drop == 0:
                model.add(Dropout(d_rate))
        except:
            pass





@click.command()
@click.option('--symbol', '-s', help='Symbol of cryptocurrency to retrieve '
                                     'price history for', multiple=True)
@click.option('--from-coinmarketcap', help='Use coinmarketcap json to get '
                                           'symbols to retrieve price info for',
              type=click.File(), required=False)
@click.option('--historical-price-directory', help='Path to directory containing'
                                                   ' CSVs with historic data',
              type=click.Path(file_okay=False), required=True)
def cli(symbol, from_coinmarketcap, historical_price_directory):
    # full coinmarketcap json passed, ignore -s passed and parse symbols
    if from_coinmarketcap:
        coinmarketcap = json.load(from_coinmarketcap)
        symbol = [coin['symbol'] for coin in sorted(coinmarketcap.values(),
                                                    key=lambda x: x['cmc_rank'])]
    for s in symbol:
        price_file_path = os.path.join(historical_price_directory,
                                       s + '_daily.csv')

        df = pd.read_csv(price_file_path)

        df = df.set_index("timestamp")[['high']].tail(1000)
        df = df.set_index(pd.to_datetime(df.index, unit='s'))

        # Normalizing/Scaling the Data
        scaler = MinMaxScaler()
        df = pd.DataFrame(scaler.fit_transform(df), columns=df.columns,
                          index=df.index)

        # How many periods looking back to learn
        n_per_in = 30

        # How many periods to predict
        n_per_out = 7

        # Features (in this case it's 1 because there is only one feature: price)
        n_features = 1

        # Splitting the data into appropriate sequences
        X, y = split_sequence(list(df.high), n_per_in, n_per_out)

        # Reshaping the X variable from 2D to 3D
        X = X.reshape((X.shape[0], X.shape[1], n_features))

        model = Sequential()

        # Activation
        activ = "softsign"

        # Input layer
        model.add(LSTM(30, activation=activ, return_sequences=True,
                       input_shape=(n_per_in, n_features)))

        # Hidden layers
        n_layers=6
        n_nodes=12
        activation=activ

        # Creating the specified number of hidden layers with the specified number of nodes
        for x in range(1, n_layers + 1):
            model.add(
                LSTM(n_nodes, activation=activation, return_sequences=True))


        # Final Hidden layer
        model.add(LSTM(10, activation=activ))

        # Output layer
        model.add(Dense(n_per_out))

        # Model summary
        model.summary()

        # Compiling the data with selected specifications
        model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])

        res = model.fit(X, y, epochs=10, batch_size=32, validation_split=0.1)

        # Getting predictions by predicting from the last available X variable
        yhat = model.predict(X[-1].reshape(1, n_per_in, n_features)).tolist()[0]

        # Transforming values back to their normal prices
        yhat = scaler.inverse_transform(np.array(yhat).reshape(-1, 1)).tolist()

        # Getting the actual values from the last available y variable which correspond to its respective X variable
        actual = scaler.inverse_transform(y[-1].reshape(-1, 1))

        # Printing and plotting those predictions
        predicted = yhat

        actual = [e[0] for e in actual.tolist()]
        # Printing and plotting the actual values

        yhat = model.predict(np.array(df.tail(n_per_in)).reshape(1, n_per_in,
                                                                 n_features)).tolist()[
            0]
        # Transforming the predicted values back to their original prices
        yhat = scaler.inverse_transform(np.array(yhat).reshape(-1, 1)).tolist()

        # Creating a DF of the predicted prices
        preds = pd.DataFrame(yhat, index=pd.date_range(start=df.index[-1],
                                                       periods=len(yhat),
                                                       freq="D"),
                             columns=df.columns)
        #
        # Printing the predicted prices
        print(preds)

        mape = np.mean(
            np.abs(preds['high'] - actual) / np.abs(actual)) * 100  # MAPE
        print('#####' + s, mape)


if __name__ == '__main__':
    cli()
