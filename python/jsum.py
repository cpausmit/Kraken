from enum import Enum

class js(Enum):
    IDLE = 1
    RUNNING = 2
    REMOVED = 3
    COMPLETED = 4
    HELD = 5
    TRANSFERING= 6
    SUSPENDED = 7

class Jsum:
    "Summary of submitted job(s) for a given request."
    def __init__(self,f = [0,0,0,0,0,0,0,0]):
        self.n_total = float(f[0])
        self.n_done = float(f[1])
        self.n_nocatalog = float(f[2])
        self.n_batch = float(f[3])
        self.n_idle = float(f[4])
        self.n_running = float(f[5])
        self.n_held = float(f[6])
        self.run_time = float(f[7])
        return

    def set_totals(self,n_total,n_done,n_nocatalog):
        self.n_total = n_total
        self.n_done = n_done
        self.n_nocatalog = n_nocatalog
        return
    
    def add_job(self,jstat,runtime):
        self.n_batch += 1
        if   jstat == js.IDLE.value:
            self.n_idle += 1
        elif jstat == js.RUNNING.value:
            self.n_running += 1
            self.run_time += runtime
        elif jstat == js.HELD.value:
            self.n_held += 1
        return

    def show(self,key='',first=False):
        if first:
            print("TOTAL  DONE NOCAT BATCH  IDLE  RUN HELD  RT[hr] -- Key")
            print("======================================================")
        rtime = 0
        if self.n_running>0:
            rtime = self.run_time/3600./self.n_running
        print("%5d %5d %5d %5d %5d %4d %4d %7.1f -- %s"\
              %(self.n_total,self.n_done,self.n_nocatalog,
                self.n_batch,self.n_idle,self.n_running,self.n_held,rtime,key))
        
    def string(self):
        rtime = 0
        if self.n_running>0:
            rtime = self.run_time/3600./self.n_running
        return "%d,%d,%d,%d,%d,%d,%d,%f"\
            %(self.n_total,self.n_done,self.n_nocatalog,
              self.n_batch,self.n_idle,self.n_running,
              self.n_held,rtime)

    def merge(self,js):
        sum = self.n_running + js.n_running
        if sum > 0:
            self.run_time = self.n_running/sum * self.run_time + js.n_running/sum * js.run_time
        else:
            self.run_time = 0.
        self.n_total += js.n_total
        self.n_done += js.n_done
        self.n_nocatalog += js.n_nocatalog
        self.n_batch += js.n_batch
        self.n_idle += js.n_idle
        self.n_running += js.n_running
        self.n_held += js.n_held
        return
