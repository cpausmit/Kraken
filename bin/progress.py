from time import sleep
import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BgGreen = '\033[42m\033[30m'

sys.stdout.write(bcolors.BgGreen+' '+bcolors.ENDC)
print " "

#sys.stdout.write(REVERSE + CYAN)
#print "From now on change to cyan, in reverse mode"
#print "NOTE: 'CYAN + REVERSE' wouldn't work"

#
#blank = bcolors.WARNING + " " + bcolors.ENDC
#
#for i in range(21):
#    sys.stdout.write('\r')
#    sys.stdout.write("[%-20s] %d%%" % (blank*i, 5*i))
#    sys.stdout.flush()
#    sleep(0.25)
#
#print
