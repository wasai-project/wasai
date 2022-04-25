import symzzer.setting as setting

# if setting.mode == 0:
    # from symzzer.fuzzertestAllActionCoverageMode0 import fuzz
# else:
#     from symzzer.fuzzertestAllActionCoverage import fuzz
from symzzer.fuzzActions import fuzz
from symzzer.argumentFactory import ABIObj
from symzzer.logAnalyzer import FeedbackFactory

import os
import time
import json
import sys


def init_static():
    contractName = setting.contractName
    pathOriginContract = setting.pathBaseContract + setting.contractDir

    # init ./rt_info
    os.system(f'rm -rf {setting.pathHookContract} ; mkdir {setting.pathHookContract}')
    os.system(f'mkdir {setting.pathHookContract}/{contractName}')

    # modify .abi
    contractPathABI  = setting.pathHookContract + contractName + '/' + contractName + '.abi'
    os.system(f'cp {pathOriginContract}/*.abi  {contractPathABI}')

    with open(contractPathABI,'r') as f:
        normalABI = json.load(f)
    if 'transfer' not in [item['name'] for item in normalABI['actions']]:
        normalABI['actions'].append(        
            {"name":"transfer","type":"transfer","ricardian_contract":""}
        )
        normalABI['structs'].append(
            {"name":"transfer","base":"","fields":[{"name":"from","type":"name"},{"name":"to","type":"name"},{"name":"quantity","type":"asset"},{"name":"memo","type":"string"}]}
        )
    with open(contractPathABI, 'w') as f:
        json.dump(normalABI, f)

    # modify .wasm
    pathContract = setting.pathHookContract + contractName
    pathWasm = pathContract + '/' + contractName + '.wasm'
    os.system(f'cp {pathOriginContract}/*.wasm {pathWasm}')

    # wasabi
    os.system(f'wasabi {pathWasm} ./out')
    os.system(f'mv ./{contractName}.txt {setting.pathHookContract}')
    os.system(f'rm -rf {pathWasm}')
    os.system(f'mv ./out/{contractName}.wasm {pathWasm}')
    os.system(f'rm -rf ./out')

    # for analysis
    os.system(f"rm -r {setting.pathHookContract}/tmpLogs/ ; mkdir {setting.pathHookContract}/tmpLogs/")
    os.system(f"cp {pathOriginContract}/*.wasm {setting.pathHookContract}/") # original wasm

    return ABIObj(contractPathABI), FeedbackFactory()


