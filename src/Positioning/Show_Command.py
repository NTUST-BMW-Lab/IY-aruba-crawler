#show command via Aruba API

import Authentication
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def show_command(aosip,uidaruba,command):
    url_login = 'https://' + aosip + ':4343/v1/configuration/showcommand?command='+command+'&UIDARUBA=' + uidaruba
    aoscookie = dict(SESSION = uidaruba)
    AOS_response = requests.get(url_login, cookies=aoscookie, verify=False)
    
    if AOS_response.status_code != 200:
        print('Status:', AOS_response.status_code, 'Headers:', AOS_response.headers,'Error Response:', AOS_response.reason)
        AOS_response = 'error'

    else:
        AOS_response = AOS_response.json()
        
    return AOS_response

username=os.environ.get("ACCOUNT") # Aruba controller username
password=os.environ.get("PASSWORD") # Aruba controller password
aosip = os.environ.get("CONTROLLER_URL") # Aruba controller URL
uidaruba = Authentication.authentication(username,password, aosip)
command = 'show+time-range'

print(show_command(aosip,uidaruba,command))
