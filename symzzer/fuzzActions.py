import os
import subprocess
import time
import timeout_decorator
import json
import itertools
import logging
import random
import copy
import z3
import traceback
import sys

import symzzer.setting as setting
from symzzer.setting import logger

from symzzer.node import Node, PriorityQueue
from symzzer.logAnalyzer import FeedbackFactory
from symzzer.argumentFactory import ArgumentFactory, ABIObj
import symzzer.utils as utils

from symzzer.tainter.wasabiHooker import Wasabi
import symzzer.tainter.utils as taintutils

# global variable
idxPeriod = 1

DISABLE = '0'
ENABLE  = '1'
FFMODE  = '2'


def executeCommand(arguments, mustExecute = False):
    cmd = ' '.join(arguments)
    print("[-] executeCommand::", cmd)
    if mustExecute:
        testRound = 16
        while testRound > 0:
            testRound -= 1
            returnValue, out = subprocess.getstatusoutput(cmd)
            print("[-] executeCommand::", returnValue, out)
            if returnValue == 1 and "Expired Transaction" in out:
                continue
                
            elif returnValue in [0, 1]:
                return returnValue, out
        return False, ""

    else:
        r, o = subprocess.getstatusoutput(cmd)
        print(o)
        return r, o


def createAccount(name, publicKey, mustExecute = False):
    executeCommand([setting.cleosExecutable, 'create', 'account', 'eosio', name, publicKey], mustExecute)

def setContract(name, contractAddress, permission, mustExecute = False):
    executeCommand([setting.cleosExecutable, 'set', 'contract', name, contractAddress, '-p', permission], mustExecute=mustExecute)

def pushAction(contract, action, arguments, permission, mustExecute = False):
    print(' '.join([setting.cleosExecutable, 'push', 'action', contract, action, '\'' + arguments + '\'', '-p', permission]))
    logger.debug(' '.join([setting.cleosExecutable, 'push', 'action', contract, action, '\'' + arguments + '\'', '-p', permission])) #, '>> /dev/null 2>&1' if rpsRequired else ''
    return executeCommand([setting.cleosExecutable, 'push', 'action', 
     contract, action, '\'' + arguments + '\'', '-p', permission], mustExecute)#'--json' if rpsRequired else "--console"
     #, '' if rpsRequired else '>> /dev/null 2>&1'
    
def addCodePermission(name, mustExecute = False):
    #executeCommand(setting.cleosExecutable + ' set account permission ' + name + ' active --add-code', mustExecute)
    executeCommand([setting.cleosExecutable, 'set', 'account', 'permission', name, 'active', '--add-code'], mustExecute)

def getCurrency(account, permission, mustExecute = False):
    #executeCommand(setting.cleosExecutable + ' push action ' + contract + ' ' + action + ' \'' + arguments + '\' -p ' + permission + '@active', mustExecute)
    _, rt = executeCommand([setting.cleosExecutable, 'get', 'currency', 'balance', permission, account, 'EOS'], mustExecute)
    tmp = rt.split(' ')[0]
    return float(tmp) if tmp else 0