def fuzzerALL():
    setting.detectVul = True
    setting.OOB = False
    isInject = True
    setting.isProxy = False
    # ================ collect dataset ===================
    contractsList = []
    for contract in os.listdir(setting.pathBaseContract):
        # if contract != 'hello': # 'pickowngames_2019-01-15_07_27_21':#'gambaccarats_2019-3-8': #'eosbaccasino_8-02-2019-100409':#'epsdcclassic_2019-02-05_13_57_07':# 'fixfakercpt': #
        #     continue

        contractFiles = os.listdir(setting.pathBaseContract + contract)
        hasAbi = False
        hasCode = False
        for contractFile in contractFiles:
            if contractFile == contract + '.abi':
                hasAbi = True
            if contractFile == contract + '.wasm':
                hasCode = True
        if hasAbi and hasCode:
            contractsList.append(contract)
 
    # ================= fuzz ==================
    reports = dict()
    fakeNotifATKs = dict()
    fakeEOSATKs   = dict()

    beforeFuzzTime = time.time()

    for contract in contractsList:
        # if contract == 'thedeosgames_2019-02-19_20_07_50':
        #     continue

        setting.bugDict = set()
        _magic = -1
        setting.contractDir = contract
        setting.contractName = contract.split('_')[0]
        os.system(f"mkdir /devdata/cwmdata/symzzerDataset/articles/{setting.contractName}")
        caseReport = list()
        try: # TODO

            # init rt_info
            abiObj, feedbackObj = init_static()
            # fuzz
            os.system(f"rm {os.getenv('HOME') + '/dynamicAnalyze/EOSFuzzer/symzzer/.tmpRes.txt'}")
            _ = fuzz(contractName=setting.contractName, contractABI=abiObj, feedbackFactory=feedbackObj,  maxPeriod=setting.maxPeriod)

        except StopIteration:
            print("time-out")
        except:
            print('runtime error')
        
        try:
            with open(os.getenv('HOME') + '/dynamicAnalyze/EOSFuzzer/symzzer/.tmpRes.txt', 'r') as f:
                caseReport = json.load(f)
        except:
            caseReport = []
            

        if isinstance(caseReport, list):
            # record
            for _magic in list(set(caseReport)):
                if _magic in reports :
                    reports[_magic].append(contract)
                else:
                    reports[_magic] = [contract]

        # fixed fakeNotif
        if isInject:
            if (1 not in caseReport):
                try:
                    res = find_fakeNotif_atk(setting.contractName, feedbackObj)
                    if res != ():
                        fakeNotifATKs[contract] = res
                        print('[+] ATK Notif',res, contract)
                except:
                    pass

            # fixed fakeos
            if (2 not in caseReport and 3 not in caseReport):
                try:
                    res = find_fakeos_atk(setting.contractName, feedbackObj)
                    if res != ():
                        fakeEOSATKs[contract] = res
                except:
                    pass
            
        # save static
        target = '/devdata/cwmdata/symzzerDataset/dataset/logs/'
        os.system(f'mkdir {target}/{contract}/')
        os.system(f'mv {setting.pathHookContract}/tmpLogs {target}/{contract}/logs')
        os.system(f'mv {setting.pathHookContract}/{contract}.wasm {target}/{contract}/{setting.contractName}.wasm')
        os.system(f'mv {setting.pathHookContract}/{setting.contractName}/{setting.contractName}.abi {target}/{contract}/{setting.contractName}.abi')
        # break


    print('[+] ========================= Bug Report: ============================')
    if reports:
        for key, val in reports.items():
            print(f' vul_{key}: {len(val)}', val)
    else:
        print(' ALL SAFE')

    afterFuzzTime = time.time()
    timeRecordString = str(afterFuzzTime - beforeFuzzTime)
    print(f'    - Time: {timeRecordString} s.')
    print(f'    - Analyzed {len(contractsList)} contracts.')
    # print('    ==================================================================')
    if isInject:
        print('[+] ========================= ATK Report: ============================')
        atknotifPath = "/devdata/cwmdata/symzzerDataset/dataset/evilFakeNotif.json"
        with open(atknotifPath, 'w') as f:
            json.dump(fakeNotifATKs, f)
        print(f'    - file save at {atknotifPath}')
    

        atkeosPath = "/devdata/cwmdata/symzzerDataset/dataset/evilFakeos.json"
        with open(atkeosPath, 'w') as f:
            json.dump(fakeEOSATKs, f)
        print(f'    - file save at {atkeosPath}')   
        print('    ==================================================================') 


def find_fakeNotif_atk(contractName, feedbackFactory):
    _base = f'{setting.pathHookContract}/tmpLogs/'
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
    _base = f'{setting.pathHookContract}/tmpLogs/'
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


if __name__ == "__main__":
    os.system("rm -rf /devdata/cwmdata/symzzerDataset/articles ; mkdir /devdata/cwmdata/symzzerDataset/articles")
    target = '/devdata/cwmdata/symzzerDataset/dataset/logs'
    os.system(f'rm -r {target} ; mkdir {target}')
    fuzzerALL()

'''
coverage fail
contract, symzzer, eosfuzzer
eospoltokens , 134 , 438
batsicbo1234 , 132 , 1014
eosmaxioteam , 344 , 416
lottgolden33 , 927 , 1028
ppgamereward , 284 , 299

'''
