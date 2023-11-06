# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 22:16:56 2023

@author: Hoai-Nam Nguyen
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
import json


def main():
    # Load variables from .env file
    load_dotenv()
    
    # Login
    username = os.getenv("ACCOUNT")
    password = os.getenv("PASSWORD")
    vMM_aosip = os.getenv('vMM_aosip')
    
    # Building name 
    building = 'IY'
    
    # Read the JSON file
    with open('AP_dict', 'r') as file:
        ref_aps_dict_all = json.load(file)
        
    # Set RSSI threshold
    threshold = 60 
    # Max AP number per floor in the building. Take IY building as an example, max AP = 5.
    max_ap_per_floor = 5

    #Get the token to access vMM information  -- via API
    token = RSSI_function.authentication(username,password,vMM_aosip)
    
    # Get floor list
    f_name = RSSI_function.get_floor_list(ref_aps_dict_all)
    
    # Get AP list
    AP_name = RSSI_function.get_AP_name(ref_aps_dict_all)

    # Get AP coordinates
    AP_coords = RSSI_function.get_AP_coords(ref_aps_dict_all, max_ap_per_floor)
    
    # Get datetime
    ts, ts_tw_str, ts_tw = RSSI_function.calculate_taiwan_time()
    
    # Retrieve RSSI for rogue APs in every floor
    rogue = RSSI_function.rogue_rss_retrieve(AP_name[0], f_name[0], vMM_aosip, token, building, threshold)
    
    # Save as json format
    data_json = json.loads(rogue.to_json(orient='records'))
    
    # Add datetime
    for i in range(len(data_json)):
        data_json[i].update({'ts': ts, 'DatetimeStr': ts_tw_str, 'Datetime': ts_tw})
    
    # =============================================================================
#     # Databases info
    MONGOIP = os.getenv('MONGOIP')
    DB = os.getenv('DB')
    COLLECTION = os.getenv('COLLECTION')
    
#     # Store json data to MongoDB
#     client = MongoClient(MONGOIP,27017)
#     db = client[DB]
#     col=db[COLLECTION]
#     col.insert_many(data_json)
        
    print('Done!')
    print(rogue)
    
if __name__ == "__main__":
    main()
