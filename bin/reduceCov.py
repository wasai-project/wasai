import sys
import os
import json
import re

from genEvil.injectWasm import getWasmBody, parse 

def process_bar(percent, start_str='', end_str='', total_length=0):
    bar = ''.join(["\033[31m%s\033[0m"%'###'] * int(percent * total_length)) + ''
    bar = '\r' + start_str + bar.ljust(total_length) + ' {:0>4.1f}%|'.format(percent*100) + end_str
    print(bar, end='', flush=True)


def findMap(cbase):    
    def typeSwitcher(tp):
        tp = str(tp)
        switcher = {
            'float32':'F32',
            'double':'F64'
        }
        _t = re.search('^[u]*int(\d+)$', tp)
        if _t:
            tlen = int(_t.group(1))
            if tlen <= 32:
                return 'I32'
            else:
                return 'I64'
        elif tp in switcher:
            return switcher[tp]
        elif tp == 'asset':
            return 'asset'
        else:
            return ''
    template = {
            'I32' : "\n(if (i32.eq (get_local {0}) (i32.const 123) ) (then unreachable))\n",
            'I64' : "\n(if (i64.eq (get_local {0}) (i64.const 123456) ) (then unreachable))\n",
            'F32' : "\n(if (f32.lt (get_local {0}) (f32.const 11.2) (f32.sub) (f32.abs) (f32.const 0.001) ) (then unreachable))\n",
            'F64' : "\n(if (f64.lt (get_local {0}) (f64.const 123.5) (f64.sub) (f64.abs) (f64.const 0.001) ) (then unreachable))\n",
        }
    with open(f"{cbase}/actPartly.txt", 'r') as f:
        line = f.readline().split()
        applyFuncId, eosponserFuncId = int(line[0]), int(line[1])

    _guard  = "\n(if (i64.ne (get_local 3)  (i64.load) (i64.const 100000) ) (then   (unreachable) ) )\n" 
    _guard += "\n(if (i64.ne (get_local 3) (i64.load offset=8) (i64.const 1397703940) ) (then  (unreachable) ) )\n"
    reduceMap = {applyFuncId: "###", eosponserFuncId:  '###' + _guard}
    return reduceMap
    '''
    -------------------------
    ------------------------
    '''

    # print(applyFuncId, eosponserFuncId)
    # exit()
    # obfuscate other actions
    _bs = os.path.join(cbase, 'pLogs')
    logs = [os.path.join(_bs, p) for p in os.listdir(_bs) if p.split('_')[1][0] == '0']
    
    actMap = dict()
    for log in logs:
        with open(log, 'r') as f:
            (traces, actLinePos), types, _, cleosCmd = json.load(f)
        actName = cleosCmd.split(' ')[4]
        if actName in actMap:
            continue
        
        if actLinePos == -1:
            continue
        
        # light filter
        if len(traces[actLinePos][3]) == len(types):
            actMap[actName] = (traces[actLinePos+2][2][0], types)
        # print(traces[actLinePos-1], traces[actLinePos], traces[actLinePos+1], traces[actLinePos+2], types)
        if len(actMap.keys()) > 8:
            break

    
    # print(f'[-] processing apply, {applyFuncId}')
    for actName, (actFid, types) in actMap.items():
        # print(f'[-] processing [{actName}],{actFid}, {types}')

        if actFid in (applyFuncId, eosponserFuncId):
            continue

        # only inject one guard condition
        guard = ""
        for localIdx, rawtp in enumerate(types):
            tp = typeSwitcher(rawtp)
            if tp in template:
                guard = template[tp].format(localIdx+1)
                # print(f"[-] inject: {rawtp}, {guard}")
                break
            elif tp == 'asset':
                guard  = f"(if (i64.ne (get_local {localIdx+1})  (i64.load) (i64.const 100000) ) (then (unreachable) ) )\n" 
                guard += f"(if (i64.ne (get_local {localIdx+1}) (i64.load offset=8) (i64.const 1397703940) ) (then (unreachable) ) )\n"
                # print(f"[-] inject: {tp}, {guard}")
                break

        if guard:
            reduceMap[actFid] = guard
                
    return reduceMap


