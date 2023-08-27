import requests
import warnings
import pandas as pd  
import math
from pymongo import MongoClient
from scipy.optimize import minimize
import Taiwan_Time
import Authentication
import Show_Command
import os
from dotenv import load_dotenv
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
    print('Start Calibrating...')
    # Login Aruba
    token = Authentication.authentication(username, password, vMM_aosip)

        
    def C_n_calibration(room, ref_aps_dict_all, token):
    
        # Input a dict of ref APs in a floor/room
        ref_aps_dict = ref_aps_dict_all[room]
        ref_aps = list(ref_aps_dict.keys())  # Extracting keys (AP names)
        ref_aps_coords = list(ref_aps_dict.values())  # Extracting values (AP coordinates)
    
        def dis_ref_ap(ref_aps, ref_aps_coords):
            # Calculate distances between APs
            distance_data = []
            for i in range(len(ref_aps_coords)):
                for j in range(i + 1, len(ref_aps_coords)):
                    distance = math.sqrt((ref_aps_coords[i][0] - ref_aps_coords[j][0])**2 + 
                                         (ref_aps_coords[i][1] - ref_aps_coords[j][1])**2)
                    distance_data.append({'i': ref_aps[i], 'j': ref_aps[j], 'd': distance})
    
            # Create DataFrame
            df_distance = pd.DataFrame(distance_data)
            return df_distance
    
        # Test result
        df_distance = dis_ref_ap(ref_aps, ref_aps_coords)
        
        def get_PL(df_distance, ref_aps, vMM_aosip, token):
    
            # Declare dict of list of Path Loss
            df_dict = {} 
    
            for ap in ref_aps:
                try:
                    command = 'show+ap+arm+state+ap-name+IY_'+ap
                    list_ap_database = Show_Command.show_command(vMM_aosip, token, command)
                    df_dict[ap] = pd.DataFrame(list_ap_database['Neighbor Data'])
                    df_dict[ap] = df_dict[ap][['Name', 'Path Loss (dB)']]
                    df_dict[ap]['Name'] = df_dict[ap]['Name'].str.replace('IY_', '', regex=False)
                    df_dict[ap] = df_dict[ap][df_dict[ap]['Name'].str.startswith('{}'.format(ap[:2]))]
                    df_dict[ap].drop_duplicates(subset='Name', keep='first', inplace=True)
                    df_dict[ap]['j'] = df_dict[ap]['Name'].str.replace('IY_', '', regex=False)
                    df_dict[ap]['i'] = ap
                    df_dict[ap].drop(columns=['Name'], inplace=True)
                except Exception:
                    pass
    
            df = pd.concat(df_dict.values(), ignore_index=True)
    
            # Create a set to keep track of pairs that have been encountered
            pair_set = set()
    
            # List to store indices to keep
            indices_to_keep = []
    
            # Iterate through rows of the final DataFrame
            for index, row in df.iterrows():
                if row['i'] in ref_aps and row['j'] in ref_aps:
                    pair = tuple(sorted([row['i'], row['j']]))
                    if pair not in pair_set:
                        pair_set.add(pair)
                        indices_to_keep.append(index)
    
            # Keep only the rows with selected indices
            df = df.loc[indices_to_keep]
    
            # Merge the filtered DataFrame with the distance DataFrame based on columns 'i' and 'j'
            df_PL = pd.merge(df, df_distance, on=['i', 'j'], how='left')
    
            # Convert 'Path Loss (dB)' column to integer
            df_PL['Path Loss (dB)'] = df_PL['Path Loss (dB)'].astype(int)
    
            # Reorder columns as 'i', 'j', 'Path Loss', 'd'
            ordered_columns = ['i', 'j', 'Path Loss (dB)', 'd']
            df_PL = df_PL[ordered_columns]
            return df_PL
    
        # Test result
        df_PL = get_PL(df_distance, ref_aps, vMM_aosip, token)
    
        ### Use known PL(d_ij) and d_ij from Aruba APs to calibrate C and n.
    
        def cal_C_n(df_PL):
            # Define path loss functions in eq. 9.
            # x[0] stands for PL(d_ij) and x[1] stands for d_ij in every two APs i,j
            def path_loss_function(x, distance):
                return x[0] + 10 * x[1] * math.log10(distance)
    
            # Define the objective function J
            def objective_function(x):
                error_sum = 0
                for distance, rssi in data:
                    estimated_rssi = path_loss_function(x, distance)
                    error_sum += (estimated_rssi - rssi) ** 2
                return error_sum
    
            # Data take only PL(d_ij), d_ij from function 1
            data = df_PL[['d', 'Path Loss (dB)']].apply(tuple, axis=1).tolist()
    
            # Minimize the objective function J
            initial_guess = [0, 0]
            result = minimize(objective_function, initial_guess)
    
            # Extract the optimized values of C and n
            C = result.x[0]
            n = result.x[1]
            return C, n
    
        C, n = cal_C_n(df_PL)
        return C, n
    
    # Dict of AP coordinate for all floor in IY building
    ref_aps_dict_all = {
        '1F': {'1F_AP01': (16.84, 13.98), '1F_AP03': (19.59, 1.51), '1F_AP05': (23.9, 9.38)},
        '2F': {'2F_AP01': (1.07, 6.59), '2F_AP03': (10.45, 11.97), '2F_AP05': (10.55, 4.26)},
        '3F': {'3F_AP01': (11.24, 2.41),'3F_AP03': (17.38, 12.13),'3F_AP05': (20.50, 3.32),'3F_AP07': (25.42, 12.97), '3F_AP09': (31.08, 4.85)},
        '4F': {'4F_AP01': (16.82, 4.96),'4F_AP03': (16.22, 12.93),'4F_AP05': (31.53, 4.70),'4F_AP07': (26.90, 13.09)},
        '5F': {'5F_AP01': (10.78, 3.11),'5F_AP03': (13.07, 12.29),'5F_AP05': (15.89, 3.18),'5F_AP07': (21.97, 12.21),'5F_AP09': (27.63, 8.02)},
        '6F': {'6F_AP01': (10.58, 14.12),'6F_AP03': (19.17, 14.40),'6F_AP05': (25.32, 14.18),'6F_AP07': (13.14, 4.25),'6F_AP09': (28.51, 6.45)},
        '7F': {'7F_AP01': (14.09, 3.31),'7F_AP03': (15.77, 12.25),'7F_AP05': (20.86, 3.33),'7F_AP07': (23.01, 12.35),'7F_AP09': (28.74, 4.07)},
        '8F': {'8F_AP01': (13.80, 3.22),'8F_AP03': (14.56, 12.04),'8F_AP05': (19.88, 3.17),'8F_AP07': (22.64, 12.11),'8F_AP09': (31.58, 3.25)},
        '9F': {'9F_AP01': (3.95, 11.37),'9F_AP03': (26.43, 4.12),'9F_AP05': (14.33, 3.80),'9F_AP07': (27.07, 11.01)},
        '10F': {'10F_AP01': (15.56, 3.99),'10F_AP03': (13.99, 12.02),'10F_AP05': (27.53, 3.01),'10F_AP07': (27.43, 12.32)}
    }
    
    # Extracting keys (AP names)
    ref_aps = list(ref_aps_dict_all.keys())  
    
    # C_n_calibration(floor, ref_aps_dict_all, token)
    
    # Create dict of C and n in each floor
    C_n_dict = {}
    
    # Loop to get C and n in each floor
    for floor in ref_aps:
        try:
            C, n = C_n_calibration(floor, ref_aps_dict_all, token)
            C_n_dict[floor] = [C, n]
        except Exception as e:
            print(f"An exception occurred for floor {floor}: {e}")
            # Skip if exception
            C_n_dict[floor] = [45, 3]
        
    print(C_n_dict)
    
    client = MongoClient(MONGOIP,27017)
    db = client[ROGUEAPDB]
    col=db["Calibration"]
    # col.delete_many({"Datetime": {"$lt": previous_day}})
    col.insert_one(C_n_dict)
    
if __name__ == "__main__":
    main()