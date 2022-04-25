import sys
import os
import json
import hashlib
import re

from genEvil.utils import injectTupleProto
from genEvil.injectWasm import injectNotif as genVulWasm
from genEvil.injectWasm import getWasmBody, parse, caseAuth

from genEvil.lava import InjectMemFault # OOB


def process_bar(percent, start_str='', end_str='', total_length=0):
    bar = ''.join(["\033[31m%s\033[0m"%'###'] * int(percent * total_length)) + ''
    bar = '\r' + start_str + bar.ljust(total_length) + ' {:0>4.1f}%|'.format(percent*100) + end_str
    print(bar, end='', flush=True)


def inject(rawPath, injectTuple):
    print(rawPath)
    os.system(f"eosio-wasm2wast {rawPath} > raw.wat")
    with open("raw.wat", 'r') as f:
        raw = f.read().strip()
    evil = genVulWasm(raw, injectTuple)

    with open('temp.wat', 'w') as f:
        f.write(evil)

    if 0 != os.system(f"eosio-wast2wasm temp.wat -o temp.wasm"):
        raise Exception("ERROR eosio-wast2wasm")



# def reduceCoverage(rawPath, funcID={'apply': -1, 'transfer':-1}):
#     # print("start")
#     os.system(f"eosio-wasm2wast {rawPath} > raw.wat")
#     with open("raw.wat", 'r') as f:
#         raw = f.read().strip()

#     evil = "(module\n"
#     body = getWasmBody(raw)
#     for t in parse(body):
#         if not t.strip().startswith('(func'):
#             evil += t
#         else:
#             contents = t.split('\n')
#             fid = int(re.search(r";(\d+);", contents[0]).group(1))

#             if fid == funcID['apply']:
#                 # obfuscate magic number
#                 newContents = list()
#                 idx = 0 
#                 while idx < len(contents) - 1:
#                     if contents[idx].strip() == 'get_local 2' and \
#                         contents[idx+1].strip() == 'i64.const -3617168760277827584':

#                         newContents.append('get_local 2')
#                         newContents.append('get_local 2')
#                         newContents.append('i64.popcnt')
#                         newContents.append('i64.const -3617168760277827607')
#                         newContents.append('i64.add')
#                         idx += 2
#                         continue

#                     else:
#                         newContents.append(contents[idx])
#                         idx += 1
#                 newContents.append(contents[-1])
#                 contents = newContents

            
#             elif fid == funcID['transfer']:
#                 for idx, line in enumerate(contents):
#                     if not line.strip().startswith('('):
#                         break
#                 code  = "(if (i64.ne (get_local 3)  (i64.load) (i64.const 100000) ) (then   (unreachable) ) )\n" 
#                 code += "(if (i64.ne (get_local 3) (i64.load offset=8) (i64.const 1397703940) ) (then  (unreachable) ) )\n"
#                 contents = contents[:idx] + [code] + contents[idx:]

#             evil += '\n'.join(contents) 
#     evil += ')'
#     with open('temp.wat', 'w') as f:
#         f.write(evil)

#     if os.system(f"eosio-wast2wasm temp.wat -o temp.wasm") != 0:
#         raise Exception("eosio-wast2wasm Error")

