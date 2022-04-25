#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import signal
import pandas as pd
import uuid

from termcolor import colored
from pymisp import ExpandedPyMISP,PyMISP, MISPEvent, MISPObject, MISPAttribute
from keys import misp_url, misp_key

DEF_DIST = 0
DEF_INFO = "IDS Network Data"
DEF_ANLY = 1
DEF_TLID = 4

def parse_args():
    parser = argparse.ArgumentParser(description='ToN-IoT-based IDS Network Data event producer')
    parser.add_argument("-n", "--nobjects")
    parser.add_argument("-d", "--data_source")
    
    args = parser.parse_args()
    
    return args

def create_event_backbone():
    event = MISPEvent(disable_correlation=True)
    
    event.distribution = DEF_DIST
    event.threat_level_id = DEF_TLID
    event.analysis = DEF_ANLY
    event.info = DEF_INFO

    return event

def print_message(m_type, text):
    if m_type == 'INFO':
        print(colored('(INFO) ', 'green') + text)

        
if __name__ == "__main__":
    args = parse_args()

    misp = PyMISP(misp_url, misp_key)

    df = pd.read_csv(args.data_source)

    event = create_event_backbone()

    nobjects = int(args.nobjects)
    current_row = 0
    for index, row in df.iterrows():
        object = MISPObject(
            name="ids-network-data",
            template_uuid="ea1c97ae-cb89-4e15-aad0-18e5db3483b2",
            uuid=uuid.uuid4(),
        )
        for column in df.columns:
            object.add_attribute(
                column,
                None,
                type="comment",
                category="Other",
                value=str(row[column]),
                uuid=uuid.uuid4(),
            )
            event.add_object(object)

        current_row = 1
        if current_row % nobjects == 0:
            event = misp.add_event(event)
            print_message("INFO", "Event uploaded")
            event = create_event_backbone()


