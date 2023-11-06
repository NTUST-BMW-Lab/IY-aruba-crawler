New folder updated: "positioning_update". 

So far this folder includes 2 files: "RSSI_function" and "RSSI_retrieve".

The "RSSI_function" is used to initialize all the functions used for retrieving RSSI.

The "RSSI_retrieve" is used to declare the input and run the RSSI retrieval program.

In "RSSI_retrieve", the input is the login info (username, password, IP), the building name, and the AP dictionary (floor, AP name, coordinate). 

The AP dictionary (floor, AP name, coordinate) is stored as "AP_dict" in json file. You can download the file for IY building here:

https://drive.google.com/file/d/1EHds9mhtqhlU7bHwo4AcIkzQll9-NWIx/view?usp=sharing

If you want to implement in D1 or other building, you can change the detail from AP_dict accordingly.

Please let me know if you want to get the username, password, IP address for IY or D1 building in "RSSI_retrieve".

Demo video:

https://youtu.be/RDZ1K9jTeOs

Video of login and run WiFi files:

https://youtu.be/SxyfTSvkGyY
