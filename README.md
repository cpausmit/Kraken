## Kraken

Kraken is a processing tool that allows the user to run on either official CMS data/MC samples or on locally produced Panda files. It uses a number of other packages and relies on a database to manage requests and the output files.

## Private Monte Carlo Samples

### Copy them to a convenient location

A convenient location could be the Tier-2 it could also be the Tier-3 but Tier-2 is prefered.



## Installation

* clone git://github.com/cpausmit/Kraken
* edit the ./Kraken/setup.sh file to match your specific setup
* source ./Kraken/setup.sh

## Running independent test job interactively




## Typical use for Panda file production

### Install your own code

* export KRAKEN_CMSSW=$HOME/cms/cmssw

To properly version your output/code use a three digit number starting from '000' to '999' which will be used subsequently to make sure the right code is selected and data is stored depending on the version number. So, install the code for example in $KRAKEN_CMSSW/000.

The tar ball later created for the submission will pack up your bin/ lib/ src/ python/ so you can use all of that.

### Execution Script

export KRAKEN_SCRIPT=releaseKraken.sh

This script is what condor executes. Release Kraken is fairly general and should allow you to do what you need to do. It would be a good idea to not change the script, but of course you can, and you can edit releaseKraken.sh to your likings, but be careful, damage can be done.

### Executable

export KRAKEN_EXE=slimmer

The executable that is used inside the execution script can be freely specified. Best is to place it in the bin directory in your CMSSW release area because that will be in your path automatically.


### Requesting a Sample

Instead of just submitting your sample, which you could with submitCondor.py and many parameters, it is recommended to add a request to the database. This might seem painful initially but it enables a whole slew of automation, including monitoring.

* addRequest.py --dbs local --config slimmr --version 000 --py fake --dataset pandaf=002=SinglePhoton+Run2016H-03Feb2017_ver3-v1+MINIAOD

The sample we request is not an officical CMS sample (dbs) but a local Panda sample. It derives from the official CMS sample SinglePhoton+Run2016H-03Feb2017_ver3-v1+MINIAOD and was derived using the pandaf configuration with version 002 as inidcated in the full dataset name.
The dataset properties will be stored when you request the dataset so make sure it is complete at this time. If you want to go back, you can re-declare the sample which will update the database, but be careful, the output of the same previously requested sample should be carefully removed to avoid event overlaps as several input files are combined into one output file and the definitions are likely not the same anymore. The input for the job splitting comes from the catalogs (one fileset one job).

### Submitting a job standalone

There is no need to request the sample through the database and you can go head and submit a sample production interactively. To submit your jobs running on the local Panda sample as specified above just do this:

* submitCondor.py --noCleanup --dbs=local --py=fake --config=slimmr --version=000 --dataset=pandaf=002=SinglePhoton+Run2016H-03Feb2017_ver3-v1+MINIAOD

The submission is safe as far as already submitted or completed jobs concerns. They are accounted for in the submission process and only what is not completed or not queued will be submitted.

## Status

