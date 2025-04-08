class Atom:
    "Atomic unit of a request."
    def __init__(self,config='',version='',dataset='',file='',status=0,stime=0,etime=0):
        self.config = config
        self.version = version
        self.dataset = dataset
        self.file = file
        self.status = status
        self.stime = stime
        self.etime = etime

    def update(self,config,version,dataset,file,status,stime,etime):
        self.config = config
        self.version = version
        self.dataset = dataset
        self.file = file
        self.status = status
        self.stime = stime
        self.etime = etime
        return

    def reset(self):
        self.config = ''
        self.version = ''
        self.dataset = ''
        self.file = ''
        self.status = 0
        self.stime = 0
        self.etime = 0
        return

    def show(self,first=False):
        if first:
            print("CONFIG:VERSION:DATASET:FILE:STATUS:STIME:ETIME")
            print("==============================================")
        print(f"{self.config}:{self.version}:{self.dataset}:{self.file}:{self.status}:{self.stime}:{self.etime}")

    def summary(self):
        key = "%s:%s:%s:%s"%(self.config,self.version,self.dataset,self.file)
        value = "%d:%d:%d"%(self.status,self.stime,self.etime)
        return key,value
               
