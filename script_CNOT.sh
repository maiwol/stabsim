#!/bin/bash

time python latt_surg_test_MC.py 0.002 0.002 0.002 31250 8 False 
time python latt_surg_test_MC.py 0.005 0.005 0.005 5000 8 False 
time python latt_surg_test_MC.py 0.008 0.008 0.008 2000 8 False 
time python latt_surg_test_MC.py 0.008 0.008 0.008 2000 8 True
time python latt_surg_test_MC.py 0.001 0.001 0.001 125000 8 False 
time python latt_surg_test_MC.py 0.001 0.001 0.001 125000 8 True
time python latt_surg_test_MC.py 0.0008 0.0008 0.0008 200000 8 False 
time python latt_surg_test_MC.py 0.0008 0.0008 0.0008 200000 8 True
