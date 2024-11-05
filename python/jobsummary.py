from enum import Enum

class js(Enum):
    IDLE = 1
    RUNNING = 2
    REMOVED = 3
    COMPLETED = 4
    HELD = 5
    TRANSFERING= 6
    SUSPENDED = 7

class Jobsummary:
    "Status summary of submitted job(s) for a given request."
    def __init__(self,key,n_total,n_done,n_nocatalog):
        self.key = key
        self.run_time = 0
        self.n_total = n_total
        self.n_done = n_done
        self.n_nocatalog = n_nocatalog
        self.n_batch = 0
        self.n_idle = 0
        self.n_running = 0
        self.n_removed = 0
        self.n_completed = 0
        self.n_held = 0

    def add_job(self,jobstatus,runtime):
        self.n_batch += 1
        if   jobstatus == js.IDLE.value:
            self.n_idle += 1
        elif jobstatus == js.RUNNING.value:
            self.n_running += 1
            self.run_time += runtime
        elif jobstatus == js.REMOVED.value:
            self.n_removed += 1
        elif jobstatus == js.COMPLETED.value:
            self.n_completed += 1
        elif jobstatus == js.HELD.value:
            self.n_held += 1
           
        return

    def is_active(self):
        return (self.n_nocatalog+self.n_batch+self.n_idle+self.n_running+self.n_held>0)
    
    def show(self,first):
        if first:
            print("TOTAL  DONE NOCAT BATCH  IDLE  RUN HELD  RT[hr] -- Request")
            print("============================================================")
        rtime = 0
        if self.n_running>0:
            rtime = self.run_time/3600./self.n_running
        print("%5d %5d %5d %5d %5d %4d %4d %7.1f -- %4s"\
              %(self.n_total,self.n_done,self.n_nocatalog,
                self.n_batch,self.n_idle,self.n_running,self.n_held,rtime,self.key))
        
    def summary_string(self):
        rtime = 0
        if self.n_running>0:
            rtime = self.run_time/3600./self.n_running
        return "%d,%d,%d,%d,%d,%d,%d,%f"\
            %(self.n_total,self.n_done,self.n_nocatalog,
              self.n_batch,self.n_idle,self.n_running,
              self.n_held,rtime)

    def merge(self,merged_key,js):
        self.key = merged_key
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
        self.n_removed += js.n_removed
        self.n_completed += js.n_completed
        self.n_held += js.n_held

        return