# advanced
def reduceCoverage(rawPath, reduceMap):
    injected = False
    
    # print("start")
    os.system(f"eosio-wasm2wast {rawPath} > raw.wat")
    with open("raw.wat", 'r') as f:
        raw = f.read().strip()

    evil = "(module\n"
    body = getWasmBody(raw)
    for t in parse(body):
        if t[:5].strip().startswith('(func'):
            fid = int(re.search(r";(\d+);", t.split('\n', 1)[0]).group(1))
            if fid in reduceMap:
                # APPLY
                if reduceMap[fid] == "###":
                    contents = t.split('\n')
                    # apply() : obfuscate magic number
                    newContents = ""
                    idx = 0 
                    isWritedAct = False
                    isWritedCode = False
                    isOpaquePredict = False
                    while idx < len(contents) - 1:
                        if not isOpaquePredict and not contents[idx].strip().startswith('('):
                            sig = int(re.search(r"\(type (\d+)\)", t.split('\n', 1)[0]).group(1))
                            # opaque predict
                            newContents += f"(if (i64.eq (get_local 1) (i64.const -4060558379637014528 ) ) (then get_local 0 get_local 1 get_local 2 (call {fid} )) )\n"
                            
                            # Opaque Input
                            # for _i in range(3):
                            #     newContents += f'''get_local {_i}
                            #                     i64.const 32
                            #                     i64.shr_u
                            #                     i32.wrap/i64

                            #                     get_local {_i}
                            #                     i64.const 33
                            #                     i64.shr_u
                            #                     i32.wrap/i64
                            #                     i32.const 1533916891
                            #                     i32.and
                            #                     i32.sub
                            #                     get_local {_i}
                            #                     i64.const 34
                            #                     i64.shr_u
                            #                     i32.wrap/i64
                            #                     i32.const 153391689
                            #                     i32.and
                            #                     i32.sub
                            #                     tee_local 3
                            #                     i32.const 3
                            #                     i32.shr_u
                            #                     get_local 3
                            #                     i32.add
                            #                     i32.const -954437177
                            #                     i32.and
                            #                     i32.const 63
                            #                     i32.rem_u
                            #                     get_local {_i}
                            #                     i32.wrap/i64
                            #                     tee_local 3
                            #                     get_local 3
                            #                     i32.const 1
                            #                     i32.shr_u
                            #                     i32.const 1533916891
                            #                     i32.and
                            #                     i32.sub
                            #                     get_local 3
                            #                     i32.const 2
                            #                     i32.shr_u
                            #                     i32.const 153391689
                            #                     i32.and
                            #                     i32.sub
                            #                     tee_local 3
                            #                     i32.const 3
                            #                     i32.shr_u
                            #                     get_local 3
                            #                     i32.add
                            #                     i32.const -954437177
                            #                     i32.and
                            #                     i32.const 63
                            #                     i32.rem_u
                            #                     i32.add
                            #                     i64.extend_u/i32
                                                
                            #                     get_local {_i}
                            #                     i64.add 
                            #                     get_local {_i}
                            #                     i64.popcnt
                            #                     i64.sub 
                            #                     set_local {_i}\n'''

                            isOpaquePredict = True
                            

                        # if (not isWritedAct) and (contents[idx].strip() == 'get_local 2' and \
                        #     contents[idx+1].strip() == 'i64.const -3617168760277827584'):
                        #     # obfuscate rtValue
                        #     newContents += 'get_local 2\n'
                        #     newContents += 'get_local 2\n'
                        #     newContents += 'i64.popcnt\n'
                        #     newContents += 'i64.const -3617168760277827607\n'
                        #     newContents += 'i64.add\n'
                        #     idx += 2
                        #     isWritedAct = True
                        #     # print("inject act !!!", fid, " apply")
                        #     continue

                        # elif (not isWritedCode) and (contents[idx].strip() == 'get_local 1' and \
                        #     contents[idx+1].strip() == 'i64.const 6138663591592764928'):
                        #     # obfuscate rtValue
                        #     newContents += 'get_local 1\n'
                        #     newContents += 'get_local 1\n'
                        #     newContents += 'i64.popcnt\n'
                        #     newContents += 'i64.const 6138663591592764906\n'
                        #     newContents += 'i64.add\n'
                        #     idx += 2
                        #     isWritedCode = True
                        #     # print("inject code!!!", fid, " apply")
                        #     continue

                        else:
                            newContents += contents[idx] + '\n'
                            idx += 1
                        '''
                        
                        '''
                    newContents += contents[-1] + '\n'
                    t = newContents
                
                # Actions
                else:
                    contents = t.split('\n')
                    for idx, line in enumerate(contents):
                        if not line.strip().startswith('('):
                            break
                    
                    # you have to confirm eosponser
                    if reduceMap[fid].startswith('###'):
                        if re.search(r"\(param i32 i64 i64 i32 i32\)", t.split('\n', 1)[0]) :
                            contents = contents[:idx] + [reduceMap[fid][3:]] + contents[idx:]
                        else:
                            raise Exception("Eosponser Error")
                        # else:not inject
                    # else:
                    #     contents = contents[:idx] + [reduceMap[fid]] + contents[idx:]

                    # print('[-] idx= ', idx, '\n[-] fid=', fid)
                    
                    # print("inject!!!", fid)
                    t = '\n'.join(contents) 

        evil += t

    evil += ')'
    with open('temp.wat', 'w') as f:
        f.write(evil)

    if os.system(f"eosio-wast2wasm temp.wat -o temp.wasm") != 0:
        raise Exception("eosio-wast2wasm Error")

