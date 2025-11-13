class Atom:
    "Atomic unit of a request."
    def __init__(self,config='',version='',dataset='',file='',status=0,stime=0,etime=0,size=0):
        self.config = config
        self.version = version
        self.dataset = dataset
        self.file = file
        self.status = status
        self.stime = stime
        self.etime = etime
        self.size = size

    def update(self,config,version,dataset,file,status,stime,etime,size):
        self.config = config
        self.version = version
        self.dataset = dataset
        self.file = file
        self.status = status
        self.stime = stime
        self.etime = etime
        self.size = size
        return

    def reset(self):
        self.config = ''
        self.version = ''
        self.dataset = ''
        self.file = ''
        self.status = 0
        self.stime = 0
        self.etime = 0
        self.size = 0
        return

    def show(self,first=False):
        if first:
            print("CONFIG:VERSION:DATASET:FILE:STATUS:STIME:ETIME")
            print("==============================================")
        print(f"{self.config}:{self.version}:{self.dataset}:{self.file}:{self.status}:{self.stime}:{self.etime}:{self.size}")

    def summary(self):
        key = "%s:%s:%s:%s"%(self.config,self.version,self.dataset,self.file)
        value = "%d:%d:%d:%d"%(self.status,self.stime,self.etime,self.size)
        return key,value
               
