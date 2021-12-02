import flwr as fl
import pandas as pd
import numpy as np
import warnings
# To avoid TF future warnings
warnings.filterwarnings('ignore', category=FutureWarning)
import tensorflow

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


TEST_SIZE = 0.2


def preprocess_data(data):
    # Transform INF and NaN values to median
    pd.set_option('use_inf_as_na', True)
    data.fillna(data.median(), inplace=True)

    # Shuffle samples (optional)
    data = data.sample(frac=1).reset_index(drop=True)

    # Normalize column values except for label column
    scaler = MinMaxScaler()
    features_to_normalize = data.columns.difference(['Label'])
    data[features_to_normalize] = scaler.fit_transform(data[features_to_normalize])

    return data

def split_data(data):
    # Split data intro train/test sets
    x_0 = data.iloc[:, :-1]
    y_0 = data.iloc[:, -1]
    x = np.array(x_0)
    y = np.array(y_0)
    x_train, x_test, y_train, y_test = \
        train_test_split(x, y, test_size = TEST_SIZE)

    return x_train, x_test, y_train, y_test

def create_model(data):
    input_shape = (len(data.columns) - 1,)
    num_classes = data['Label'].nunique()

    model = Sequential()
    model.add(Dense(350, input_shape=input_shape, activation='relu'))
    model.add(Dense(50, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))

    model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    return model


class ToNIoTClient(fl.client.NumPyClient):
    def __init__(self, client):
        self.x_train, self.x_test, self.y_train, self.y_test = \
            client.x_train, client.x_test, client.y_train, client.y_test

        self.model = client.model
        self.accuracy_hist = client.accuracy_hist
            
    def get_parameters(self):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        self.model.fit(self.x_train, self.y_train, epochs=1, batch_size=32, steps_per_epoch=1)
        return self.model.get_weights(), len(self.x_train), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        loss, accuracy = self.model.evaluate(self.x_test, self.y_test)
        self.accuracy_hist.append(accuracy)
        return loss, len(self.x_test), {"accuracy": accuracy}


class FLClient:
    def __init__(self, data):
        data = preprocess_data(data)
        self.x_train, self.x_test, self.y_train, self.y_test = \
            split_data(data)
        self.model = create_model(data)
        self.accuracy_hist = []

    def start(self, aggregator_ip):
        fl.client.start_numpy_client("{aggregator_ip}:8080".format(aggregator_ip=aggregator_ip), client=ToNIoTClient(self))

    def get_final_model(self):
        return self.model

    def get_accuracy_hist(self):
        return self.accuracy_hist
