import sys
import os
import time
import json
from func_timeout import func_timeout, FunctionTimedOut

import symzzer.setting as setting
from symzzer.utils import EOSPonserException

# if setting.mode == 0:
    # from symzzer.fuzzertestAllActionCoverageMode0 import fuzz
# else:
#     from symzzer.fuzzertestAllActionCoverage import fuzz
from symzzer.fuzzActions import fuzz
from symzzer.argumentFactory import ABIObj
from symzzer.logAnalyzer import FeedbackFactory

TIMEOUT = 5

def init_static(contractName, pathWasm, pathABI):
    os.system(f"rm .tmpRes.txt")

    # init ./rt_info
    rtContractDir = f'{setting.pathHookContract}/{contractName}/'
    os.system(f'rm -rf {setting.pathHookContract} ; mkdir {rtContractDir} -p')
    
    # modify .abi
    with open(pathABI,'r') as f:
        normalABI = json.load(f)
    print(pathABI)
    if 'transfer' not in [item['name'] for item in normalABI['actions']]:
        normalABI['actions'].append(        
            {"name":"transfer","type":"transfer","ricardian_contract":""}
        )
        normalABI['structs'].append(
            {"name":"transfer","base":"","fields":[{"name":"from","type":"name"},{"name":"to","type":"name"},{"name":"quantity","type":"asset"},{"name":"memo","type":"string"}]}
        )
    # new abi
    with open(f'{rtContractDir}/{contractName}.abi', 'w') as f:
        json.dump(normalABI, f)

    # .wasm instrumentation
    os.system(f'cp {pathWasm} {setting.pathHookContract}') # original wasm

    # wasabi
    os.system(f'wasabi {pathWasm} ./out')
    os.system(f"mv ./{pathWasm.split('/')[-1].split('.wasm')[0]}.txt {setting.pathHookContract}/{contractName}.txt")
    os.system(f'mv ./out/*.wasm {rtContractDir}/{contractName}.wasm')
    os.system(f'rm -rf ./out')

    # for analysis
    os.system(f"mkdir {setting.pathHookContract}/rLogs/") #       raw logs
    os.system(f"mkdir {setting.pathHookContract}/pLogs/") # processed logs
    
    return ABIObj(f'{rtContractDir}/{contractName}.abi'), FeedbackFactory()


def find_fakeNotif_atk(contractName, feedbackFactory):
    _base = f'{setting.pathHookContract}/pLogs/'
    for _fname in os.listdir(_base):
        if _fname.split('_')[1][0] != '1':
            continue
        # recovery
        with open(_base + _fname, 'r') as f:
            (logJson, entry), _, _, _ = json.load(f)

        # find atk   
        currentActionId = logJson[entry+1][2][0]
        if currentActionId != feedbackFactory.transferEntry:
            continue# keep trying

        # in first action, contract is safe with (to != self / !(to == self))
        a = feedbackFactory.name2uint64(setting.forgedNotificationAgentName)
        b = feedbackFactory.name2uint64(contractName)
        for tmpidx, item in enumerate(logJson[entry:]):
            _ , instr , args, _ = item
            if instr == 'end_function' and args[0] == currentActionId:
                # action terminated
                break
            if args[0] != currentActionId:
                # not in action
                continue

            if instr in ['i64.ne', 'i64.eq']:
                operand1 = args[3]<<32 | args[2] 
                operand2 = args[5]<<32 | args[4] 
                _res = args[6]
                if ((a, b) == (operand1, operand2) or (a, b) == (operand2, operand1)):
                    print(f'[+] Fake Notification has fix:: ' +\
                        f'action@{currentActionId}:row_{args[1]} checks to({a}) != _self({b})')
                    return tuple(args[:2] + [instr])
    return ()

