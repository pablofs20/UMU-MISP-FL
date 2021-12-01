#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymisp import ExpandedPyMISP
from keys import misp_url, misp_key, misp_verifycert
from datetime import datetime
from termcolor import colored
from FLClient import FLClient
try:
    from keys import misp_client_cert
except ImportError:
    misp_client_cert = ''
import pandas as pd
import time
import json


INST_THRESHOLD = 1000
RETR_INTERVAL = 6 # seconds


def parse_event(event):
    event = event.to_json()
    event = json.loads(event)

    column_names = []
    column_values = []
    for obj in event["Object"]:
        for attr in obj["Attribute"]:
            column_names.append(attr["object_relation"])
            column_values.append(attr["value"])

    event_dict = dict(zip(column_names, column_values))
    df = pd.DataFrame(event_dict, index=[0])

    return df

def get_last_events(last_timestamp):
    results = misp.search(timestamp=last_timestamp+1, pythonify=True)
    if len(results) > 0:
        print_message("RESULT", str(len(results)) + " new events have been found ")
        for event in results:
            event = event.to_dict()
            last_timestamp = int(event.get('timestamp'))
    else:
        print_message("RESULT", "No new events have been found")

    return last_timestamp, results

def get_last_timestamp():
    f = open("last_timestamp", "r")
    return int(f.readline())

def set_last_timestamp(last_timestamp):
    f = open("last_timestamp", "w")
    f.write(str(last_timestamp))

def print_message(m_type, text):
    if m_type == "INFO":
        print(colored("(INFO) ", "green") + text)
    elif m_type == "RESULT":
        print(colored("(RESULT) ", "yellow") + text)
    elif m_type == "ERROR":
        print(colored("(ERROR) ", "red") + text)


if __name__ == '__main__':
    if misp_client_cert == '':
        misp_client_cert = None
    else:
        misp_client_cert = (misp_client_cert)

    # Initialize MISP instance
    misp = ExpandedPyMISP(misp_url, misp_key, misp_verifycert, cert=misp_client_cert)
    
    # Get timestamp from last processed event (saved)
    last_timestamp = get_last_timestamp()
    
    # Dataframes list that will contain a dataframe per event
    df_list = []

    try:
        while True:
            print_message("INFO", "Looking for new events...")
            
            # Get new events (from last timestamp)
            last_timestamp, events = get_last_events(last_timestamp)
            for event in events:
                df = parse_event(event)
                df_list.append(df)
            
            current_instances = len(df_list)
            if current_instances > INST_THRESHOLD:
                print_message("INFO", "The instance threshold has been reached")
                #data = pd.concat(df_list, ignore_index=True)
                data = pd.read_csv('data_party0_compressed.csv')

                print_message("INFO", "Starting FL...")
                fl_client = FLClient(data)
                fl_client.start()
                
                print_message("INFO", "FL process has ended. Retrieving final model...")
                final_model = fl_client.get_final_model()
                accuracy_hist = fl_client.get_accuracy_hist()
                
                ###
                # Upload final model back to MISP
                ###

                df_list.clear()

            time.sleep(RETR_INTERVAL)
    
    except KeyboardInterrupt:
        # Save new last timestamp and exit
        print_message("INFO", "Saving new timestamp and exiting...")
        set_last_timestamp(last_timestamp)
