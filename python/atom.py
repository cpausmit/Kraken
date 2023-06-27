class Atom:
    "Atomic unit of a request."
    def __init__(self,config='',version='',dataset='',file='',status=0,time=0):
        self.config = config
        self.version = version
        self.dataset = dataset
        self.file = file
        self.status = status
        self.time = status

    def update(self,config,version,dataset,file,status,time):
        self.config = config
        self.version = version
        self.dataset = dataset
        self.file = file
        self.status = status
        self.time = time
        return

    def reset(self):
        self.config = ''
        self.version = ''
        self.dataset = ''
        self.file = ''
        self.status = 0
        self.time = 0
        return

    def show(self,first=False):
        if first:
            print("CONFIG:VERSION:DATASET:FILE:STATUS:TIME")
            print("========================================")
        print("%s:%s:%s:%s:%d:%d"%(self.config,self.version,self.dataset,self.file,self.status,self.time))

    def summary(self):
        key = "%s:%s:%s:%s"%(self.config,self.version,self.dataset,self.file)
        value = "%d:%d"%(self.status,self.time)
        return key,value
               
