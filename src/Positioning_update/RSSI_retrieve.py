# -*- coding: utf-8 -*-
"""
RSSI Main Script
Author: Hoai-Nam Nguyen
"""

import RSSI_function
import os
from dotenv import load_dotenv
import requests
import json
import warnings
from pymongo import MongoClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore")


def main():
    """
    Main function to retrieve and store RSSI data from vMM to MongoDB.
    """
    # Load variables from .env file
    load_dotenv()

    # Login
    username = os.getenv("ACCOUNT")
    password = os.getenv("PASSWORD")
    vMM_aosip = os.getenv('vMM_aosip')

    # Building name
    building = os.getenv('BUILDING')

    # Read the JSON file containing AP data
    with open('AP_dict', 'r') as file:
        ref_aps_dict_all = json.load(file)

    # Set RSSI threshold
    threshold = 60

    # Get the token to access vMM information  -- via API
    token = RSSI_function.authentication(username, password, vMM_aosip)

    # Get floor list
    f_name = RSSI_function.get_floor_list(ref_aps_dict_all)

    # Get AP list
    AP_name = RSSI_function.get_AP_name(ref_aps_dict_all)

    # Get datetime
    ts, ts_tw_str, ts_tw = RSSI_function.calculate_taiwan_time()

    # Retrieve RSSI for reference APs in every floor
    ref = RSSI_function.ref_retrieve_all(AP_name, f_name, vMM_aosip, token, building)

    # Retrieve RSSI for rogue APs in every floor
    rogue = RSSI_function.rogue_retrieve_all(AP_name, f_name, vMM_aosip, token, building, threshold)

    # Merge reference APs and rogue APs
    dfa = ref.append(rogue)

    # Save as json format
    data_json = json.loads(dfa.to_json(orient='records'))

    # Add datetime
    for i in range(len(data_json)):
        data_json[i].update({'ts': ts, 'DatetimeStr': ts_tw_str, 'Datetime': ts_tw})

    # Databases info
    MONGOIP = os.getenv('MONGOIP')
    DB = os.getenv('DB')
    COLLECTION = os.getenv('COLLECTION')

    ## Store json data to MongoDB
    # client = MongoClient(MONGOIP, 27017)
    # db = client[DB]
    # col = db[COLLECTION]
    # col.insert_many(data_json)

    print('Done!')
    print(dfa)


if __name__ == "__main__":
    main()
