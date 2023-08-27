   
import Taiwan_Time
import Positioning_Function
import os
from dotenv import load_dotenv
import requests
import json
import pandas as pd 
import warnings
import ast
import math
import pymongo
from pymongo import MongoClient
from datetime import timedelta
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore")

# Load variables from .env file
load_dotenv()

# Simplified path loss model
def calc_dist_cal(rssi,C,n, P_i):
    cal_d= pow(10,((P_i - C - rssi)/(10*n)))
    return cal_d
    
def main():
    # =============================================================================
    # Calculate Taiwan time (GMT +8)

    ts, ts_tw_str, ts_tw = Taiwan_Time.calculate_taiwan_time()

    # =============================================================================
    # Initiate variables

    MONGOIP = os.environ.get("MONGOIP") # MongoDB IP address
    ROGUEAPDB = os.environ.get("ROGUEAPDB") # RogueAP database
    ROGUEAPCOLLECTION = os.environ.get("ROGUEAPCOLLECTION") # Rogue AP collection
    COORDINATECOLLECTION = os.environ.get("COORDINATECOLLECTION") # Coordinate collection
    print(COORDINATECOLLECTION)
    # Create monitoring APs coordinate dictionary from xlsx

    df = pd.read_excel('Coordinate.xlsx')

    f = df['Floor'].tolist()
    loc_iy = df.values.tolist()
    loc_iy = [[value for value in inner_list[1:] if not (isinstance(value, float) and math.isnan(value))] for inner_list in loc_iy]

    # Convert list of lists of strings to a dictionary of lists of tuples
    loc_iy = {str(f[i]): [ast.literal_eval(item) for item in inner_list] for i, inner_list in enumerate(loc_iy)}

    # Assume that tx power in rogue APs = 15 dBm
    P_i = 15
    # =============================================================================

    # create a MongoDB client instance

    myclient = pymongo.MongoClient(MONGOIP,27017)
    mydb = myclient[ROGUEAPDB]
    mycol = mydb[ROGUEAPCOLLECTION]
    data = pd.DataFrame(list(mycol.find().sort('_id',-1).limit(1)))
    data['Datetime'][0]
    data = pd.DataFrame(list(mycol.find({'DatetimeStr':data['DatetimeStr'][0]}).sort('_id',-1)))
    data = data.reset_index(drop=True).drop_duplicates().drop(columns=['_id'], axis=0)
    data = data[(data['mon AP number']) > 2].reset_index(drop=True).drop_duplicates()
    
    from datetime import timedelta
    
    # Query data in the previous 1h
    one_hour_ago = data['Datetime'][0] - timedelta(hours=1)
    data_1h = pd.DataFrame(list(mycol.find({'Datetime':{'$gte':one_hour_ago}}).sort('_id',-1)))
    data_1h = data_1h.reset_index(drop=True).drop_duplicates().drop(columns=['_id'], axis=0)
    
    # Calculate RSSI_1h 
    data_mean = data_1h.groupby(['bssid'], as_index=False).agg({'essid': 'first', 'AP01': 'mean', 'AP03': 'mean', 'AP05': 'mean', 'AP07': 'mean', 'AP09': 'mean',  'channel': 'first', 'ap type': 'first', 'floor':'first','Datetime':'first'})
    cols_to_count = ['AP01', 'AP03','AP05','AP07','AP09']
    data_mean['mon AP number'] = data_mean[cols_to_count].notna().sum(axis=1)
    
    # Write back to data
    data = data_mean[data_mean['bssid'].isin(list(data['bssid']))]
    
    # Save RSSI_1h as AP01R, AP03R, AP05R, AP07R, AP09R
    
    data["AP01R"] = data['AP01']
    data["AP03R"] = data['AP03']
    data["AP05R"] = data['AP05']
    data["AP07R"] = data['AP07']
    data["AP09R"] = data['AP09']
    
    data = data.reset_index(drop=True).drop_duplicates()
    
    # # =============================================================================
    # Query calibrated C and n from MongoDB
    myclient = pymongo.MongoClient(MONGOIP,27017)
    mydb = myclient[ROGUEAPDB]
    mycol = mydb["Calibration"]
    Cn = pd.DataFrame(list(mycol.find().sort('_id',-1).limit(1)))
    
    # Calculate distance from path loss model using the calibrated C and n
    for i in f[:10]:
        C, n = Cn[i][0]
        data.loc[data['floor'] == i, "AP01"] = data[data['floor'] == i]["AP01R"].apply(lambda x: calc_dist_cal(x, C, n, P_i))
        data.loc[data['floor'] == i, "AP03"] = data[data['floor'] == i]["AP03R"].apply(lambda x: calc_dist_cal(x, C, n, P_i))
        data.loc[data['floor'] == i, "AP05"] = data[data['floor'] == i]["AP05R"].apply(lambda x: calc_dist_cal(x, C, n, P_i))
        data.loc[data['floor'] == i, "AP07"] = data[data['floor'] == i]["AP07R"].apply(lambda x: calc_dist_cal(x, C, n, P_i))
        data.loc[data['floor'] == i, "AP09"] = data[data['floor'] == i]["AP09R"].apply(lambda x: calc_dist_cal(x, C, n, P_i))
    
    # =============================================================================
    # Separate APs from floors
    
    dfa = []
    dfa.append(data[(data['floor'] == '1F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '2F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '3F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '4F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '5F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '6F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '7F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '8F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '9F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '10F')].reset_index(drop=True).drop_duplicates())
    dfa.append(data[(data['floor'] == '11F')].reset_index(drop=True).drop_duplicates())
    
    # 2D-trilateration and least squares algorithm for indoor localization
    for j in range(len(dfa)):
        for i in range(len(dfa[j])):
            # Interfering AP name (essid). If essid is none, replace by "-"
            if dfa[j].iloc[i]['essid'] == None:
                name = '-'
            else:
                name = dfa[j].iloc[i]['essid']
    
            # Define the positions of the reference points
            positions = loc_iy[dfa[j]['floor'][0]]
            
            # Define the distances between the object and the reference points
            distances = [dfa[j].iloc[i]['AP01'], dfa[j].iloc[i]['AP03'], dfa[j].iloc[i]['AP05'], dfa[j].iloc[i]['AP07'], dfa[j].iloc[i]['AP09']]
    
            #Create dataframe
            df = pd.DataFrame({'positions': positions, 'distances': distances})
    
            #Sort values
            df = df.sort_values('distances').reset_index(drop=True).drop_duplicates()
            df = df.dropna()
            
            #Calculate AP coordinates for 3 APs, 4 APs, 5 APs
            positions = list(df['positions'])
            distances = list(df['distances'])
            final = Positioning_Function.trilateration_2d_co(distances[:3], positions[:3], name)
            dfa[j].at[i, 'x3'] = final[1]
            dfa[j].at[i, 'y3'] = final[2]
            dfa[j].at[i, 'z3'] = 2.74
    
    df_final = dfa[0].append(dfa[1], ignore_index=True).append(dfa[2], ignore_index=True).append(dfa[3], ignore_index=True).append(dfa[4], ignore_index=True).append(dfa[5], ignore_index=True).append(dfa[6], ignore_index=True).append(dfa[7], ignore_index=True).append(dfa[8], ignore_index=True).append(dfa[9], ignore_index=True).append(dfa[10], ignore_index=True)
    df_final = df_final.rename(columns={'AP01': 'd01R', 'AP03': 'd03R', 'AP05': 'd05R', 'AP07': 'd07R', 'AP09': 'd09R'})
    df_final = df_final.reindex(columns=['floor', 'bssid', 'essid', 'channel','ap type', 'mon AP number', 'AP01R', 'AP03R', 
                                         'AP05R', 'AP07R', 'AP09R', 'd01R', 'd03R', 'd05R', 'd07R', 'd09R', 'x3', 'y3', 'z3', 'Datetime'])
    # Add datetime
    data_json = json.loads(df_final.to_json(orient='records'))
    
    from datetime import timedelta
    from datetime import datetime, timedelta
    
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    ts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fz")
    ts
    n = 8
    # Subtract 8 hours from datetime object
    ts = ts - timedelta(hours=n)
    ts_tw_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_tw = datetime.now()
    
    for i in range(len(data_json)):
        data_json[i]['ts'] = ts 
        data_json[i]['DatetimeStr'] = ts_tw_str
        data_json[i]['Datetime'] = ts_tw
    # =============================================================================
    
    # Save to databases
    
    #previous_day = datetime.now() - timedelta(days=30) 
    
    client = MongoClient(MONGOIP,27017)
    db = client[ROGUEAPDB]
    col=db[COORDINATECOLLECTION]
    # col.delete_many({"Datetime": {"$lt": previous_day}})
    col.insert_many(data_json)
    print('Done!')
    print(data_json[0])
    
if __name__ == "__main__":
    main()