def find_fakeos_atk(contractName, feedbackFactory):
    _base = f'{setting.pathHookContract}/pLogs/'
    for _fname in os.listdir(_base):
        if _fname.split('_')[1][0] not in  ('2', '3'):
            continue
    
        with open(_base + _fname, 'r') as f:
            (logJson, entry), _, _, _ = json.load(f)
            
        a = feedbackFactory.name2uint64(contractName) # [code]
        b = feedbackFactory.name2uint64("eosio.token")

        for _ , instr , args, _  in logJson[:entry]:
            if args[0] != feedbackFactory.applyFuncId:
                continue

            if instr == 'i64.eq':
                operand1 = args[3] <<32 | args[2] 
                operand2 = args[5] <<32 | args[4] 
                _res = args[6]
                if ((a, b) == (operand1, operand2) or (a, b) == (operand2, operand1)):
                    print(f'[+] Fakeos has fix:: ' +\
                        f'apply():row_{args[1]} checks code == eoso.token')
                    return tuple(args[:2] + [instr])
    return ()


def fuzzTimeLimiter(contractABI, feedbackFactory, in_atk=()):
    print("fuzzing...")
    failCnt = 8
    while failCnt > 0:
        failCnt -= 1
        try:
            retVal = func_timeout(setting.timeoutSeconds, fuzz, args=(contractABI, feedbackFactory, in_atk))
            break
        except FunctionTimedOut:
            print(f"[-] fuzz:: Fuzzer was terminated in {setting.timeoutSeconds}s.\n")
            break
        except EOSPonserException as e:
            print(f"[-] fuzz:: No EOSPonser. Try Again")
            continue
    
    if failCnt == 0:
        print(f"[-] fuzz:: No EOSPonser. Exit")
        exit(-1)
            
    if setting.isFakeNot != '0':
        if -11 in setting.bugSet:
            if 1 in setting.bugSet:
                setting.bugSet.remove(1)
        else:
            if 1 not in setting.bugSet:
                setting.bugSet.append(1)

