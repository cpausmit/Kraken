import MySQLdb
import fileIds
class Kdb:
    "Kraken Data Base."
    
    def __init__(self,debug=0):
        # Access the database to determine all requests
        self.db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
        self.cursor = self.db.cursor()
        self.debug = debug

    def find_requests(self,config,version,py=''):
        # find all requests for a given set of config/version/py
        
        sql = 'select ' + \
            'Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,Datasets.DatasetDbsInstance,Datasets.DatasetNFiles,RequestConfig,RequestVersion,RequestPy,RequestId,RequestNFilesDone ' + \
            'from Requests left join Datasets on Requests.DatasetId = Datasets.DatasetId ' + \
            'where RequestConfig="' + config + '" and RequestVersion = "' + version
        if py != "":
            sql += '" and RequestPy = "' + py
        sql += '" order by Datasets.DatasetProcess, Datasets.DatasetSetup, Datasets.DatasetTier;'

        return self._execute_sql(sql)
        
    def find_files_done(self,config,version,dataset):
        # find all requests for a given set of config/version/dataset
        
        f = dataset.split('+') # decode the dataset
        process = f[0]
        setup = f[1]
        tier = f[2]

        sql = "select FileName, NEvents from Files inner join Requests on " \
            + " Files.RequestId = Requests.RequestId inner join Datasets on " \
            + " Requests.DatasetId = Datasets.DatasetId where " \
            + " DatasetProcess='%s' and DatasetSetup='%s' and DatasetTier='%s'"%(process,setup,tier) \
            + " and RequestConfig='%s' and RequestVersion='%s'"%(config,version)

        results = []
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
        except:
            print('ERROR(%s) - could not find request id.'%(sql))
    
        # found the request Id
        catalogedIds = fileIds.fileIds()
        for i,row in enumerate(results):
            fileId = row[0]
            nEvents = int(row[1])
            catalogedId = fileIds.fileId(fileId,nEvents)
            catalogedIds.addFileId(catalogedId)
    
        return catalogedIds
        
    def _execute_sql(self,sql):
        # execute a given SQL
        if self.debug > 0:
            print(' SQL: ' + sql)
            
        results = []
        try:
            # Execute the SQL command
            self.cursor.execute(sql)
            results = self.cursor.fetchall()      
        except:
            print(" ERROR (%s): unable to fetch data."%(sql))

        return results
