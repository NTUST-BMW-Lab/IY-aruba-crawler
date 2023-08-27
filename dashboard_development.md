# Dashboard Development

After [pushing MongoDB data to Dashboard](https://github.com/nguyennam2010/RSSIIY/blob/main/README.md#c-query-data-from-databases-to-wise-paas), this is how you develop the Dashboard.

## Method
Two main methods in Dashboard development: Direct (MongoDB - Dashboard) and indirect visualization (MongoDB - DataHub - SaaS Composer - Dashboard).

![image](https://github.com/nguyennam2010/RSSIIY/assets/102983698/2401a8a3-e246-4d68-8822-f23c9e9197de)

## Variables

Create variables for AP and floor.

![01](https://github.com/nguyennam2010/RSSIIY/assets/102983698/22058ec8-5692-4185-aba2-1b65819c9cfd)


## AP information

- Query:

```
db.Controller_4.aggregate([
{"$sort":{"ts":-1, "Client":-1}},
{"$match": {"AP Name":"$ap", "ts":{ "$gte" : "$from"}}}, 
{"$project": {"_id":0,"AP Name":"$AP Name", "Client":"$Client","IP Address":"$IP address","MAC Address":"$MAC address","Model":"$Model","AP Group":"$AP_Group", "TW Time":"$DatetimeStr"}},
{"$limit":1}
            ])
```
Note: In this query, ```Controller_4``` is the collection of the AP database, which named ```Aruba_AP```. The query is same as you query data in your MongoDB. 

- Result:

![02](https://github.com/nguyennam2010/RSSIIY/assets/102983698/a09b211c-33ed-4666-86b6-2665ee9db4a2)


## Client number

- Query (2.4 GHz):

```
db.AP_List.aggregate([
{"$match": {"ap_name":"$ap","radio_band": 0, "ts":{ "$gte" : "$from", "$lt":"$to"}}}, 
{"$project": {"_id":0, "name":"2.4 GHz", "ap_name":"$ap", "value":"$sta_count","ts":"$ts"}}
            ])
```
Note: You need to Add Query to query 5GHz, then it can show in the map together as the pic below.

- Result:

![03](https://github.com/nguyennam2010/RSSIIY/assets/102983698/3fab722b-c8cd-4320-8ccf-31e0ada1d0e2)


## Noise floor
- Query (5 GHz):

```
db.AP_List.aggregate([
{"$match": {"ap_name":"IY_1F_AP01","radio_band":1,  "ts":{ "$gte" : "$from", "$lt":"$to"}}}, 
{"$project": {"_id":0,"name":"5 GHz", "value":"$noise_floor","ts":"$ts"}}
            ])
```

- Result:

![04](https://github.com/nguyennam2010/RSSIIY/assets/102983698/960534b2-20f5-4372-afdd-c6691e2e10e4)


## Channel utilization
- Query (2.4 GHz - tx time):

```
db.AP_List.aggregate([
{"$match": {"ap_name":"$ap","radio_band": 0, "ts":{ "$gte" : "$from", "$lt":"$to"}}}, 
{"$project": {"_id":0, "name":"tx time", "value":"$tx_time","ts":"$ts"}}
            ])
```
- Result:

![05](https://github.com/nguyennam2010/RSSIIY/assets/102983698/02db0e81-a0ea-42a2-b458-22adbf2ed9b3)


## Client information

- Query:

```
db.Controller_4.aggregate([
{"$sort":{"ts":-1, "Client":-1}},
{"$match": {"ap_name":"$ap", "ts":{ "$gte" : "$from", "$lt":"$to"}}}, 
{"$project": {"_id":0,"Client User Name":"$client_user_name", "MAC Address":"$sta_mac_address","IP Address":"$client_ip_address","OS":"$client_dev_type","WLAN":"$ssid","AP Name":"$ap","Client Health":"$client_health", "Radio Band":"$radio_band","Channel":"$channel","SNR":"$snr","TW Time":"$DatetimeStr"}},
{"$limit":100}
])
```

- Result:

![06](https://github.com/nguyennam2010/RSSIIY/assets/102983698/f4e88179-e9b7-4418-981a-2a8ac6a5a41f)


## Client map

To visualize as map in Dashboard, you need to push your data to DataHub.

First, you need to download SDK code from [WISE-PaaS documentation](https://docs.wise-paas.advantech.com/en/Guides_and_API_References/Data_Acquisition/DataHub/py_Edge_SDK_Manual/v1.1.7)

Their code for random data generation:

![image](https://github.com/nguyennam2010/RSSIIY/assets/102983698/c77899be-7ef4-423a-ac4c-d67b36c1ddd4)

You need to adjust the above code to connect to DataHub. For example, push AP name and Client number from MongoDB:

![08](https://github.com/nguyennam2010/RSSIIY/assets/102983698/2b754e42-e9e8-4139-9645-94ee5af6d608)


Then you can push the data to DataHub follow this video: https://www.youtube.com/watch?v=IP46vcWuHhY

Now you edit Composer to bind the data to the map. Create appropriate assets and bind the corresponding data from DataHub:

![09](https://github.com/nguyennam2010/RSSIIY/assets/102983698/a961c912-a397-4544-987e-d23d37bbafb4)


Use advanced setting to change color of the Client nodes:

![010](https://github.com/nguyennam2010/RSSIIY/assets/102983698/7665bc20-bf1d-408f-be93-0b44021bbc21)


```
function(value, oldValue, option){ 
    if(value>=10) return "symbols/builtIn/large transformer/red light.json";
    if(value<10 & value>2) return "symbols/builtIn/large transformer/yellow light.json";
    if(value<=2) {value=0;return "symbols/builtIn/large transformer/green light.json";}
    else return "symbols/builtIn/large transformer/green light.json";}
```

- Now the map can show number of clients and color corresponding to the data.
    - Green light: < 2 users (clients)
    - Yellow light: 2 < users < 10
    - Red light: > 10 users

In Dashboard, create a panel, choose SaaS Composer-Viewer and choose the SaaS Composer directory to the file setting:

![011](https://github.com/nguyennam2010/RSSIIY/assets/102983698/656bde70-bb0a-43d4-a145-66cbadd9d6b7)



## Interference map

Same as Client map, you import the IY building map to SaaS Composer and bind their (x, y) variables.

![012](https://github.com/nguyennam2010/RSSIIY/assets/102983698/fdb3ab37-25d9-48ab-aed5-a1ef6ceabe3e)

In Dashboard, create a panel for Interference Map and choose the directory same as Client Map.









