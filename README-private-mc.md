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
    addData.py --exec --dataset /mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM
    addRequest.py --config nanosu --version A01 --py nano \
                  --dataset /mc/SUEP-m400-md2-t0.5-generic/RunIIAutumn18-private/MINIAODSIM

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
