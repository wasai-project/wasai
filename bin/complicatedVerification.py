import sys
import os
import json
import re

template = {
    'I32' : "\n(if (i32.eq (get_local {0}) (i32.const 123) ) (then unreachable))\n",
    'I64' : "\n(if (i64.eq (get_local {0}) (i64.const 123456) ) (then unreachable))\n",
    'F32' : "\n(if (f32.lt (get_local {0}) (f32.const 11.2) (f32.sub) (f32.abs) (f32.const 0.001) ) (then unreachable))\n",
    'F64' : "\n(if (f64.lt (get_local {0}) (f64.const 123.5) (f64.sub) (f64.abs) (f64.const 0.001) ) (then unreachable))\n",
    'asset':"\n(if (i64.ne (get_local {0}) (i64.load) (i64.const 100000) ) (then (unreachable) ) )\n" +\
            "  (if (i64.ne (get_local {0}) (i64.load offset=8) (i64.const 1397703940) ) (then (unreachable) ) )\n" 
}

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

def process_bar(percent, start_str='', end_str='', total_length=0):
    bar = ''.join(["\033[31m%s\033[0m"%'###'] * int(percent * total_length)) + ''
    bar = '\r' + start_str + bar.ljust(total_length) + ' {:0>4.1f}%|'.format(percent*100) + end_str
    print(bar, end='', flush=True)


def main():
    if len(sys.argv) != 3:
        print('Usage: %s <path_to_fuzzer\'s output> <cnt=-1>' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)

    auxbase = sys.argv[1]
    _cnt = int(sys.argv[2])

    if _cnt > 0:
        fuzzingContracts = os.listdir(auxbase)[:_cnt]
    else:
        fuzzingContracts = os.listdir(auxbase)

    result = dict()

    for _idx, contract in enumerate(fuzzingContracts):
        # print('---- ', contract, '-----')
        # if contract != 'xlotoioeosio':
        #     continue

        # print process
        process_bar((_idx+1)/(len(fuzzingContracts)), start_str='', end_str="100%", total_length=20)
        # print(_idx, len(fuzzingContracts))

        _bs = os.path.join(auxbase, contract, 'pLogs')
        if not (os.path.exists(_bs) and os.path.exists(os.path.join(auxbase, contract, "actPartly.txt"))):
            continue
        
        reduceMap = dict()

        logs = [os.path.join(_bs, p) for p in os.listdir(_bs) if p.split('_')[1][0] == '0']
        
        with open(os.path.join(auxbase, contract, "actPartly.txt"), 'r') as f:
            _line = f.readline().split()
            _, eosponserFuncId = int(_line[0]), int(_line[1])
            _guard  = "\n(if (i64.ne (get_local 3)  (i64.load) (i64.const 100000) ) (then   (unreachable) ) )\n" 
            _guard += "\n(if (i64.ne (get_local 3) (i64.load offset=8) (i64.const 1397703940) ) (then  (unreachable) ) )\n"
            reduceMap[eosponserFuncId] = _guard
    
        actMap = dict()
        for log in logs:
            try:
                with open(log, 'r') as f:
                    (traces, actLinePos), seedTypes, _, _cleosCmd = json.load(f)
                actName = _cleosCmd.split(' ')[4]
                if actName in actMap or actLinePos == -1:
                    continue
            except:
                continue
            
            # light filter
            # traceCallin = traces[actLinePos]
            # if not len(traceCallin[3]) == len(seedTypes) + 1: # the first type is _self
            actMap[actName] = (traces[actLinePos+2][2][0], seedTypes, _cleosCmd)


        for actName, (actFid, seedTypes, _cleosCmd) in actMap.items():
            # only inject one guard condition
            guard = ""
            for localIdx, rawtp in enumerate(seedTypes):
                tp = typeSwitcher(rawtp)
                if tp in template:
                    guard = template[tp].format(localIdx+1)
                    break

            if guard:
                reduceMap[actFid] = guard
                # print(actName)
        result[contract] = reduceMap
    with open(os.path.join("/devdata/cwmdata/symzzerDataset/sec22/rq2/data", "reduceCov.json"), 'w') as f:
        json.dump(result, f)

    # return result

main()