def initEosEnv():
    # init EOS environment & deploy contract
    os.system('killall nodeos')
    os.system('killall keosd')  


    os.system('keosd --max-body-size 100000000 &')
    os.system('rm -rf ' + setting.eosFilePath)
    os.system('rm ./nodeos.log')
    
    os.system('echo ' + setting.aPasswordToKeosd + ' | ' + setting.cleosExecutable + ' wallet unlock')
    
    os.system(setting.nodeosExecutable + ' -e -p eosio\
                            --plugin eosio::chain_api_plugin \
                            --plugin eosio::http_plugin \
                            --plugin eosio::history_plugin \
                            --plugin eosio::history_api_plugin\
                            --access-control-allow-origin=\'*\' \
                            --contracts-console \
                            --http-validate-host=false \
                            --verbose-http-errors \
                            --max-transaction-time=1000 \
                            --max-body-size=102400000 \
                            --genesis-json genesis.json \
                            >> nodeos.log 2>&1 &')
    time.sleep(2)

    # createAccount('clerk', setting.eosioTokenPublicKey, True)
    createAccount('eosio.token', setting.eosioTokenPublicKey, True)
    setContract('eosio.token', setting.eosioTokenContract, 'eosio.token@active', True)
    # print("set contract eosio.token")
    createAccount('bob', setting.eosioTokenPublicKey, True)
    addCodePermission('bob', True)

    pushAction('eosio.token', 'create', '["eosio","20000000000000.0000 EOS"]', 'eosio.token@active', True)
    pushAction('eosio.token', 'issue', '["eosio", "20000000000000.0000 EOS",""]', 'eosio@active', True)

    createAccount('fake.token', setting.eosioTokenPublicKey, True)
    createAccount('fakeosio', setting.eosioTokenPublicKey, True)
    setContract('fake.token', setting.eosioTokenContract, 'fake.token@active', True)
    addCodePermission('fake.token', True)
    addCodePermission('fakeosio', True)

    pushAction('fake.token', 'create', '["fakeosio","200000000000000.0000 EOS"]', 'fake.token@active', True)# fake EOS
    
    pushAction('fake.token', 'issue', '["fakeosio", "20000000000000.0000 EOS",""]', 'fakeosio@active', True)
    
    pushAction('eosio.token', 'transfer', '["eosio","fakeosio","10000000.0000 EOS",""]', 'eosio@active', True)

    createAccount('testeosfrom', setting.eosioTokenPublicKey, True)
    addCodePermission('testeosfrom', True)
    pushAction('eosio.token', 'transfer', '["eosio","testeosfrom","10000000.0000 EOS",""]', 'eosio@active', True)


    createAccount(setting.forgedNotificationTokenFromName, setting.eosioTokenPublicKey, True)
    pushAction('eosio.token', 'transfer', f'["eosio","{setting.forgedNotificationTokenFromName}","10000000.0000 EOS",""]', 'eosio@active', True)
    addCodePermission(setting.forgedNotificationTokenFromName, True)
    createAccount(setting.forgedNotificationAgentName, setting.eosioTokenPublicKey, True)
    setContract(setting.forgedNotificationAgentName, setting.atkforgContract, f'{setting.forgedNotificationAgentName}@active', True)
    pushAction(setting.forgedNotificationAgentName, 'regist', f'["{setting.contractName}"]', 'eosio@active', True)
    addCodePermission(setting.forgedNotificationAgentName, True)

  

    createAccount('atknoti', setting.eosioTokenPublicKey, True)
    setContract('atknoti', setting.atknotiContract, 'atknoti@active', True)
    addCodePermission('atknoti', True)


    if setting.useAccountPool:
        createAccount('fuzzacc1', aPublicKey, True)
        createAccount('fuzzacc2', aPublicKey, True)
        createAccount('fuzzacc3', aPublicKey, True)
        os.system('cp ./accounts.conf ' + os.getenv('HOME') + '/.local/share/eosio/')

    # init contract
    pathContract =  setting.pathHookContract + setting.contractName

    createAccount(setting.contractName, setting.aPublicKey)
    addCodePermission(setting.contractName)
    setContract(setting.contractName, pathContract, setting.contractName+'@active')
    

