import pandas as pd 
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore")
"""
RSSI Main Script
Author: Hoai-Nam Nguyen
"""
# =============================================================================

# Datetime calculation (convert to Taiwan time GMT +8)
def calculate_taiwan_time():
    """
    Calculate the current time in Taiwan (GMT +8).
    Returns:
        ts (datetime): Current time in GMT.
        ts_tw_str (str): Current time in Taiwan in string format.
        ts_tw (datetime): Current time in Taiwan.
    """
        
    from datetime import timedelta
    from datetime import datetime, timedelta
    
    # Add datetime (GMT +8)
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z") #datetime (GMT)
    ts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fz")

    n = 8
    # Subtract 8 hours from datetime object for Taiwan time
    ts = ts - timedelta(hours=n)
    ts_tw_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_tw = datetime.now() #datetime Taiwan (GMT + 8)
    return ts, ts_tw_str, ts_tw

# Login controller functions

#Get the token to access vMM information  -- via API
def authentication(username,password,vMM_aosip):
    """
    Get the token to access vMM information via API.
    
    Args:
        username (str): Username for authentication.
        password (str): Password for authentication.
        vMM_aosip (str): vMM IP for access.
    Returns:
        uidaruba (str): Token for accessing vMM information.
    """
    url_login = "https://" + vMM_aosip + ":4343/v1/api/login"
    payload_login = 'username=' + username + '&password=' + password
    headers = {'Content-Type': 'application/json'}
    get_uidaruba = requests.post(url_login, data=payload_login, headers=headers, verify=False)

    if get_uidaruba.status_code != 200:
        print('Status:', get_uidaruba.status_code, 'Headers:', get_uidaruba.headers,'Error Response:', get_uidaruba.reason)
        uidaruba = "error"

    else:
        uidaruba = get_uidaruba.json()["_global_result"]['UIDARUBA']
        return uidaruba

#show command
def show_command(vMM_aosip,uidaruba,command):
    """
    Execute a show command.
    
    Args:
        vMM_aosip (str): vMM IP for access.
        uidaruba (str): Token for accessing vMM information.
        command (str): Command to be executed.
    Returns:
        AOS_response: Response of the executed command.
    """
    url_login = 'https://' + vMM_aosip + ':4343/v1/configuration/showcommand?command='+command+'&UIDARUBA=' + uidaruba
    aoscookie = dict(SESSION = uidaruba)
    AOS_response = requests.get(url_login, cookies=aoscookie, verify=False)
    
    if AOS_response.status_code != 200:
        print('Status:', AOS_response.status_code, 'Headers:', AOS_response.headers,'Error Response:', AOS_response.reason)
        AOS_response = 'error'

    else:
        AOS_response = AOS_response.json()
        
    return AOS_response

# Extracting floor names from AP dictionary
def get_floor_list(ref_aps_dict_all):
    """
    Extract the floor names from the AP dictionary.
    
    Args:
        ref_aps_dict_all: Dictionary containing AP information.
    Returns:
        f_name: List of floor names.
    """
    f_name = list(ref_aps_dict_all.keys()) 
    return f_name

# Exacting AP names from AP dictionary
def get_AP_name(ref_aps_dict_all):
    """
    Extract the AP names from the AP dictionary.
    
    Args:
        ref_aps_dict_all: Dictionary containing AP information.
    Returns:
        AP_name: List of AP names.
    """
    AP_name = []
    for floor, aps in ref_aps_dict_all.items():
        AP_name.append(list(aps.keys()))
    return AP_name

# Extract APs coordinate from AP dictionary
def get_AP_coords(ref_aps_dict_all, max_ap_per_floor):
    """
    Extract the coordinates of APs from the AP dictionary.
    
    Args:
        ref_aps_dict_all: Dictionary containing AP information.
        max_ap_per_floor: Maximum number of APs per floor.
    Returns:
        AP_coords: Dictionary containing AP coordinates for each floor.
    """
    AP_coords = {}
    for floor, aps in ref_aps_dict_all.items():
        AP_coords[floor] = []
        for ap, coords in aps.items():
            AP_coords[floor].append(coords)
        while len(AP_coords[floor]) < max_ap_per_floor:
            AP_coords[floor].append((None, None))
    return AP_coords

