import pandas as pd
from FLClient import FLClient

data = pd.read_csv("data/ton_iot_2.csv")

client = FLClient(data)

client.start()