def main():
    isInject = False
    # CLI
    fields = ['code', 'abi', 'name', 'round', 'timeout', 'savefile', 'vuls']
    config = {f: None for f in fields}
    config['flags'] = set()

    field_iter = iter(fields)
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            # '--isInjected'
            config['flags'].add(arg[2:].upper())
        else:
            field = next(field_iter)
            config[field] = arg

    if config['code'] is None or config['abi'] is None:
        # e.g. python -m bin.fuzz test/contracts/hello/hello.wasm test/contracts/hello/hello.abi hello 30 120 .rt/ --detect_vuls 0111
        #      python -m bin.fuzz test/contracts/hello/hello.wasm test/contracts/hello/hello.abi hello 30 120 .rt/ --detect_vuls 1000
        #      python -m bin.fuzz /home/toor/benchmark/fixed_receipt_withABI/eosbetdice11_2018-10-20_00_04_45/eosbetdice11_2018-10-20_00_04_45.wasm /home/toor/benchmark/fixed_receipt_withABI/eosbetdice11_2018-10-20_00_04_45/eosbetdice11_2018-10-20_00_04_45.abi eosbetdice11  50 120 .rt/ --detect_vuls 0100 --inject
    
        print('Usage: %s [flags] <code> <abi> <name> [round] [timeout] [savefile] [vuls]' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)

    setting.contractName = config['name'] if config['name'] != 'NULL' else config['code'].split('/')[-1].split('.wasm')[0].split('_')[0].split('-')[0]
    
    if 'inject'.upper() in config['flags']:
        isInject = True
        
    if config['round'] is not None:
        _t = int(config['round'])
        if _t != -1:
            setting.maxPeriod = _t
    
    if config['timeout'] is not None:
        setting.timeoutSeconds = int(config['timeout'])

    if config['savefile'] is not None:
        setting.pathHookContract = config['savefile'] + '/'
        setting.plogPath = setting.pathHookContract + '/log2.txt'

    # config for the detectors
    if 'DETECT_VULS' in config['flags']:
        setting.detectVul = True

        if config['vuls'] is not None:
            assert len(config['vuls']) == 6 and config['vuls'].count('2') <= 1, '[-] Invalid parameter for `vuls`'
            '''
            0 : disable
            1 : enable
            2 : fast mode: stop analysis as soon as found a bug
            '''
            setting.isChkOOB       = config['vuls'][0] 
            setting.isFakeEos      = config['vuls'][1] 
            setting.isFakeNot      = config['vuls'][2] 
            setting.isChkPems      = config['vuls'][3]
            setting.isRollback     = config['vuls'][4]
            setting.isBlockinfoDep = config['vuls'][5]
    else:
        setting.detectVul = False     

    print("[+] Test:", setting.contractName)
    # final report for this contract
    caseReport = {
        'name': setting.contractName,
        'time':-1,
        'bugs':[],
        'lava_eos':(),
        'lava_notif':()
    }

    _beforeFuzzTime = time.time()

    abiObj, feedbackObj = init_static(setting.contractName, config['code'], config['abi'])
    fs = {'send_inline', 'send_deferred', 'send_context_free_inline', 'cancel_deferred', 
                'db_find_i64', 'db_lowerbound_i64', 'db_get_i64',
                'db_update_i64', 'db_store_i64', 'db_remove_i64', 'db_idx64_store', 'db_idx64_update', 'db_idx64_remove', 'db_idx128_update',
                'db_idx128_store', 'db_idx128_remove', 'db_idx256_remove', 'db_idx256_store'}
    
    # for filter pm
    # if len(set(feedbackObj.importsFunc ) & fs) == 0:
    #     print("???[-] remove, ", setting.contractName)
    #     os.system(f"echo {setting.contractName} >> /tmp/pmrms")
    #     # os.system(f"rm -r {setting.contractName}")
    # else:
    #     print("???[+] use it, ", setting.contractName)
    #     print(set(feedbackObj.importsFunc ) & fs)

    fuzzTimeLimiter(contractABI=abiObj, feedbackFactory=feedbackObj)

    
    caseReport['time'] = '%.2fs' % (time.time() - _beforeFuzzTime)
    caseReport['logLifes'] = [(pidx, _k - _beforeFuzzTime) for pidx, _k in setting.timePoints]
    caseReport['bugs'] = setting.bugSet

    if isInject:
        # fixed fakeNotif
        if 1 not in caseReport['bugs']:
            try:
                caseReport['lava_notif'] = find_fakeNotif_atk(setting.contractName, feedbackObj)
            except:
                pass

        # fixed fakeos
        if 2 not in caseReport:
            try:
                caseReport['lava_eos'] = find_fakeos_atk(setting.contractName, feedbackObj)
            except:
                pass
    
    with open(f'{setting.pathHookContract}/report.json', 'w') as f:
        json.dump(caseReport, f)
    os.system(f'rm {setting.plogPath}')
    os.system(f'mv {setting.pathHookContract}/*.wasm {setting.pathHookContract}/raw.wasm')

    if 'nostdout'.upper() not in config['flags']:
        # stdout
        if setting.isChkOOB != '0':
            print("- Checking OOB")
        if setting.isFakeEos != '0':
            print('- Checking Fakeos')
        if setting.isFakeNot != '0':
            print('- Checking FakeNotif')
        if setting.isChkPems != '0':
            print("- Checking AuthMissing")
        if setting.isBlockinfoDep != '0':
            print("- Checking BlockinfoDep")
        if setting.isRollback != '0':
            print("- Checking Rollback")

        caseReport['logLifes'] = []
        print('[+] final report:', json.dumps(caseReport, indent=4))
    '''
    bugs:
    1: fake notification
    2. fake eos
    3. OOB
    6. AuthMissing
    7. BlockinfoDep
    8. Rollback
    '''



if __name__ == "__main__":
    main()