def main():
    if len(sys.argv) != 5:
        print('Usage: %s <path_to_fuzzer\'s output> <path_to_vul> <path_to_save_injected> <cnt=-1>' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)

    auxbase = sys.argv[1]
    base = sys.argv[2]
    target = sys.argv[3]
    cnt = int(sys.argv[4])

    # ======================= Injecting ==========================
    if cnt > 0:
        fuzzingContracts = os.listdir(base)[:cnt]
    else:
        fuzzingContracts = os.listdir(base)

    threshold = len(fuzzingContracts)
    _idx = 0
    os.system(f"mkdir -p {target} && rm -r {target}/*")
    # print(fuzzingContracts, base, cnt, os.listdir(base))
    for contract in fuzzingContracts:
        # print('---- ', contract, '-----')
        # if contract != 'xlotoioeosio':
        #     continue

        process_bar(_idx/(threshold), start_str='', end_str="100%", total_length=15)
        _idx += 1
        
        auxDir = os.path.join(auxbase, contract)

        if not os.path.exists(os.path.join(auxDir, 'report.json')):
            continue
        else:
            with open(os.path.join(auxDir, 'report.json'), 'r') as f:
                report = json.load(f)

        conDir = os.path.join(base, report['name'])

        # python -m bin.inject /devdata/cwmdata/symzzerDataset/articles /devdata/cwmdata/symzzerDataset/injected_notif /devdata/cwmdata/symzzerDataset/injected_notif        
        # reduceMap = findMap(auxDir)
        # rawWasmPath = os.path.join(base, report['name'], '*.wasm')
        # print(rawWasmPath, reduceMap)
        # reduceCoverage(rawWasmPath, reduceMap)

        rawWasmPath = os.path.join(base, report['name'], '*.wasm')
        try:
            reduceMap = findMap(auxDir)
            # print(reduceMap.keys(), auxDir)
            reduceCoverage(rawWasmPath, reduceMap)
            print("Success for ", rawWasmPath)
        except:
            print("ERROR with ", rawWasmPath)
            continue

        # injected successfully
        targetContractDir = os.path.join(target, report['name'])
        rawAbiPath  = os.path.join(base, report['name'], '*.abi')
        os.system(f"mkdir -p {targetContractDir} && " + \
                f"mv temp.wasm {os.path.join(targetContractDir, report['name']+'.wasm')} && " +\
                f"cp {rawAbiPath} {os.path.join(targetContractDir, report['name'] + '.abi')}")

main()
