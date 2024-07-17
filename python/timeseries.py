import os
import datetime,time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mlp
from optparse import OptionParser

import jsum

BASE = "%s/moni"%(os.getenv('KRAKEN_WORK'))
EXT = "moni"
NOW = datetime.datetime.now().strftime("%m/%d/%y, %H:%M")

class Timeseries:
    "Time series of job summaries."
    def __init__(self,key):
        self.key = key
        self.times = []
        self.jsums = []

    def get_totals(self):
        totals = []
        for time,jsum in zip(self.times,self.jsums):
            totals.append(jsum.n_total)
        return totals

    def get_dones(self):
        dones = []
        for time,jsum in zip(self.times,self.jsums):
            dones.append(jsum.n_done)
        return dones

    def get_nocatalogs(self):
        nocatalogs = []
        for time,jsum in zip(self.times,self.jsums):
            nocatalogs.append(jsum.n_nocatalog)
        return nocatalogs

    def get_batches(self):
        batches = []
        for time,jsum in zip(self.times,self.jsums):
            batches.append(jsum.n_batch)
        return batches

    def get_idles(self):
        idles = []
        for time,jsum in zip(self.times,self.jsums):
            idles.append(jsum.n_idle)
        return idles

    def get_runnings(self):
        runnings = []
        for time,jsum in zip(self.times,self.jsums):
            runnings.append(jsum.n_running)
        return runnings

    def get_helds(self):
        helds = []
        for time,jsum in zip(self.times,self.jsums):
            helds.append(jsum.n_held)
        return helds

    def add(self,time,jsum):
        if len(self.times) == 0 or time>self.times[-1]:
            self.times.append()
        else:
            print("ERROR - time is attached out of order (last: %d, this: %d)"%(times[-1],time))
            return -1
        self.jsums.append(jsum)

    def read(self):
        with open("%s/%s.%s"%(BASE,self.key,EXT),"r") as file:
            data = file.read()

        # go through each row
        for line in data.split("\n"):
            f = line.split(',')                               # use a comma to separate columns
            if len(f)>1 and len(line)>0 and line[0] != '#':   # protect against not well formatted lines
                self.times.append(int(f[0]))
                self.jsums.append(jsum.Jsum(f[1:]))    

    def write(self):
        filename = "%s/%s.%s"%(BASE,self.key,EXT)
        print(" Write file: %s"%(filename))
        with open(filename,"w") as f:
            for time,jsum in zip(self.times,self.jsums):
                f.write("%d,%s\n"%(time,jsum.string()))

    def show(self):
        print(" Key - %s"%(self.key))
        for time,jsum in zip(self.times,self.jsums):
            print("%d,%s"%(time,jsum.string()))

    def drop(self,times):
        new_times = []
        new_jsums = []
        for time,jsum in zip(self.times,self.jsums):
            if time not in times:
                new_times.append(time)
                new_jsums.append(jsum)
            else:
                #print(" Dropping time: %d"%(time))
                pass
        self.times = new_times
        self.jsums = new_jsums
        return
    
    def merge(self,key,ts):
        if len(self.times) !=  len(ts.times):
            #print(" ERROR - time series have different length (this %d vs added %d)"%(len(self.times),len(ts.times)))
            pass
            #return 1

        i = 0
        drop_times = []
        for time,jsum in zip(self.times,self.jsums):
            if len(ts.times)>i:
                if len(ts.times)>i and time != ts.times[i]:
                    #print(" ERROR - (%s,%s)"%(self.key,ts.key))
                    #print("       time series out of sync (this %d vs added %d)"%(time,ts.times[i]))
                    while (time>ts.times[i]):
                        #print(" WARNING - Ignore new record (%d)."%(ts.times[i]))
                        i += 1
                        if i>len(ts.times)-1:
                            break
                    if (len(ts.times)<=i):
                        print(f" ERROR - index: {i} ({len(ts.times)}")
                    if (time<ts.times[i]):
                        #print(" WARNING - Drop existing record (%d)."%(time))
                        drop_times.append(time) # keep record of what needs to be dropped
                        continue
                jsum.merge(ts.jsums[i])
            i += 1

        self.drop(drop_times)
                
        # last update the key
        self.key = key

        return 0

    def find_droptimes(self,ts,remove=True):

        #if len(self.times) !=  len(ts.times):
        #    print(" WARNING - time series have different length (this %d vs added %d)"%(len(self.times),len(ts.times)))

        i = 0
        drop_times = []

        for time,jsum in zip(self.times,self.jsums):

            if i>=len(ts.times):
                #print(" WARNING - Drop existing record (%d)."%(time))
                drop_times.append(time)
                i += 1
                continue
            
            if time != ts.times[i]:
                #print(" ERROR - (%s,%s)"%(self.key,ts.key))
                #print("       time series out of sync (this %d vs added %d)"%(time,ts.times[i]))
                while (time>ts.times[i]):
                    print(" WARNING - Ignore new record (%d)."%(ts.times[i]))
                    drop_times.append(ts.times[i])   # keep record of what needs to be dropped
                    i += 1
                    if i>len(ts.times)-1:
                        print("STOP")
                        break
                if (time<ts.times[i]):
                    print(" WARNING - Drop existing record (%d)."%(time))
                    drop_times.append(time)          # keep record of what needs to be dropped
                    continue
            i += 1

        if remove:
            self.drop(drop_times)
            ts.drop(drop_times)
            
        return drop_times

    def plot(self,options,figure="total",last='not-defined'):
        # define the figure

        ts = [datetime.datetime.fromtimestamp(p) for p in self.times]      
        
        plt.figure(options.name+'_'+figure)
        fig = plt.gcf()
        fig.set_size_inches(7,6)
    
        if   figure == "total":
            plt.plot(ts,self.get_totals(),marker="",ls='dashed',linewidth=1,label='total')
            plt.plot(ts,self.get_dones(),marker=".",ls='solid',linewidth=2,label='done')
            plt.plot(ts,self.get_nocatalogs(),marker="o",ls='solid',linewidth=1,label='no catalog')
            plt.plot(ts,self.get_batches(),marker="s",ls='solid',linewidth=1,label='in batch')
        elif figure == "batch":    
            plt.figure(options.name+'_'+figure)
            plt.plot(ts,self.get_nocatalogs(),marker=".",ls='dashed',linewidth=1,label='no catalog')
            plt.plot(ts,self.get_batches(),marker="o",ls='solid',linewidth=1,label='in batch')
            plt.plot(ts,self.get_idles(),marker="s",ls='solid',linewidth=1,label='idle')
            plt.plot(ts,self.get_runnings(),marker="^",ls='solid',linewidth=1,label='running')
            plt.plot(ts,self.get_helds(),marker="v",ls='solid',linewidth=1,label='held')
        
        plt.legend(title='ends: '+last, frameon=False, fontsize="14")
        
        plt.xticks(rotation=20, ha='right')
        plt.gca().xaxis.set_major_formatter(mlp.dates.DateFormatter('%m/%d %H:%M'))
        #plt.rcParams.update({'font.size': 18})
        ax = plt.gca()
        ax.annotate(NOW, xy=(-0.13,0),xycoords=('axes fraction','figure fraction'),
                    size=10, ha='left', va='bottom')
        #ax.annotate('ends: '+last, xy=(0.99,0.01), xycoords=('axes fraction','axes fraction'),
        #            size=10, ha='right', va='bottom')
        
        # make plot nicer
        plt.xlabel(options.xtitle, fontsize=18)
        plt.ylabel(figure+' '+options.ytitle, fontsize=18)
        
        # make axis tick numbers larger
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        
        # make sure to noe have too much white space around the plot
        plt.subplots_adjust(top=0.99, right=0.99, bottom=0.18, left=0.18)
        #plt.subplots_adjust(top=0.99, right=0.99, bottom=0.13, left=0.12)
        
        # save plot for later viewing
        plt.savefig(options.name+'_'+figure+".png",bbox_inches='tight',dpi=400)

        return
 
