# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 07:52:22 2023

@author: Hoai-Nam Nguyen
"""

import time
from datetime import datetime, timedelta

script_1 = __import__("Client_Data")
script_2 = __import__("AP_Data")
script_3 = __import__("Radio_Data")
script_4 = __import__("Calibration")
while (1):
    try:
        start_time = time.time()
        print("Run script 1...")
        script_1.main()
        print("Run script 2...")
        script_2.main()
        print("Run script 3...")
        script_3.main()
        print("Run script 4...")
        script_4.main()
        end_time = time.time()
        total_time = round(end_time - start_time)
        print(total_time)
        time.sleep(300-total_time)
    except:
        time.sleep(150)