def main():
    if len(sys.argv) != 5:
        print('Usage: %s <path_to_fuzzer\'s output> <path_to_save_injected> <mode> <cnt=-1>' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)
    base = sys.argv[1]
    target = sys.argv[2]
    mode = int(sys.argv[3])
    cnt = int(sys.argv[4])

    if mode not in (0,1,2,3):
        print('Error Mode with', mode)
        exit(-1)

    # ======================= Injecting ==========================
    fuzzingContracts = os.listdir(base)[:cnt]
    threshold = len(fuzzingContracts)
    _idx = 0
    os.system(f"mkdir -p {target} && rm -r {target}/*")
    for contract in fuzzingContracts:
        # if contract != "betsandbacca":
        #     continue

        process_bar(_idx/(threshold), start_str='', end_str="100%", total_length=15)
        _idx += 1
        
        contractDir = os.path.join(base, contract)
        if not os.path.exists(os.path.join(contractDir, 'report.json')):
            continue
        with open(os.path.join(contractDir, 'report.json'), 'r') as f:
            report = json.load(f)
    
        rawAbiPath  = os.path.join(contractDir, report['name'], '*.abi')
        rawWasmPath = os.path.join(contractDir, '*.wasm')

        if mode == 0:
            targetContractDir = os.path.join(target, report['name'])
            # inject [fake eos]
            if not report["lava_eos"]:
                continue

            bug = 'drop\ndrop\ni32.const ' + ('1' if report["lava_eos"][2] == 'i64.eq' else '0')
            bug += '\n'
            injectTuple = injectTupleProto(func=report["lava_eos"][0], offset=report["lava_eos"][1], code=bug)
            try:
                inject(os.path.join(contractDir, '*.wasm'), injectTuple)
            except:
                print("ERROR =>", contractDir)

            # injected successfully
            os.system(f"mkdir -p {targetContractDir} && " + \
                    f"mv temp.wasm {os.path.join(targetContractDir, report['name']+'.wasm')} && " +\
                    f"cp {rawAbiPath} {os.path.join(targetContractDir, report['name'] + '.abi')}")

        elif mode == 1:
            targetContractDir = os.path.join(target, report['name'])
            # inject [fake notif]/[fake eos]
            if not report["lava_notif"]:
                continue
            
            # xor
            bug = '\ndrop\ndrop\ni32.const ' + ('0' if report["lava_notif"][2] == 'i64.ne' else '1')
            bug += '\n'
            injectTuple = injectTupleProto(func=report["lava_notif"][0], offset=report["lava_notif"][1], code=bug)
            
            try:
                inject(os.path.join(contractDir, '*.wasm'), injectTuple)
            except:
                print("ERROR =>", contractDir)
  
            # injected successfully
            os.system(f"mkdir -p {targetContractDir} && " + \
                    f"mv temp.wasm {os.path.join(targetContractDir, report['name']+'.wasm')} && " +\
                    f"cp {rawAbiPath} {os.path.join(targetContractDir, report['name'] + '.abi')}")

        elif mode == 2:
            # inject OOB
            _bs = os.path.join(contractDir, 'pLogs')
            logs = [os.path.join(_bs, p) for p in os.listdir(_bs) if p.split('_')[1][0] == '0']
            
            if logs:
                client = InjectMemFault(threshold=4, group=16)
                oobReports = client.run(report['name'], rawWasmPath, rawAbiPath, logs) # save in tmpDir
                if oobReports:
                    # report[0] : (actionFID, offset, clen), evilName, cmd
                    for _, evilName, _ in oobReports:
                        targetContractDir = os.path.join(target, evilName.split('.wasm')[0])
                        os.system(f"mkdir -p {targetContractDir} && " +  
                                f"mv {os.path.join(client.RESPATH, evilName)} {os.path.join(targetContractDir, report['name']+'.wasm')} && " + 
                                f"cp {rawAbiPath} {os.path.join(targetContractDir, report['name']+'.abi')}")
       
        elif mode == 3:
            # inject pm
            targetContractDir = os.path.join(target, report['name'])
            os.system(f"eosio-wasm2wast {os.path.join(contractDir, '*.wasm')} > raw.wat")
            with open("raw.wat", 'r') as f:
                raw = f.read().strip()
            try:
                caseAuth(raw)
            except:
                continue

            os.system(f"mkdir -p {targetContractDir} && " + \
                    f"mv temp.wasm {os.path.join(targetContractDir, report['name']+'.wasm')} && " +\
                    f"cp {rawAbiPath} {os.path.join(targetContractDir, report['name'] + '.abi')}")





main()