# # define and get all command line arguments
# parser = OptionParser()
# parser.add_option("-n","--name",dest="name",default='graph_xy',help="name of input file")
# parser.add_option("-q","--quiet",action="store_true",dest="quiet",default=False,help="no plot show")
# parser.add_option("-x","--xtitle",dest="xtitle",default='Default x title',help="x axis title")
# parser.add_option("-y","--ytitle",dest="ytitle",default='Default y title',help="y axis title")
# (options, args) = parser.parse_args()
#    
# ts1 = Timeseries("nanoao/518/BcToJPsiMuMu_inclusive_TuneCP5_13TeV-bcvegpy2-pythia8-evtgen+RunIISummer20UL16MiniAOD-106X_mcRun2_asymptotic_v13-v3+MINIAODSIM")
# ts1.read()
# ts1.show()
# 
# ts2 = Timeseries("nanoao/518/BcToJPsiMuMu_inclusive_TuneCP5_13TeV-bcvegpy2-pythia8-evtgen+RunIISummer20UL17MiniAOD-106X_mc2017_realistic_v6-v3+MINIAODSIM")
# ts2.read()
# ts2.show()
# 
# ts3 = Timeseries("nanoao/518/BsToMuMu_SoftQCDnonD_TuneCP5_BsLifetime1p45_13TeV-pythia8-evtgen+RunIISummer20UL18MiniAOD-106X_upgrade2018_realistic_v11_L1v1-v1+MINIAODSIM")
# ts3.read()
# ts3.show()
# 
# ts1.merge("nanoao/518",ts2)
# ts1.merge("nanoao/518",ts3)
# ts1.show()
# ts1.write()
# 
# ts1.plot(options)
