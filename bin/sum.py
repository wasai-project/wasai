#!/usr/bin/python3
import threading
import time
from copy import deepcopy

import z3
z3.set_param('parallel.enable', True)
z3.set_option("parallel.threads.max", 10)

class myThread (threading.Thread):
    def __init__(self, constraint, context):
        threading.Thread.__init__(self)
        self.constraint = constraint
        self.context = context

    def run(self):
        time.sleep(1)
        constraint = self.constraint
        solver = z3.Solver(ctx=self.context)
        solver.add(self.constraint)
        _r = solver.check() == z3.sat
        self.result = solver.model() if _r else None

    def get_result(self):
        try:
            return self.result  
        except:
            return None

    
class Analysis():
    def __init__(self):
        self.queue = list()
    
    def model(self, a):
        arg = z3.BitVec(f'a_{a}', 32)
        self.queue.append(z3.And(arg < a+2, arg & 12 > 2))

def multiThread():
    traces = list(range(0, 20))
    analysis = Analysis()
    for trace in traces:
        analysis.model(trace)

    threadPool = list()
    for constraint in analysis.queue:
        i_context = z3.Context()
        i_constraint = deepcopy(constraint).translate(i_context)

        thread = myThread(i_constraint, i_context)
        thread.start()
        threadPool.append(thread)

    for thread in threadPool:  
        thread.join()  
        print(thread.get_result())

def singleThread():
    traces = list(range(0, 20))
    analysis = Analysis()
    for trace in traces:
        analysis.model(trace)

    threadPool = list()
    for constraint in analysis.queue:
        time.sleep(1)
        solver = z3.Solver()
        solver.add(constraint)
        result = solver.check() == z3.sat
        print(solver.model() if result else None)
    

def main():
    timeBegin = time.time()
    multiThread()
    print(f"[+] multiThread: {time.time() - timeBegin}s")
    print("00000")
    
    timeBegin = time.time()
    singleThread()
    print(f"[+] single: {time.time() - timeBegin}s")#0.32s


main()