def fuzz(contractABI, feedbackFactory, in_atk=()):
    contractName = setting.contractName
    tmpLogger = utils.Logger(os.getenv('HOME') + '/dynamicAnalyze/EOSFuzzer/symzzer/.tmpRes.txt')

    global idxPeriod
    logging.info(f"{'='*20} {contractName} {'='*20}")

    testDataFactory = ArgumentFactory(contractABI, contractName)

    # init eosio platform
    initEosEnv() 

    os.system(f'rm -r {setting.logPath}* ; rm {setting.plogPath}')
    pushAction('eosio.token', 'transfer', '[ "testeosfrom", "' + setting.contractName + '","100.0000 EOS","FUZZER"]', 'testeosfrom@active', mustExecute=True)
    
    # try:
    feedbackFactory.getTransferEntry() # target eosponser
    with open(f"{setting.pathHookContract}/actPartly.txt", 'w') as f:
        f.write( str(feedbackFactory.applyFuncId) + " " + str(feedbackFactory.transferEntry))

    acceptEOSToken = False
    isFixForgedBug = False
    rejectFakeos = list()
    pmSafeActs = list()

    # fuzzing
    candidateKinds = [0, 1, 2, 3, 4]
    '''
    0: invoke one action of S
    1: fake notification payload
    2: fake EOS payload.1
    3: fake EOS payload.2
    4: transfer valid EOS
    '''

    idxPeriod = 0
    kind = 0

    while idxPeriod <= setting.maxPeriod:
        print("[+] round = ", idxPeriod)
        idxPeriod += 1

        if isFixForgedBug and 1 in candidateKinds:
            candidateKinds.remove(1)
        if acceptEOSToken and 2 in candidateKinds:
            candidateKinds.remove(2)
            candidateKinds.remove(3)
        if kind != 0:
            kind = 0
        else:
            kind = random.choice(candidateKinds)

        if setting.isChkOOB == FFMODE:
            kind = random.choice([0, 4])

        elif setting.isFakeEos == FFMODE:
            kind = random.choice([2, 3])


        elif setting.isFakeNot == FFMODE:
            kind = random.choice([0, 1, 4])

        # kind = 4 
        print('[-] kind = ', kind)
        # 1. choose function
        _fc = ":ALL"
        
        # 考虑把以下代码放入 argumentFactory.py
        lofter = random.choice([0,1])
        if kind == 0 and lofter:
            prexFc =  testDataFactory.functionName
            if prexFc in feedbackFactory.rdb:
                rdbs = feedbackFactory.rdb[testDataFactory.functionName] # table
                if rdbs != []:
                    fs = []
                    for rdb in rdbs:
                        if rdb in feedbackFactory.dbFlow:
                            fs.extend(feedbackFactory.dbFlow[rdb]['w'])
                    if fs != []:
                        _fc = random.choice(fs)
        
        # 2. generate cleos command
        testDataFactory.generateNewData(_fc, kind)
        currentFuncName = testDataFactory.functionName
        logger.info(f'================= testing {currentFuncName} ==========================')
        testDataFactory.generateNewDataType(currentFuncName)
        
        fbSeed = feedbackFactory.seeds(kind, currentFuncName)
        testArgumentStr = json.dumps(fbSeed) if fbSeed != [] else testDataFactory.testArgument

        # 3. execute cleos
        os.system(f"rm {setting.logPath}/* ; rm {setting.plogPath}")

        cmd = ' '.join(['cleos', 'push', 'action', testDataFactory.executedContractName,
                 currentFuncName, '\'' + testArgumentStr + '\'', '-p', f'{testDataFactory.activeAccount}@active'])
        
        logger.info(cmd)  
        feedbackFactory.cmds.append(cmd)

        PriBalance = getCurrency(setting.contractName, 'eosio.token')
        atkPriBalance = getCurrency("testeosfrom", 'eosio.token')
        print('[+] Execute Cleos CMD: ', cmd)
        returnValue, out = subprocess.getstatusoutput(cmd) # sync with nodeos 太慢了？？？
        AftBalance = getCurrency(setting.contractName, 'eosio.token')
        atkAftBalance = getCurrency("testeosfrom", 'eosio.token')
        print('[+] target currency: ', PriBalance, AftBalance)
        print('[+] atker currency: ', atkPriBalance, atkAftBalance)
        if atkPriBalance < atkAftBalance:
            print("YEEEEEEEEEEEEEEEEEEEEEH", setting.contractName)
            with open ("/home/szh/dynamicAnalyze/EOSFuzzer/symzzer/.exploits", "w+") as f:
                f.write(f"{setting.contractName}   {cmd}\n")

        print(returnValue, out)
        
        if os.listdir(setting.logPath):
            setting.timePoints.append((int(sorted(os.listdir(setting.logPath), key=lambda fname: int(fname[4:-4]))[0][4:-4]), time.time()))

        os.system(f'cp {setting.logPath}/* {setting.pathHookContract}/rLogs/') # for coverage
            
        # print('_____++++++++++++++====end', subprocess.getstatusoutput(f'ls {setting.logPath}'))
        isExecuted = True if returnValue == 0 else False
        if 'ABI has an unsupported version' in out:
            return False
        if 'Duplicate transaction' in out or 'Expired Transaction' in out:
            continue

        # 4. deserialize logs
        if not feedbackFactory.processLog('Error' not in out):
            if kind in (2,3):
                if kind not in rejectFakeos:
                    rejectFakeos.append(kind)
                if len(rejectFakeos) == 2 and setting.isFakeEos == FFMODE:
                    return True
            if kind == 1 and setting.isFakeNot == FFMODE:
                return True

            continue
        try:
            feedbackFactory.locateActionPos(index=0, txFuncName=currentFuncName)  # also collect information for first action
        except :
            print("[-] fuzzActions:: ERROR when location actions\n")
            continue

        # save processed logs
        logTuple = [feedbackFactory.firstActLog, feedbackFactory.firstActPos] # logs, line_pos
        with open(f"{setting.pathHookContract}/pLogs/{idxPeriod}_{kind}.json", 'w') as f:
            json.dump([logTuple, testDataFactory.testArgumentType, json.loads(testArgumentStr), cmd], f)

        if setting.detectVul:
            try:
                if setting.isChkPems != DISABLE and 6 not in setting.bugSet:
                    if feedbackFactory.authCheckFault():
                        logging.info("permission check fault")
                        setting.bugSet.append(6)
                        # fast mode
                        if setting.isChkPems == FFMODE:
                            return True
 

                if setting.isBlockinfoDep != DISABLE and 7 not in setting.bugSet:
                    if feedbackFactory.usedTaposFunctionThenEosioTokenTransfer():
                        # success
                        logging.info("Tapos Warning")
                        setting.bugSet.append(7)
                        
                        # fast mode
                        if setting.isBlockinfoDep == FFMODE:
                            return True
                        
                        if (setting.isBlockinfoDep, setting.isRollback) == (ENABLE, ENABLE) \
                                and (7 in setting.bugSet and 8 in setting.bugSet):
                            return True

                if setting.isRollback != DISABLE and 8 not in setting.bugSet:
                    if feedbackFactory.rollback():
                        # success
                        logging.info("rollback Warning")
                        setting.bugSet.append(8)

                        # fast mode
                        if setting.isRollback == FFMODE:
                            return True

                        if (setting.isBlockinfoDep, setting.isRollback) == (ENABLE, ENABLE) \
                                and (7 in setting.bugSet and 8 in setting.bugSet):
                            return True

                if setting.isFakeNot != DISABLE and isFixForgedBug == False and kind == 1:
                    
                    _magic = feedbackFactory.checkForgedNotificationBug(testDataFactory.forgedNotificationAgentName, contractName, isExecuted)
                    if _magic == 0:
                        isFixForgedBug = True
                        setting.bugSet.append(-11)
                        if setting.isFakeNot == FFMODE:
                            return True
                
                    elif _magic == 1: 
                        logger.info("Fake Notification")
                        if 1 not in setting.bugSet:
                            setting.bugSet.append(1)
                        

                if setting.isFakeEos != DISABLE and kind in [2, 3] and 2 not in setting.bugSet:
                    print("-----------------------------testing fake eos \n\n\n---------------")
                    if feedbackFactory.hasFakeTransferBug():
                        logger.info(f"Has fake transfer bug;Fake EOS kind={kind}")
                        setting.bugSet.append(2)

                    if setting.isFakeEos == FFMODE:
                        return True

            except:
                print('[-] Scanner Error')

            
        if True and (kind == 0 or (kind in (1, 4) and feedbackFactory.transferEntry == feedbackFactory.caseInfo[2])):
            '''
            inactive feeback when detecting Fake EOS, as it is unnecessary to analyze action function.
            '''
            # 5. feedback base on symbolic execution
            print('-------------------- emulator -------------------', idxPeriod)
            if setting.globalDebug:
                print("??? test argument=", testArgumentStr)
                print("??? test argument types =", testDataFactory.testArgumentType)

            cleosJson = json.loads(testArgumentStr)
            inputType = testDataFactory.testArgumentType

            wasabi = Wasabi(inputType, cleosJson, feedbackFactory.importsFunc, feedbackFactory.firstActEntry)
            
            # handling first action
            startPos, endPos, _, _ = feedbackFactory.caseInfo
            actionLog = feedbackFactory.firstActLog[startPos-1:endPos]
            # print("[-] fuzzActions.wasabiInput::", actionLog)
            for line in actionLog:
                try:
                    _, instr, args, types = line
                    symArgs = taintutils.buildArgs(instr, args, types)
                    wasabi.lowlevelHooks(instr, symArgs)

                except Exception as e:
                    print('[-] EOSVM Model ERROR:', e)
                    break # drop

            # exit()
            threadPool = list()
            for _, constraint in wasabi.analysis.queue:
                i_context = z3.Context()
                i_constraint = copy.deepcopy(constraint).translate(i_context)
                thread = utils.myThread(i_constraint, i_context)
                thread.start()
                threadPool.append(thread)
                
            # exit()   
            z3Models = list()
            for thread in threadPool:  
                thread.join()  
                z3Models.append(thread.get_result())
                     
            for cfb, z3Model in zip([cfb for cfb, _ in wasabi.analysis.queue], z3Models):
                if z3Model == [None]:
                    continue
                try:
                    wasabi.analysis.seedMining(cfb, z3Model)
                except:
                    pass
                    # abi mismatch
            

            print("[+] =========== output new seeds ====================")
            print(wasabi.analysis.cleosArgs)
            # exit()
            newSeeds = list()
            f = lambda data, k : list(data.keys())[k] 
            for location, argPosTuple, value in wasabi.analysis.cleosArgs:
                # TODO 将此 touched branches filter 转移至analysis.solve()中

                if location in feedbackFactory.touchedBrs[(kind, currentFuncName)]:
                    continue

                seed = cleosJson.copy()
                layout_o, layout_i = argPosTuple

                key = f(cleosJson, layout_o)
                if layout_i != -1:
                    # struct
                    if setting.globalDebug:
                        print(seed, key, layout_i, '@@')
                    ikey = f(seed[key], layout_i)
                    seed[key][ikey] = value
                    if setting.globalDebug:
                        print(f"cmd={cmd} ---- newSeed={seed}, argPosTuple={argPosTuple}, value={value}")

                else:
                    seed[key] = value 

                newSeed = (location, seed)
                feedbackFactory.seedDict[(kind, currentFuncName)].append(newSeed)
                feedbackFactory.touchedBrs[(kind, currentFuncName)].add(location)
                print('[+] newSeed generated:', newSeed)
        
            print('[+++++++++++] ============ runtime debug ================')
            for cmd in feedbackFactory.seedDict[(kind, currentFuncName)]:
                print("[+] seed Pools:", cmd, '\n')
     
    return True