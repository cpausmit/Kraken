## Private Monte Carlo Samples - NANOAODSIM (no MINIAODSIM --> fake them)

### Copy them to the right location

A location consistent with other samples should be the Tier-2.

    /cms/store/user/paus/nanosu/A01/SUEP-m125-md2-t2-generic-htcut+RunIIAutumn18-private+MINIAODSIM

### Make a catalog

To make sure the files can be used in the system they have to be cataloged. This does not yet check the event numbers!!

    catalogPrivateNanos.sh /cms/store/user/paus/nanosu/A01/SUEP-m125-md2-t2-generic-htcut+RunIIAutumn18-private+MINIAODSIM
      --> catalog/t2mit/nanosu/A01/SUEP-m125-md2-t2-generic-htcut+RunIIAutumn18-private+MINIAODSIM/RawFiles.00

Now we need to fake the 'presumed' MINIAODSIM input files:

    process:   SUEP-m125-md2-t2-generic-htcut
    setup:     RunIIAutumn18-private
    data tier: MINIAODSIM

    mkdir -p catalog/t2mit/mc/SUEP-m125-md2-t2-generic-htcut/RunIIAutumn18-private/MINIAODSIM/
    cp       catalog/t2mit/nanosu/A01/SUEP-m125-md2-t2-generic-htcut+RunIIAutumn18-private+MINIAODSIM/RawFiles.00 \
             catalog/t2mit/mc/SUEP-m125-md2-t2-generic-htcut/RunIIAutumn18-private/MINIAODSIM
    cd       catalog/t2mit/mc/SUEP-m125-md2-t2-generic-htcut/RunIIAutumn18-private/MINIAODSIM
    repstr   nanosu/A01/SUEP-m125-md2-t2-generic-htcut+RunIIAutumn18-private+MINIAODSIM \
             mc/SUEP-m125-md2-t2-generic-htcut/RunIIAutumn18-private/MINIAODSIM \
	     RawFiles.00
	     
    # this last step makes sure that the faked MINIAODSIM inputs are in the database and can be used to compare event numbers
    
    addDataset.py --exec --dataset /mc/SUEP-m125-md2-t2-generic-htcut/RunIIAutumn18-private/MINIAODSIM
    addRequest.py --config nanosu --version A01 --py nano \
                         --dataset /mc/SUEP-m125-md2-t2-generic-htcut/RunIIAutumn18-private/MINIAODSIM

Now we can check the NANOAODSIM files with respect to their faked inputs. So, run checkFile.py on each file in the directory to update the database. The should also generate the catalog.


## Private Monte Carlo Samples - MINIAODSIM

### Copy them to the right location

A convenient location could be the Tier-2 it could also be the Tier-3 but Tier-2 is prefered.

    /cms/store/user/paus/mc

Now add process, setup and tier as separate subdirectories.

Example:

    process:   SUEP-m400-md2-t0.5-generic
    setup:     RunIIAutumn18-private
    data tier: MINIAODSIM

Files are in:

    /cms/store/user/paus/mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM

### Make a catalog (and LFNS and JOBS)

To make sure the files can be used in the system they have to be cataloged.

    catalogPrivateMc.sh /cms/store/user/paus/mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM
      --> catalog/t2mit/mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM.00

### Add a processing request

Now the dataset can be added to the Kraken database. This is not explicitely needed because adding a request of a nw dataset will automatically also add the data to the database, but it it a good step to check whether it works.

    addData.py --dataset /mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM

Finally add you request to the Kraken request table.

    addRequest.py --config nanosu --version A01 --py nano \
                  --dataset /mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM

### Requesting a Sample

Instead of just submitting your sample, which you could with submitCondor.py and many parameters, it is recommended to add a request to the database. This might seem painful initially but it enables a whole slew of automation, including monitoring.

* addRequest.py --dbs local --config slimmr --version 000 --py fake --dataset pandaf=002=SinglePhoton+Run2016H-03Feb2017_ver3-v1+MINIAOD

The sample we request is not an officical CMS sample (dbs) but a local Panda sample. It derives from the official CMS sample SinglePhoton+Run2016H-03Feb2017_ver3-v1+MINIAOD and was derived using the pandaf configuration with version 002 as inidcated in the full dataset name.
The dataset properties will be stored when you request the dataset so make sure it is complete at this time. If you want to go back, you can re-declare the sample which will update the database, but be careful, the output of the same previously requested sample should be carefully removed to avoid event overlaps as several input files are combined into one output file and the definitions are likely not the same anymore. The input for the job splitting comes from the catalogs (one fileset one job).

### Submitting a job standalone

There is no need to request the sample through the database and you can go head and submit a sample production interactively. To submit your jobs running on the local Panda sample as specified above just do this:

* submitCondor.py --noCleanup --dbs=local --py=fake --config=slimmr --version=000 --dataset=pandaf=002=SinglePhoton+Run2016H-03Feb2017_ver3-v1+MINIAOD

The submission is safe as far as already submitted or completed jobs concerns. They are accounted for in the submission process and only what is not completed or not queued will be submitted.