# Retrieve RSSI for reference APs in each floor
def ref_rss_retrieve(AP_name, f_name, vMM_aosip, token, building): 
    """
    Retrieve RSSI for reference APs in each floor.
    
    Args:
        AP_name: List of AP names.
        f_name: List of floor names.
        vMM_aosip (str): vMM IP for access.
        token (str): Token for accessing vMM information.
        building (str): Building name.
    Returns:
        ap_all: Dataframe containing RSSI information for reference APs.
    """
    df = {} # Initiate RSSI dataframe for a floor

    for ap in AP_name:
        command = 'show+ap+arm+state+ap-name+'+building+'_'+ap # Run CLI command to retrieve RSSI data
        list_ap_database = show_command(vMM_aosip,token,command)
        df[ap] = pd.DataFrame(list_ap_database['Neighbor Data'])
        df[ap] = df[ap].assign(
            **{'Path Loss (dB)': pd.to_numeric(df[ap]['Path Loss (dB)']),
               'channel': df[ap]['Channel/Pwr'].str.split('/').str[0],
               'Pwr': pd.to_numeric(df[ap]['Channel/Pwr'].str.split('/').str[1]),
               'RSSI (dBm)': lambda x: x['Pwr'] - x['Path Loss (dB)']
               }
        )
        df[ap].drop('Channel/Pwr', axis=1, inplace=True)
        df[ap] = df[ap].loc[df[ap]['Name'].str.contains(ap[:-1])]

    ap_int = {}
    for i in range(len(AP_name)):
        try:
            ap_int[i] = df[AP_name[i]]['IP Address']
        except Exception:
            ap_int[i] = None

    # Group all the interfering APs on a floor
    ap_int_concat = [ap_int[i] for i in range(len(AP_name))]
    ap_all_int = pd.concat(ap_int_concat).reset_index(drop=True).drop_duplicates()
    ap_all = pd.DataFrame(ap_all_int).reset_index(drop=True)

    ap_all['essid'], ap_all['ap type'], ap_all['channel'], ap_all['power'], ap_all['mon AP number']= '','valid','','', ''

    for i in range(len(AP_name)):
        try:
            ap_all[AP_name[i]] = None
        except Exception:
            pass
    # ap_all['mon AP number'] = None

    for i in range(len(ap_all)):
        no_ap = 0

        for ap in AP_name:
            try:
            # Get essid
                ap_all['essid'][i] = list(df[ap][(df[ap]['IP Address']==ap_all['IP Address'][i])]['Name'])[0]
                ap_all['power'][i] = list(df[ap][(df[ap]['IP Address']==ap_all['IP Address'][i])]['Pwr'])[0]
                ap_all['channel'][i] = list(df[ap][(df[ap]['IP Address']==ap_all['IP Address'][i])]['channel'])[0]
    #                 ap_all['mac'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['mac'])[0]
            # Get rssi
                if df[ap]['IP Address'].str.contains(ap_all['IP Address'][i]).any():
                    ap_all[ap][i] = list(df[ap][df[ap]['IP Address']==ap_all['IP Address'][i]]['RSSI (dBm)'])[0] 
                    no_ap+=1
            except Exception:
                pass
        ap_all['mon AP number'][i] = no_ap
    ap_all = ap_all[ap_all['mon AP number'] > 0].assign(floor=f_name).reset_index(drop=True).drop_duplicates()
    ap_all.columns = ap_all.columns.str.replace('IP Address', 'bssid')
    return ap_all

# Loop to retrieve RSSI for reference APs in every floor
def ref_retrieve_all(AP_name, f_name, vMM_aosip, token, building):
    """
    Loop to retrieve RSSI for reference APs in every floor.
    
    Args:
        AP_name: List of AP names.
        f_name: List of floor names.
        vMM_aosip (str): vMM IP for access.
        token (str): Token for accessing vMM information.
        building (str): Building name.
    Returns:
        dfa: Dataframe containing RSSI information for reference APs.
    """
    dfa = pd.DataFrame()

    for i in range(len(f_name)):
        try:
            df = ref_rss_retrieve(AP_name[i], f_name[i], vMM_aosip, token, building)
            dfa = dfa.append(df, ignore_index=True)
        except Exception:
            pass
    return dfa

