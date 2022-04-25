#!/usr/bin/python
# -*- coding: utf-8 -*-

from pymisp import ExpandedPyMISP, MISPEvent, MISPObject
from keys import misp_url, misp_key
from pathlib import Path

import pandas as pd
import numpy as np
import json

DEFAULT_DIST = "0" # Distribution
DEFAULT_TLID = "1" # Threat Level ID
DEFAULT_ANLY = "1" # Analysis
DEFAULT_DCOR = True # Disable correlation


def add_ml_object(event, model_timestamp, model_filepath):
    f = Path(model_filepath)
    
    obj = MISPObject("ml_ids", template_uuid="fbcc20a2-54e2-11eb-ae93-0242ac130002")

    obj.add_attribute("creation_timestamp", type="datetime", value=model_timestamp)
    obj.add_attribute("ml_file", type="attachment", value="model.h5", data=f)
    obj.add_attribute("ml_encoding", type="text", value="HDF5")

    event.add_object(obj)
    event.info = "ML IDS"

    return event

def create_default_event():
    event = MISPEvent(disable_correlation=DEFAULT_DCOR)

    event.distribution = DEFAULT_DIST
    event.threat_level_id = DEFAULT_TLID
    event.analysis = DEFAULT_ANLY

    return event

class MISPManager:
    def __init__(self):
        self.instance = ExpandedPyMISP(misp_url, misp_key)

    def upload_ml_event(self, model_timestamp, model_filepath):
        event = create_default_event()
        ml_event = add_ml_object(event, model_timestamp, model_filepath)

        self.instance.add_event(ml_event)

    def parse_ids_network_event(self, event):
        event = event.to_json()
        event = json.loads(event)

        key = "Object"
        if key not in event.keys():
            return None

        df = None
        for obj in event['Object']:
            column_names = []
            column_values = []
            if obj['name'] != "ids-network-data":
                continue
            for attr in obj['Attribute']:
                column_names.append(attr['object_relation'])
                column_values.append(attr['value'])

            column_values = np.asarray(column_values).astype(np.float32)
            event_dict = dict(zip(column_names, column_values))
            if df is None:
                df = pd.DataFrame(event_dict, index=[0])
            else:
                df = df.append(event_dict, ignore_index=True)

        return df

    def get_last_events(self, last_timestamp):
        results = self.instance.search(timestamp=last_timestamp + 1, pythonify=True)
        
        if len(results) > 0:
            for event in results:
                event = event.to_dict()
                last_timestamp = int(event.get('timestamp'))

        return (last_timestamp, results)

