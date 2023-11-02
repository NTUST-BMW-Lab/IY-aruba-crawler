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


def main():
    # Load variables from .env file
    load_dotenv()
    
    # Login
    username = os.getenv("ACCOUNT")
    password = os.getenv("PASSWORD")
    vMM_aosip = os.getenv('vMM_aosip')
    
    # Building name 
    building = 'IY'
    
    # AP dictionary for the building. Take IY building as an example
    ref_aps_dict_all = {
        '1F': {'1F_AP01': (16.84, 13.98), '1F_AP03': (19.59, 1.51), '1F_AP05': (23.9, 9.38), '1F_AP07': (33.62, 7.42)},
        '2F': {'2F_AP01': (12.07, 6.59), '2F_AP03': (18.45, 11.97), '2F_AP05': (19.55, 4.26)},
        '3F': {'3F_AP01': (11.24, 2.41),'3F_AP03': (17.38, 12.13),'3F_AP05': (20.50, 3.32),'3F_AP07': (25.42, 12.97), '3F_AP09': (31.08, 4.85)},
        '4F': {'4F_AP01': (16.82, 4.96),'4F_AP03': (16.22, 12.93),'4F_AP05': (31.53, 4.70),'4F_AP07': (26.90, 13.09)},
        '5F': {'5F_AP01': (10.78, 3.11),'5F_AP03': (13.07, 12.29),'5F_AP05': (15.89, 3.18),'5F_AP07': (21.97, 12.21),'5F_AP09': (27.63, 8.02)},
        '6F': {'6F_AP01': (10.58, 14.12),'6F_AP03': (19.17, 14.40),'6F_AP05': (25.32, 14.18),'6F_AP07': (13.14, 4.25),'6F_AP09': (28.51, 6.45)},
        '7F': {'7F_AP01': (14.09, 3.31),'7F_AP03': (15.77, 12.25),'7F_AP05': (20.86, 3.33),'7F_AP07': (23.01, 12.35),'7F_AP09': (28.74, 4.07)},
        '8F': {'8F_AP01': (13.80, 3.22),'8F_AP03': (14.56, 12.04),'8F_AP05': (19.88, 3.17),'8F_AP07': (22.64, 12.11),'8F_AP09': (31.58, 3.25)},
        '9F': {'9F_AP01': (13.95, 11.37),'9F_AP03': (26.43, 4.12),'9F_AP05': (14.33, 3.80),'9F_AP07': (27.07, 11.01)},
        '10F': {'10F_AP01': (15.56, 3.99),'10F_AP03': (13.99, 12.02),'10F_AP05': (27.53, 3.01),'10F_AP07': (27.43, 12.32)}
    }
    
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
    
    # =============================================================================
    # Databases info
    MONGOIP = os.getenv('MONGOIP')
    DB = os.getenv('DB')
    COLLECTION = os.getenv('COLLECTION')
    
    # Store json data to MongoDB
    client = MongoClient(MONGOIP,27017)
    db = client[DB]
    col=db[COLLECTION]
    col.insert_many(data_json)
        
    print('Done!')
    print(dfa)
    
if __name__ == "__main__":
    main()