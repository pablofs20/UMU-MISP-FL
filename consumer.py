#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from termcolor import colored
from FLClient import FLClient
from MISPManager import MISPManager

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import json
import argparse

def get_last_timestamp():
    f = open('resources/last_timestamp', 'r')
    return int(f.readline())


def set_last_timestamp(last_timestamp):
    f = open('resources/last_timestamp', 'w')
    f.write(str(last_timestamp))

def save_result(result_type, result):
    timestamp = datetime.now()

    filepath = ''
    if result_type == 'model':
        filepath = 'results/model-{ts}.h5'.format(ts=timestamp)
        result.save(filepath)

    elif result_type == 'accuracy':
        filepath = 'results/accuracy-{ts}.png'.format(ts=timestamp)
        plt.plot(result)
        plt.xlabel('Rounds')
        plt.ylabel('Accuracy')
        plt.savefig(filepath)

    return timestamp, filepath

def print_message(m_type, text):
    if m_type == 'INFO':
        print(colored('(INFO) ', 'green') + text)
    elif m_type == 'RESULT':
        print (colored('(RESULT) ', 'yellow') + text)
    elif m_type == 'ERROR':
        print (colored('(ERROR) ', 'red') + text)


def parse_arguments():
    parser = argparse.ArgumentParser(description="MISP data retriever.")

    parser.add_argument(
        "-r",
        "--retr_interval",
        required=True,
        help="Time interval for querying MISP for new data",
    )
    parser.add_argument(
        "-i",
        "--inst_threshold",
        required=True,
        help="Number of instances to register against the aggregator and consume the data",
    )

    args = parser.parse_args()

    return (int(args.retr_interval), int(args.inst_threshold))


def count_instances(df_list):
    ninstances = 0
    for df in df_list:
        ninstances += len(df.index)

    return ninstances


if __name__ == "__main__":
    (retr_interval, inst_threshold) = parse_arguments()

    misp_manager = MISPManager()

    last_timestamp = get_last_timestamp()

    df_list = []

    try:
        while True:
            print_message("INFO", "Looking for new events...")

            (last_timestamp, events) = misp_manager.get_last_events(last_timestamp)

            print_message(
                "RESULT", "{nev} new events have been found".format(nev=len(events))
            )

            for event in events:
                df = misp_manager.parse_ids_network_event(event)
                if df is not None and len(df.index) != 0:
                    df_list.append(df)

            current_instances = count_instances(df_list)
            print_message(
                "INFO",
                "Current number of IDS-network instances/objects is {ins}".format(
                    ins=current_instances
                ),
            )
            if current_instances > inst_threshold:
                print_message(
                    "INFO",
                    "The instance threshold has been reached ({inst} instances)".format(
                        inst=current_instances
                    ),
                )
                data = pd.concat(df_list, ignore_index=True)

                print_message("INFO", "Starting FL...")
                fl_client = FLClient(data)
                fl_client.start()

                print_message("INFO", "FL process has ended. Retrieving final model...")

                final_model = fl_client.get_final_model()
                model_timestamp, model_filepath = save_result("model", final_model)

                print_message(
                    "RESULT",
                    'Model has been saved to "{path}"'.format(path=model_filepath),
                )

                print_message("INFO", "Uploading model to local MISP instance...")

                misp_manager.upload_ml_event(model_timestamp, model_filepath)

                print_message("RESULT", "Model has been uploaded successfully")

                accuracy_hist = fl_client.get_accuracy_hist()
                _, accuracy_filepath = save_result("accuracy", accuracy_hist)

                print_message(
                    "RESULT",
                    'Accuracy history has been saved to "{path}"'.format(
                        path=accuracy_filepath
                    ),
                )

                df_list.clear()

            time.sleep(retr_interval)
    except KeyboardInterrupt:
        print_message("INFO", "Saving new timestamp and exiting...")
        set_last_timestamp(last_timestamp)