# Retrieve RSSI for reference APs in each floor
def rogue_rss_retrieve(AP_name, f_name, vMM_aosip, token, building, threshold): 
    """
    Retrieve RSSI for rogue APs in each floor.
    
    Args:
        AP_name: List of AP names.
        f_name: List of floor names.
        vMM_aosip (str): vMM IP for access.
        token (str): Token for accessing vMM information.
        building (str): Building name.
        threshold (int): Threshold value for RSSI.
    Returns:
        ap_all: Dataframe containing RSSI information for rogue APs.
    """
    df = {} # Initiate RSSI dataframe for a floor
    
    for ap in AP_name:
        command = 'show+ap+monitor+ap-list+ap-name+'+building+'_'+ap # Run CLI command to retrieve RSSI data
        list_ap_database = show_command(vMM_aosip,token,command)
        df[ap] = pd.DataFrame(list_ap_database['Monitored AP Table'])
        df[ap]['curr-rssi'] = pd.to_numeric(df[ap]['curr-rssi'])
        df[ap] = df[ap][(df[ap]['ap-type']!='valid')][['essid','bssid','curr-rssi','ap-type', 'chan']]
        df[ap] = df[ap][(df[ap]['curr-rssi']>0)& (df[ap]['curr-rssi']<threshold)]
    print
    ap_int = {}
    for i in range(len(AP_name)):
        try:
            ap_int[i] = df[AP_name[i]]['bssid']
        except Exception:
            ap_int[i] = None

    # Group all the interfering APs on a floor
    ap_int_concat = [ap_int[i] for i in range(len(AP_name))]
    ap_all_int = pd.concat(ap_int_concat).reset_index(drop=True).drop_duplicates()
    ap_all = pd.DataFrame(ap_all_int).reset_index(drop=True)

    ap_all['essid'], ap_all['ap type'], ap_all['channel'], ap_all['power'], ap_all['mon AP number']= '','valid','','', ''

    for i in range(len(AP_name)):
        try:
            ap_all[AP_name[i]] = None
        except Exception:
            pass
    # ap_all['mon AP number'] = None

    for i in range(len(ap_all)):
        no_ap = 0

        for ap in AP_name:
            try:
            # Get essid
                ap_all['essid'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['essid'])[0]
                ap_all['ap type'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['ap-type'])[0]
                ap_all['channel'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['chan'])[0]
    #                 ap_all['mac'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['mac'])[0]
            # Get rssi
                if df[ap]['bssid'].str.contains(ap_all['bssid'][i]).any():
                    ap_all[ap][i] = -list(df[ap][df[ap]['bssid']==ap_all['bssid'][i]]['curr-rssi'])[0] 
                    no_ap+=1
            except Exception:
                pass
        ap_all['mon AP number'][i] = no_ap
    ap_all = ap_all[ap_all['mon AP number'] > 0].assign(floor=f_name).reset_index(drop=True).drop_duplicates()
#     ap_all.columns = ap_all.columns.str.replace('IP Address', 'bssid')
    return ap_all

# Loop to retrieve RSSI for rogue APs in every floor
def rogue_retrieve_all(AP_name, f_name, vMM_aosip, token, building, threshold):
    """
    Loop to retrieve RSSI for rogue APs in every floor.
    
    Args:
        AP_name: List of AP names.
        f_name: List of floor names.
        vMM_aosip (str): vMM IP for access.
        token (str): Token for accessing vMM information.
        building (str): Building name.
        threshold (int): Threshold value for RSSI.
    Returns:
        dfa: Dataframe containing RSSI information for rogue APs.
    """
    dfa = pd.DataFrame()

    for i in range(len(f_name)):
        try:
            df = rogue_rss_retrieve(AP_name[i], f_name[i], vMM_aosip, token, building, threshold)
            dfa = dfa.append(df, ignore_index=True)
        except Exception:
            pass
    return dfa
