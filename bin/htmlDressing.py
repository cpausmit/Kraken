#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
# Script to get a quick overview how far the production has come.
#
# Author: C.Paus                                                                      (Feb 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys,re,getopt

def getHeader(config,version):
    header = '<!DOCTYPE html><html><head><title>Kraken Production</title></head>\n' \
        + '<style>\n' \
        + 'a:link{color:#202020; background-color:transparent; text-decoration:none}\n' \
        + 'a:visited{color:#0074AA; background-color:transparent; text-decoration:none}\n' \
        + 'a:hover{color:#000090;background-color:transparent; text-decoration:underline}\n' \
        + 'a:active{color:#000040;background-color:transparent; text-decoration:underline}\n' \
        + 'body.ex{margin-top: 0px; margin-bottom:25px; margin-right: 25px; margin-left: 25px;}\n' \
        + '</style><body class="ex" bgcolor="#ffefef">\n' \
        + '<body style="font-family: arial;font-size: 20px;font-weight: bold;color:#405050;">\n' \
        + '<hr>\n<code><a href="%s-%s_batch.png"><img width=30%% src=%s-%s_batch.png></a>'%(config,version,config,version) \
        + '  <a href="%s-%s_total.png"><img width=30%% src=%s-%s_total.png></a></code>'%(config,version,config,version) \
        + '\n<hr>\n<pre>\n'
    return header

def getFooter():
    footer = '</pre></body></html>\n'
    return footer

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage = "\nUsage: htmlDressing.py [ --input=<id>  --version=<v>  --help ]\n"

# Define the valid options which can be specified and check out the command line
valid = ['input=','version=','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for this little task
# --------------------------------------------------------------------------------------------------
# Set defaults
input = ''
version = '000'

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--input":
        input = arg
    if opt == "--version":
        version = arg

# Deal with obvious problems
if input == "":
    cmd = "--input  parameter not provided. This is a required parameter."
    raise ValueError('No input was provided.')
#raise RuntimeError as cmd

# --------------------------------------------------------------------------------------------------
# Here is where the real action starts -------------------------------------------------------------
# --------------------------------------------------------------------------------------------------

# find new file name
htmlFile = input + '.html'
#print(' ASCII: ' + input)
#print(' HTML:  ' + htmlFile)

fileInput  = open(input,'r')
fileOutput = open(htmlFile,'w')
line = ' '

trunc = ''
f = input.split("/")
py = f.pop()
version = f.pop()
config = f.pop()

f = py.split("-")
type = f[0]
py = py.replace('status-','')
py = py.replace('incomplete-','')

# insert header
fileOutput.write(getHeader(config,version))

# translate the body
with open(input,"r") as fileInput:
    for line in fileInput:
        # cleanup CR
        line = line[:-1]

        # remove commented lines
        if '+' in line:
            f = line.split(' ')
            dataset = f.pop()
            line = ' '.join(f) \
                 + ' <a href="' + trunc + dataset + '">' + dataset + '</a>'
        else:
            f = line.split(' ')
            if len(f) > 1:
                v = f.pop()
                test = f.pop()
                if test == "VERSION:":
                    version = v

        if 'missing' in line:
            if type == 'status':
                line = line.replace('missing','<a href="incomplete-' + py + '.html">missing</a>')
            else:
                line = line.replace('missing','<a href="status-' + py + '.html">missing</a>')

        fileOutput.write(line+'\n')
    
    
# insert footer
fileOutput.write(getFooter())

fileInput .close()
fileOutput.close()
