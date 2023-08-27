# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 00:02:25 2023
@author: Hoai-Nam Nguyen
"""

import Taiwan_Time
import Authentication
import Retrieve_RSSI
import os
from dotenv import load_dotenv
import requests
import json
import math
import pandas as pd 
from pymongo import MongoClient
from datetime import timedelta
from datetime import datetime, timedelta
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore")

# Load variables from .env file
load_dotenv()

def main():
    # =============================================================================
    # Calculate Taiwan time (GMT +8)
    
    ts, ts_tw_str, ts_tw = Taiwan_Time.calculate_taiwan_time()

    # =============================================================================
    # Decleare variables

    username = os.getenv("ACCOUNT")
    password = os.getenv("PASSWORD")
    vMM_aosip = os.getenv('vMM_aosip')
    MONGOIP = os.getenv('MONGOIP')
    ROGUEAPDB = os.getenv('ROGUEAPDB')
    ROGUEAPCOLLECTION = os.getenv('ROGUEAPCOLLECTION')
    df = pd.read_excel('AP_name.xlsx')
    print('Start RSSI Processing...')
    # =============================================================================
    # Import Aruba AP information from excel

    # Create floor list
    f = df['Floor'].tolist()

    # Create CLI input ap-name list
    IY = df.values.tolist()
    IY = [[value for value in inner_list[1:] if not (isinstance(value, float) and math.isnan(value))] for inner_list in IY]


    # =============================================================================
    # Login controller function

    token = Authentication.authentication(username,password,vMM_aosip)

    # =============================================================================
    # Retrieve and process RSSI for every floor in IY

    df0 = Retrieve_RSSI.rss_retrieve(IY[0], f[0], vMM_aosip, token)
    try:
        df1 = Retrieve_RSSI.rss_retrieve(IY[1], f[1], vMM_aosip, token)
        dfa = df0.append(df1, ignore_index=True)
    except Exception:
        pass
    try:
        df2 = Retrieve_RSSI.rss_retrieve(IY[2], f[2], vMM_aosip, token)
        dfa = dfa.append(df2, ignore_index=True)
    except Exception:
        pass
    try:
        df3 = Retrieve_RSSI.rss_retrieve(IY[3], f[3], vMM_aosip, token)
        dfa = dfa.append(df3, ignore_index=True)
    except Exception:
        pass
    try:
        df4 = Retrieve_RSSI.rss_retrieve(IY[4], f[4], vMM_aosip, token)
        dfa = dfa.append(df4, ignore_index=True)
    except Exception:
        pass
    try:
        df5 = Retrieve_RSSI.rss_retrieve(IY[5], f[5], vMM_aosip, token)
        dfa = dfa.append(df5, ignore_index=True)
    except Exception:
        pass
    try:
        df6 = Retrieve_RSSI.rss_retrieve(IY[6], f[6], vMM_aosip, token)
        dfa = dfa.append(df6, ignore_index=True)
    except Exception:
        pass
    try:
        df7 = Retrieve_RSSI.rss_retrieve(IY[7], f[7], vMM_aosip, token)
        dfa = dfa.append(df7, ignore_index=True)
    except Exception:
        pass
    try:
        df8 = Retrieve_RSSI.rss_retrieve(IY[8], f[8], vMM_aosip, token)
        dfa = dfa.append(df8, ignore_index=True)
    except Exception:
        pass
    try:
        df9 = Retrieve_RSSI.rss_retrieve(IY[9], f[9], vMM_aosip, token)
        dfa = dfa.append(df9, ignore_index=True)
    except Exception:
        pass
    try:
        df10 = Retrieve_RSSI.rss_retrieve(IY[10], f[10], vMM_aosip, token)
        dfa = dfa.append(df10, ignore_index=True)
    except Exception:
        pass

    # =============================================================================
    # Save as json format

    data_json = json.loads(dfa.to_json(orient='records'))

    # Add datetime
    for i in range(len(data_json)):
        data_json[i]['ts'] = ts 
        data_json[i]['DatetimeStr'] = ts_tw_str
        data_json[i]['Datetime'] = ts_tw

    # =============================================================================
    # Store json data to MongoDB

    client = MongoClient(MONGOIP,27017)
    db = client[ROGUEAPDB]
    col=db[ROGUEAPCOLLECTION]
    ## Set time to auto-delete MongoDB
    #previous_day = datetime.now() - timedelta(days=30) 
    # col.delete_many({"Datetime": {"$lt": previous_day}})
    col.insert_many(data_json)
    print('Done!')
    print(data_json[1])

if __name__ == "__main__":
    main()