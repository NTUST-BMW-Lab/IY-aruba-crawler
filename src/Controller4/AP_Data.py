# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 16:16:14 2022

@author: Hoai-Nam
"""
import os
from dotenv import load_dotenv
import datetime
from pymongo import MongoClient
from datetime import timedelta
import login_Aruba
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
import json

# Load variables from .env file
load_dotenv()

def main():
    # =============================================================================

    # Add datetime (GMT +8) and timestamp

    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    ts = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fz")
    ts
    n = 8
    # Subtract 8 hours from datetime object
    ts = ts - timedelta(hours=n)
    ts_tw_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_tw = datetime.datetime.now()
    # =============================================================================

    # MongoDB Database & Collection

    mongoip = os.environ.get("MONGOIP")
    database = os.environ.get("APDATABASE")
    collection = os.environ.get("APCOLLECTION")

    # =============================================================================

    # Aruba API account & password

    account = os.environ.get("ACCOUNT")
    password = os.environ.get("PASSWORD")
    Controller_url = os.environ.get("CONTROLLER_URL")

    # =============================================================================

    # Login to Aruba

    url, headers, chartData, res_data, cookieStr = login_Aruba.login(account, password, Controller_url)

    # Retrieve and parse AP data

    url = Controller_url+'/screens/cmnutil/execUiQuery.xml'
    headers = {'Content-Type': 'text/plain'}
    cookie = {"SESSION":cookieStr}
    payloadData = 'query=<aruba_queries><query><qname>backend-observer-ap-42</qname><type>list</type><list_query><device_type>ap</device_type><requested_columns>ap_name ap_eth_mac_address ap_group ap_deployment_mode ap_model ap_serial_number ap_ip_address ap_status ap_state_reason ap_provisioned ap_uptime lms_ip ap_active_aac ap_standby_aac ap_cluster_name ap_cur_dual_5g_mode ap_tri_radio_mode radio_count total_data_bytes sta_count ssid_count ap_datazone role pcap_on green_state mesh_role mesh_cluster_name mesh_portal_ap_mac mesh_portal_name mesh_parent_ap_mac mesh_parent_name mesh_uplink_time mesh_uplink_age mesh_child_num</requested_columns><sort_by_field>sta_count</sort_by_field><sort_order>desc</sort_order><pagination><start_row>0</start_row><num_rows>200</num_rows></pagination></list_query><filter><global_operator>and</global_operator><filter_list><filter_item_entry><field_name>ap_status</field_name><comp_operator>equals</comp_operator><value><![CDATA[1]]></value></filter_item_entry><filter_item_entry><field_name>role</field_name><comp_operator>equals</comp_operator><value><![CDATA[1]]></value></filter_item_entry></filter_list></filter></query></aruba_queries>&UIDARUBA='+cookieStr

    res = requests.post(url, verify=False, headers = headers, cookies = cookie, data = payloadData.encode('utf-8'))

    soup = BeautifulSoup(res.text, 'html.parser')
    header_tags = soup.find_all('header')
    row_tags=soup.find_all('row')


    # =============================================================================

    # Rearrange DataFrame

    df=pd.DataFrame()
    index=0

    for values in row_tags:

        data=values.find_all('value')
        data_total=[]

        time_stamp =int(time.time())
        struct_time = time.localtime(time_stamp) 
        timeString = time.strftime("%Y-%m-%d-%H-%M", struct_time) 
        data_total.append(time_stamp)

        for i in range(len(data)):

            data_total.append(data[i].text)

        index+=1
        df[index]=data_total

    # =============================================================================

    # Add header to dataframe

    for values in header_tags:
        Header_Data=[] 
        Header_Data.append('time_stamp')
        column_name=values.find_all('column_name')
        for i in range(len(column_name)) :
            Header_Data.append(column_name[i].text)

    df.index=Header_Data
    df=df.T
    df.reset_index(drop=True, inplace=True)
    df = df[df['ap_name'].str.contains('IY')]
    df = df[['ap_name','sta_count','ap_ip_address','ap_eth_mac_address','ap_status','ap_deployment_mode','ap_model','ap_group']]
    df1 = df



    # =============================================================================

    # create json: df[] => data_json

    data_json = json.loads(df.to_json(orient='records'))

    for i in range(len(data_json)):
        try:
            data_json[i]['sta_count'] = int(data_json[i]['sta_count']) # Convert str to int
            data_json[i]['ap_status'] = int(data_json[i]['ap_status'])
            data_json[i]['ap_provisioned'] = int(data_json[i]['ap_provisioned'])
            data_json[i]['ap_uptime'] = int(data_json[i]['ap_uptime'])
            data_json[i]['ap_deployment_mode'] = int(data_json[i]['ap_deployment_mode'])
            data_json[i]['ap_model'] = int(data_json[i]['ap_model'])
        except Exception:
            pass
        data_json[i]['ts'] = ts 
        data_json[i]['DatetimeStr'] = ts_tw_str
        data_json[i]['Datetime'] = ts_tw
    data_json[1]

    # =============================================================================

    # Store json data to MongoDB

    client = MongoClient(mongoip,27017)
    db = client[database]
    col=db[collection]
    col.insert_many(data_json)
    print('Done')

if __name__ == "__main__":
    main()