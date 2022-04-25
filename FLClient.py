#!/usr/bin/python
# -*- coding: utf-8 -*-

import flwr as fl
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
import tensorflow
import configparser

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

CONFIG_FILE = "resources/fl.ini"


def preprocess_data(data):
    pd.set_option("use_inf_as_na", True)
    data.fillna(data.median(), inplace=True)

    data = data.sample(frac=1).reset_index(drop=True)

    scaler = MinMaxScaler()
    features_to_normalize = data.columns.difference(["Label"])
    data[features_to_normalize] = scaler.fit_transform(data[features_to_normalize])

    return data


def split_data(data, test_size):
    x_0 = data.iloc[:, :-1]
    y_0 = data.iloc[:, -1]
    x = np.array(x_0)
    y = np.array(y_0)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size)

    return x_train, x_test, y_train, y_test


def create_model(data):
    input_shape = (len(data.columns) - 1,)
    num_classes = data["Label"].nunique()

    model = Sequential()
    model.add(Dense(350, input_shape=input_shape, activation="relu"))
    model.add(Dense(50, activation="relu"))
    model.add(Dense(num_classes, activation="softmax"))

    model.compile(
        loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"]
    )

    return model


def get_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    client_config = config["FL Client"]
    aggregator_config = config["FL Aggregator"]

    return (
        str(aggregator_config["IP"]),
        int(aggregator_config["Port"]),
        float(client_config["TestSize"]),
        int(client_config["LocalEpochs"]),
        int(client_config["BatchSize"]),
        int(client_config["StepsPerEpoch"]),
    )


class ToNIoTClient(fl.client.NumPyClient):
    def __init__(self, client):
        self.x_train, self.x_test, self.y_train, self.y_test = (
            client.x_train,
            client.x_test,
            client.y_train,
            client.y_test,
        )

        self.model, self.accuracy_hist = client.model, client.accuracy_hist

        self.epochs, self.batch_size, self.steps_per_epoch = (
            client.epochs,
            client.batch_size,
            client.steps_per_epoch,
        )

    def get_parameters(self):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        self.model.fit(
            self.x_train,
            self.y_train,
            epochs=self.epochs,
            batch_size=self.batch_size,
            steps_per_epoch=self.steps_per_epoch,
        )
        return self.model.get_weights(), len(self.x_train), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        loss, accuracy = self.model.evaluate(self.x_test, self.y_test)
        self.accuracy_hist.append(accuracy)
        return loss, len(self.x_test), {"accuracy": accuracy}


class FLClient:
    def __init__(self, data):
        (
            self.aggregator_ip,
            self.aggregator_port,
            self.test_size,
            self.epochs,
            self.batch_size,
            self.steps_per_epoch,
        ) = get_config()
        data = preprocess_data(data)
        self.x_train, self.x_test, self.y_train, self.y_test = split_data(
            data, self.test_size
        )
        self.model = create_model(data)
        self.accuracy_hist = []

    def start(self):
        fl.client.start_numpy_client(
            "{aggregator_ip}:{aggregator_port}".format(
                aggregator_ip=self.aggregator_ip, aggregator_port=self.aggregator_port
            ),
            client=ToNIoTClient(self),
        )

    def get_final_model(self):
        return self.model

    def get_accuracy_hist(self):
        return self.accuracy_hist

