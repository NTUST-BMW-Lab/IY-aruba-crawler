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
    print('Start Positioning...')
    # Create monitoring APs coordinate dictionary from xlsx

    df = pd.read_excel('Coordinate.xlsx')

    f = df['Floor'].tolist()
    loc_iy = df.values.tolist()
    loc_iy = [[value for value in inner_list[1:] if not (isinstance(value, float) and math.isnan(value))] for inner_list in loc_iy]

    # Convert list of lists of strings to a dictionary of lists of tuples
    loc_iy = {str(f[i]): [ast.literal_eval(item) for item in inner_list] for i, inner_list in enumerate(loc_iy)}

    # Set path loss exponent (n) and reference power (a)
    n=3 # Path loss exponent
    a=-37 # Reference power for 2.4 GHz
    b=-49 # Reference power for 5 GHz

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
    # # List of bssid

    one_hour_ago = data['Datetime'][0] - timedelta(hours=1)
    data_1h = pd.DataFrame(list(mycol.find({'Datetime':{'$gte':one_hour_ago}}).sort('_id',-1)))
    data_1h = data_1h.reset_index(drop=True).drop_duplicates().drop(columns=['_id'], axis=0)

    # Calculate average RSSI in the last hour (RSSI_1h)
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

    # =============================================================================
    # RSS-based distance calculation by 2.4GHz and 5GHz

    # Separate data to 2.4 GHz and 5GHz
    pattern = r'\b(1[0-1]|[1-9])([a-zA-Z])?\b'
    mask = data['channel'].str.match(pattern)
    data24 = data[mask]
    data5 = data[~mask]

    # Calculate distance for 2.4GHz
    data24["AP01"] = data24['AP01'].apply(lambda x: Positioning_Function.calc_dist(x,a,n))
    data24["AP03"] = data24['AP03'].apply(lambda x: Positioning_Function.calc_dist(x,a,n))
    data24["AP05"] = data24['AP05'].apply(lambda x: Positioning_Function.calc_dist(x,a,n))
    data24["AP07"] = data24['AP07'].apply(lambda x: Positioning_Function.calc_dist(x,a,n))
    data24["AP09"] = data24['AP09'].apply(lambda x: Positioning_Function.calc_dist(x,a,n))

    # Calculate distance for 5GHz
    data5["AP01"] = data5['AP01'].apply(lambda x: Positioning_Function.calc_dist(x,b,n))
    data5["AP03"] = data5['AP03'].apply(lambda x: Positioning_Function.calc_dist(x,b,n))
    data5["AP05"] = data5['AP05'].apply(lambda x: Positioning_Function.calc_dist(x,b,n))
    data5["AP07"] = data5['AP07'].apply(lambda x: Positioning_Function.calc_dist(x,b,n))
    data5["AP09"] = data5['AP09'].apply(lambda x: Positioning_Function.calc_dist(x,b,n))

    data = pd.concat([data24, data5])
    data = data.sort_index()

    # =============================================================================
    # Separate APs from floors

    # Create rogue AP dataframe
    dfa = []

    #Append data of rogue APs in each floor to AP dataframe
    for i in range(len(f)):
        dfa.append(data[(data['floor'] == f[i])].reset_index(drop=True).drop_duplicates())

    # Trilateration and least squares algorithm for each AP in dfa
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

            #Create dataframe for positions and distances
            df = pd.DataFrame({'positions': positions, 'distances': distances})

            #Sort values to get the highest RSSI
            df = df.sort_values('distances').reset_index(drop=True).drop_duplicates()
            df = df.dropna()

            #Create list of position and distance from AP with highest RSSI
            positions = list(df['positions'])
            distances = list(df['distances'])

            #Calculate AP coordinates for different monitoring APs number: 3, 4, 5
            if dfa[j].loc[i]['mon AP number'] == 5:
                final = Positioning_Function.trilateration_3d_co(distances[:5], positions[:5], name) #return the coordinate axis of the rogue AP
                dfa[j].at[i, 'x5'] = final[1] #write back the coordinate axis of rogue AP to the AP dataframe
                dfa[j].at[i, 'y5'] = final[2]
                dfa[j].at[i, 'z5'] = final[3]
                final = Positioning_Function.trilateration_3d_co(distances[:4], positions[:4], name)
                dfa[j].at[i, 'x4'] = final[1]
                dfa[j].at[i, 'y4'] = final[2]
                dfa[j].at[i, 'z4'] = final[3]
                final = Positioning_Function.trilateration_2d_co(distances[:3], positions[:3], name)
                dfa[j].at[i, 'x3'] = final[1]
                dfa[j].at[i, 'y3'] = final[2]
            if dfa[j].iloc[i]['mon AP number'] == 4:
                final = Positioning_Function.trilateration_3d_co(distances[:4], positions[:4], name)
                dfa[j].at[i, 'x4'] = final[1]
                dfa[j].at[i, 'y4'] = final[2]
                dfa[j].at[i, 'z4'] = final[3]
                final = Positioning_Function.trilateration_2d_co(distances[:3], positions[:3], name)
                dfa[j].at[i, 'x3'] = final[1]
                dfa[j].at[i, 'y3'] = final[2]
            if dfa[j].loc[i]['mon AP number'] == 3:
                final = Positioning_Function.trilateration_2d_co(distances[:3], positions[:3], name)
                dfa[j].at[i, 'x3'] = final[1]
                dfa[j].at[i, 'y3'] = final[2]

    # Append every floor from dfa to a single data frame (df_final)
    df_final = dfa[0].append(dfa[1], ignore_index=True).append(dfa[2], ignore_index=True).append(dfa[3], ignore_index=True).append(dfa[4], ignore_index=True).append(dfa[5], ignore_index=True).append(dfa[6], ignore_index=True).append(dfa[7], ignore_index=True).append(dfa[8], ignore_index=True).append(dfa[9], ignore_index=True).append(dfa[10], ignore_index=True)
    df_final = df_final.rename(columns={'AP01': 'd01R', 'AP03': 'd03R', 'AP05': 'd05R', 'AP07': 'd07R', 'AP09': 'd09R'})
    df_final = df_final.reindex(columns=['floor', 'bssid', 'essid', 'channel','ap type', 'mon AP number', 'AP01R', 'AP03R', 
                                         'AP05R', 'AP07R', 'AP09R', 'd01R', 'd03R', 'd05R', 'd07R', 'd09R', 'x3', 'y3', 'x4', 'y4', 'z4', 'x5', 'y5', 'z5', 'Datetime'])
    # Add datetime to df_final
    data_json = json.loads(df_final.to_json(orient='records'))

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
    
