import json
import threading
import z3

class EOSPonserException(Exception):
    def __init__(self,err='cannot find eosponser'):
        Exception.__init__(self,err)
        

def num1bits(x):
    count=0
    while x:
        count += 1
        x = x & (x - 1)
    return count

def getBBFuncId(bbname):
    return int(bbname.split('_')[1], 16)

def format_bb_name(function_id, offset):
    return ('block_%x_%x' % (function_id, offset))

def buildArgs(args, types):
    tmp = []
    idx = 0
    alen = types.count('I32') + types.count('I64') * 2
    realArgs = args[len(args)-alen:]
    for t in types:
        # print(t, idx)
        if t == 'I32':
            tmp.append(realArgs[idx])
            idx += 1
        elif t =='I64':
            arg1 = realArgs[idx]
            arg2 = realArgs[idx+1]
            tmp.append((arg2<<32) | arg1)
            idx += 2
    return args[:len(args)-alen] + tmp

class Logger():
    def __init__(self, _path):
        self.path = _path
        
    def log(self, content):
        with open(self.path, 'w') as f:
            f.write(str(content))

def process_bar(percent, start_str='', end_str='', total_length=0):
    bar = ''.join(["\033[31m%s\033[0m"%'   '] * int(percent * total_length)) + ''
    bar = '\r' + start_str + bar.ljust(total_length) + ' {:0>4.1f}%|'.format(percent*100) + end_str
    print(bar, end='', flush=True)
 
    # for i in range(101):
    #     time.sleep(0.1)
    #     end_str = '100%'
    #     process_bar(i/100, start_str='', end_str=end_str, total_length=15)
 

class myThread (threading.Thread):
    def __init__(self, constraint, context):
        threading.Thread.__init__(self)
        self.constraint = constraint
        self.context = context

    def run(self):
        constraint = self.constraint
        solver = z3.Solver(ctx=self.context)
        solver.add(self.constraint)
        _r = solver.check() == z3.sat
        self.result = solver.model() if _r else [None]
        # print("[-] multi thread:", "res:", _r, "c:", self.constraint, "==\n")

    def get_result(self):
        try:
            return self.result  
        except:
            return [None]
