#!/usr/bin/env python

import os,sys
import datetime,time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mlp
from optparse import OptionParser

import timeseries

# initial settings
mlp.rcParams['axes.linewidth'] = 2

NOW = datetime.datetime.now().strftime("%m/%d/%y, %H:%M")

#---------------------------------------------------------------------------------------------------
def plot(options,figure="total",last='not-defined'):
    # define the figure
    
    plt.figure(options.name+'_'+figure)

    if   figure == "total":
        plt.plot(times,totals,marker="",ls='dashed',linewidth=1,label='total')
        plt.plot(times,dones,marker="o",ls='solid',linewidth=2,label='done')
        plt.plot(times,nocatalogs,marker="o",ls='solid',linewidth=1,label='no catalog')
        plt.plot(times,batches,marker="o",ls='solid',linewidth=1,label='in batch')
    elif figure == "batch":    
        plt.figure(options.name+'_'+figure)
        plt.plot(times,nocatalogs,marker="o",ls='dashed',linewidth=1,label='no catalog')
        plt.plot(times,batches,marker="o",ls='solid',linewidth=1,label='in batch')
        plt.plot(times,idles,marker="o",ls='solid',linewidth=1,label='idle')
        plt.plot(times,runnings,marker="o",ls='solid',linewidth=1,label='running')
        plt.plot(times,helds,marker="o",ls='solid',linewidth=1,label='held')
    
    plt.legend(frameon=False)
    plt.legend(title='ends: '+last)
    
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
    plt.subplots_adjust(top=0.99, right=0.99, bottom=0.13, left=0.12)
    
    # save plot for later viewing
    plt.savefig(options.name+'_'+figure+".png",bbox_inches='tight',dpi=400)
        
    return

#---------------------------------------------------------------------------------------------------
def readDataFromFile(file_name): 
        
    # arrays for y values
    times = []
    totals = []
    dones = []
    nocatalogs = []
    batches = []
    idles = []
    runnings = []
    helds = []
    durations = []

    # read all data in one shot
    if not options.quiet:
        print(" Open file: %s"%(file_name))
    with open(file_name,"r") as file:
        data = file.read()

    # go through each row
    for line in data.split("\n"):
        f = line.split(',')                               # use a comma to separate columns
        if len(f)>1 and len(line)>0 and line[0] != '#':   # protect against not well formatted lines
            times.append(float(f[0]))
            totals.append(float(f[1]))
            dones.append(float(f[2]))
            nocatalogs.append(float(f[3]))
            batches.append(float(f[4]))
            idles.append(float(f[5]))
            runnings.append(float(f[6]))
            helds.append(float(f[7]))
            durations.append(float(f[8]))

    return (times, totals, dones, nocatalogs, batches, idles, runnings, helds, durations)

#---------------------------------------------------------------------------------------------------
def readDataFromFiles(base): 
        
    # arrays for y values
    times = []
    totals = []
    dones = []
    nocatalogs = []
    batches = []
    idles = []
    runnings = []
    helds = []
    durations = []

    first = False
    
    for f in os.listdir(base):
        (ti,to,do,nc,ba,id,ru,he,du) = readDataFromFile("%s/%s"%(base,f))
        if first:
            first = False
            
        #print(" Length: %d -> %d"%(len(ti)))

    return (times, totals, dones, nocatalogs, batches, idles, runnings, helds, durations)

def write_plots(config,version,dataset):
    # write plots to the proper Kraken directory

    #print(" Writing plots ...")
    
    base = os.getenv('KRAKEN_AGENTS_BASE')
    logs = os.getenv('KRAKEN_AGENTS_LOG')
    
    # make the directory, copy the index file and move the plots
    if dataset == "":
        cmd  = "mkdir -p %s/reviewd/%s/%s/"%(logs,config,version)
        cmd += "; cp %s/html/index.php %s/reviewd/%s/%s/"%(base,logs,config,version)
        cmd += "; mv %s*.png %s/reviewd/%s/%s/"%(options.name,logs,config,version)
    else:
        cmd  = "mkdir -p %s/reviewd/%s/%s/%s"%(logs,config,version,dataset)
        cmd += "; cp %s/html/index-sample.php %s/reviewd/%s/%s/%s/index.php"%(base,logs,config,version,dataset)
        cmd += "; mv %s_*.png %s/reviewd/%s/%s/%s/"%(options.name,logs,config,version,dataset)
    os.system(cmd)

    return

#---------------------------------------------------------------------------------------------------
# define and get all command line arguments
parser = OptionParser()
parser.add_option("-n","--name",dest="name",default='graph_xy',help="name of input file")
parser.add_option("-q","--quiet",action="store_true",dest="quiet",default=False,help="no plot show")
parser.add_option("-w","--write",action="store_true",dest="write",default=False,help="write plots")
parser.add_option("-x","--xtitle",dest="xtitle",default='Default x title',help="x axis title")
parser.add_option("-y","--ytitle",dest="ytitle",default='Default y title',help="y axis title")
(options, args) = parser.parse_args()

(config,version) = options.name.split('-')[0:2]
dataset = "-".join(options.name.split('-')[2:])
if not options.quiet:
    print(" Config: %s  Version: %s  Dataset: %s"%(config,version,dataset))

# get my data
if dataset != '':
    ts = timeseries.Timeseries("%s/%s/%s"%(config,version,dataset))
    ts.read()
else:
    first = True
    ts = []
    #print("%s/moni/%s/%s"%(os.getenv('KRAKEN_WORK'),config,version))
    for f in os.listdir("%s/moni/%s/%s"%(os.getenv('KRAKEN_WORK'),config,version)):
        dataset_tmp = f.replace(".moni","")
        if first:
            first = False
            ts = timeseries.Timeseries("%s/%s/%s"%(config,version,dataset_tmp))
            ts.read()
            continue
        ts_tmp = timeseries.Timeseries("%s/%s/%s"%(config,version,dataset_tmp))
        ts_tmp.read()
        ts.merge("%s/%s"%(config,version),ts_tmp)
        
if len(ts.times) < 1:
    print(" WARNING - empty arrays")
    LAST = time.strftime('%m/%d/%y, %H:%M', time.localtime(int(time.time())))
else:
    LAST = time.strftime('%m/%d/%y, %H:%M', time.localtime(ts.times[-1]))

# making the plots
ts.plot(options,'total',LAST)
ts.plot(options,'batch',LAST)

if options.write:
    write_plots(config,version,dataset)

# show the plots for interactive use
if not options.quiet:
    plt.show()
