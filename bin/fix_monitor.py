#!/usr/bin/env python
import os,sys

import jsum
import timeseries

ts1 = timeseries.Timeseries("nanoao/521/ParkingDoubleElectronLowMass5+Run2022G-PromptReco-v1+MINIAOD")
ts1.read()
#ts1.show()

ts2 = timeseries.Timeseries("nanoao/521/ParkingDoubleMuonLowMass0+Run2022C-PromptReco-v1+MINIAOD")
ts2.read()
#ts2.show()

#ts3 = timeseries.Timeseries("")
#ts3.read()
#ts3.show()

drop_times = ts1.find_droptimes(ts2)

ts1.write()
ts2.write()

config = 'nanoao'
version = '521'

for f in os.listdir("%s/moni/%s/%s"%(os.getenv('KRAKEN_WORK'),config,version)):
    if 'moni-save' in f:
        continue
    print(f)
    dataset_tmp = f.replace(".moni","")
    ts_tmp = timeseries.Timeseries("%s/%s/%s"%(config,version,dataset_tmp))
    ts_tmp.read()
    drop_times = ts1.find_droptimes(ts_tmp)
    if len(drop_times)>0:
        print(" Dropping: ")
        print(drop_times)
        ts_tmp.write()
        #sys.exit()

