import os
import subprocess
import time
import timeout_decorator
import json
import itertools
import logging

import setting 
from setting import logger

from node import Node, PriorityQueue
from logAnalyzer import FeedbackFactory
from argumentFactory import ArgumentFactory, ABIObj
import utils




def executeCommand(arguments, mustExecute = False, rpsRequired = False):
    if rpsRequired:
        # print('ddd:', arguments)
        r = os.popen(' '.join(arguments))  
        text = r.read()  
        r.close()  
        return text 
    else:
        if mustExecute:
            testRound = 256
            while testRound >= 0:
                testRound -= 1
                #returnValue = os.system(arguments)
                returnValue = subprocess.call(arguments)
                #print('returnValue = ', returnValue)
                if returnValue == 0:
                    return True
            return False
        else:
            #os.system(arguments)
            subprocess.call(arguments)
 
def exploitCurrency(vulCBefore):
    # return False
    # verify currency
    vulCAfter = getCurrency(setting.contractName, 'eosio.token')
    cruyAtk = getCurrency('bob', 'eosio.token')
    print('asasd',vulCBefore, vulCAfter, cruyAtk)
    if vulCBefore > vulCAfter:
        print("[+] Attack Success")
        return True
    else:
        return False

def createAccount(name, publicKey, mustExecute = False):
    #executeCommand(setting.cleosExecutable + ' create account eosio ' + name + ' ' + publicKey, mustExecute)
    executeCommand([setting.cleosExecutable, 'create', 'account', 'eosio', name, publicKey], mustExecute)

def setContract(name, contractAddress, permission, mustExecute = False):
    #executeCommand(setting.cleosExecutable + ' set contract ' + name + ' ' + contractAddress, mustExecute)
    executeCommand([setting.cleosExecutable, 'set', 'contract', name, contractAddress, '-p', permission], mustExecute)

def pushAction(contract, action, arguments, permission, mustExecute = False, rpsRequired = False):
    #executeCommand(setting.cleosExecutable + ' push action ' + contract + ' ' + action + ' \'' + arguments + '\' -p ' + permission + '@active', mustExecute)
    # print(setting.cleosExecutable, 'push', 'action', contract, action, arguments, '-p', permission)
    logger.debug(' '.join([setting.cleosExecutable, 'push', 'action', contract, action, '\'' + arguments + '\'', '-p', permission]))
    return executeCommand([setting.cleosExecutable, 'push', 'action',
     contract, action, arguments, '-p', permission, '--json'], mustExecute, rpsRequired)
    
def addCodePermission(name, mustExecute = False):
    #executeCommand(setting.cleosExecutable + ' set account permission ' + name + ' active --add-code', mustExecute)
    executeCommand([setting.cleosExecutable, 'set', 'account', 'permission', name, 'active', '--add-code'], mustExecute)

def getCurrency(account, permission, mustExecute = False):
    #executeCommand(setting.cleosExecutable + ' push action ' + contract + ' ' + action + ' \'' + arguments + '\' -p ' + permission + '@active', mustExecute)
    rt = executeCommand([setting.cleosExecutable, 'get', 'currency', 'balance', permission, account, 'EOS'], mustExecute, rpsRequired=True)
    tmp = rt.split(' ')[0]
    # print(tmp[0])
    return float(tmp) if tmp else 0


@timeout_decorator.timeout(60, timeout_exception=StopIteration)
def initEosEnv():
    # init EOS environment & deploy contract
    os.system('killall keosd')
    os.system('killall nodeos')
    os.system('keosd &')
    os.system('rm -rf ' + setting.eosFilePath)
    os.system('rm ./nodeos.log')
    
    os.system('echo ' + setting.aPasswordToKeosd + ' | ' + setting.cleosExecutable + ' wallet unlock')
    os.system(setting.nodeosExecutable + ' -e -p eosio\
                            --plugin eosio::producer_plugin \
                            --plugin eosio::chain_api_plugin \
                            --plugin eosio::http_plugin \
                            --plugin eosio::history_plugin \
                            --plugin eosio::history_api_plugin \
                            --access-control-allow-origin=\'*\' \
                            --contracts-console \
                            --http-validate-host=false \
                            --verbose-http-errors \
                            --max-transaction-time=1500 \
                            >> nodeos.log 2>&1 &')
    # os.system('eosio-cpp -o ' + setting.atkforgContractBinary + ' ' + setting.atkforgContractSource + ' -DCONTRACT_NAME=\\"' + setting.contractName + '\\"')
    
    time.sleep(1)

    # os.system('eosio-cpp -o ' + atkforgContractBinary + ' ' + atkforgContractSource + ' -DCONTRACT_NAME=\\"' + setting.contractName + '\\"')
    createAccount('alice', setting.eosioTokenPublicKey, True)

    addCodePermission('alice', True)
    createAccount('bob', setting.eosioTokenPublicKey, True)
    addCodePermission('bob', True)
    # createAccount('clerk', setting.eosioTokenPublicKey, True)
    createAccount('eosio.token', setting.eosioTokenPublicKey, True)
    setContract('eosio.token', setting.eosioTokenContract, 'eosio.token@active', True)
    pushAction('eosio.token', 'create', '["alice","20000000000000.0000 EOS"]', 'eosio.token@active', True)
    pushAction('eosio.token', 'issue', '["alice", "20000000000000.0000 EOS",""]', 'alice@active', True)
    pushAction('eosio.token', 'transfer', '["alice", "eosio","20000000000000.0000 EOS",""]', 'alice@active', True)

    pushAction('eosio.token', 'transfer', '["eosio", "bob","10000000000.0000 EOS",""]', 'eosio@active', True)
    
  
    # if setting.isProxy:

    createAccount('testeosfrom', setting.eosioTokenPublicKey, True)
    pushAction('eosio.token', 'transfer', '["eosio","testeosfrom","10000000.0000 EOS","FUZZER"]', 'eosio@active', True)

    createAccount(setting.forgedNotificationTokenFromName, setting.eosioTokenPublicKey, True)
    pushAction('eosio.token', 'transfer', f'["eosio","{setting.forgedNotificationTokenFromName}","10000000.0000 EOS","FUZZER"]', 'eosio@active', True)

    createAccount('atkforg', setting.eosioTokenPublicKey, True)
    setContract('atkforg', setting.atkforgContract, 'atkforg@active', True)
    addCodePermission('atkforg', True)

    # createAccount('atknoti', setting.eosioTokenPublicKey, True)
    # setContract('atknoti', setting.atknotiContract, 'atknoti@active', True)
    # addCodePermission('atknoti', True)

    # createAccount('atkrero', setting.eosioTokenPublicKey, True)
    # setContract('atkrero', setting.atkreroContract, 'atkrero@active', True)
    # addCodePermission('atkrero', True)

    if setting.useAccountPool:
        createAccount('fuzzacc1', aPublicKey, True)
        createAccount('fuzzacc2', aPublicKey, True)
        createAccount('fuzzacc3', aPublicKey, True)
        os.system('cp ./accounts.conf ' + os.getenv('HOME') + '/.local/share/eosio/')

    # init contract
    pathContract =  setting.pathHookContract + setting.contractName
    # os.system('eosio-cpp -o ' + setting.contractName+'.wasm' + ' ' + pathContract+'.cpp' + ' -DCONTRACT_NAME=\\"' + setting.contractName + '\\"')

    createAccount(setting.contractName, setting.aPublicKey)
    addCodePermission(setting.contractName)

    pushAction('eosio.token', 'transfer', '[ "eosio", "' + setting.contractName + '","100000.0000 EOS","FUZZER"]', 'eosio@active', True)
    setContract(setting.contractName, pathContract, setting.contractName+'@active')
    # exit(0)

@timeout_decorator.timeout(setting.timeoutSeconds, timeout_exception=StopIteration)
def fuzz(actionName = ':ALL', useAnotherAccountName = False, accountName = '', fuzzerCount = 4, Debug=False):
    def isNewPath(path, existedPaths):
        for epath in existedPaths:
            if [p[0] for p in epath] == path:
                return False
        return True

    def isDiffPath(cbbs, existedPaths):
        for epath in existedPaths:
            if [p[1] for p in epath] == path:
                return False
        return True
    
    logging.info(f"{'='*20} {setting.contractName} {'='*20}")

    os.system(f'rm -rf {setting.pathHookContract}')
    os.system(f'mkdir {setting.pathHookContract}')
    pathOriginContract =  setting.pathBaseContract + setting.contractName
    os.system(f'cp -r {pathOriginContract} ./rt_info/{setting.contractName}')
    pathABI  = setting.pathHookContract + setting.contractName + '/' + setting.contractName + '.abi'
    pathWasm = setting.pathHookContract + setting.contractName + '/' + setting.contractName + '.wasm'
    pathContract = setting.pathHookContract + setting.contractName

    # wasabi
    os.system(f'wasabi {pathWasm} ./out')
    os.system(f'mv ./{setting.contractName}.txt {setting.pathHookContract}')
    os.system(f'mv ./out/{setting.contractName}.wasm {pathWasm}')
    os.system(f'rm -rf ./out')

    # static output
    pathOriginWasm = pathOriginContract + '/' + setting.contractName + '.wasm'
  
    os.system(f'python3 /home/toor/staticAnalyze/octopus/gen_br.py {pathOriginWasm}')
    os.system(f'mv ./bbs.json {setting.pathHookContract}')
    os.system(f'mv ./edges.json {setting.pathHookContract}')
    os.system(f'mv ./instrs.json {setting.pathHookContract}')

    initEosEnv() 
    # vulCBefore= getCurrency(setting.contractName, 'eosio.token')

    abi = ABIObj(pathABI)
    testDataFactory = ArgumentFactory(setting.contractName, abi, setting.contractName, setting.contractName)

    feedbackFactory = FeedbackFactory()

    # actions = entryFilter(actions)
    # iterActions = []
    # max transaction cnt : 3
    # total cnt = n^3 - 2n^2 + 2n
    # for i in range(min(len(actions), 1)): # TODO set 3
    #     iterActions += list(itertools.permutations(actions, i+1))
    

    foundBBsCnt = 0
    # fuzzing each action

    kind = 0
    if kind == 0:
        realContractName = contractName
        realFunctionName = functionName
        realAccountName = accountName

    if kind == 1 :
        realContractName = "eosio.token"
        realFunctionName = "transfer"
        realAccountName = ArgumentFactory.forgedNotificationTokenFromName
    
    elif kind == 2 :
        realContractName = ArgumentFactory.fakeTransferAgentName
        realFunctionName = "transfer"
        realAccountName = ArgumentFactory.fakeTransferAgentName
    
    elif kind == 3 :
        realContractName = "eosio.token"
        realFunctionName = "transfer"
        realAccountName = ArgumentFactory.testEOSTokenFromName
    
    ArgumentFactory.contractName = realContractName

    # realAccountName = ArgumentFactory.realActiveAccount


    # use cleos to push an action
    # pipe.exe = "cleos push action " + realContractName + " " + realFunctionName + " '" +\
    #              ty.testArgument + "' -p " + realAccountName + "@active -f 2>&1"
    
    # pushAction(realContractName, realFunctionName, ArgumentFactory.testArgument(kind) , f'{realAccountName}@active', True)

    testActions = [action['name'] for action in abi.actions] if kind == 0 else [realFunctionName]
    for actionName in testActions:
        touchedBBs = set()
        # ====================== start initlog ========================
        # init transaction with random data
        testDataFactory.generateNewData(actionName, kind)
        testArgumentStr = testDataFactory.testArgument

        os.system("rm %s" % (setting.plogPath))

        logger.debug(f"fuzzing action@{actionName} arg@{testArgumentStr}")

        response = pushAction(realContractName, actionName, testArgumentStr, f'{realAccountName}@active', mustExecute=True, rpsRequired=False)
        if not response:
            logger.info(f"fail to handle action@{actionName}")
            continue
        # inputDataStream = json.loads(response)['processed']['action_traces'][0]['act']['hex_data']
        
        inputDataStream = testDataFactory.serializeJsonStr2Stream(actionName, testArgumentStr)        
        feedbackFactory.processLog() 

        # detect bug
        if feedbackFactory.usedTaposFunctionThenEosioTokenTransfer():
            # success
            logging.info("Tapos Bug")
            pass
            # results.add(true, successExit, realContractName == contractName ? realFunctionName : "transfer", 0, ty.testArgument)
        else:
            # fail
            pass
            # results.add(false, successExit, realContractName == contractName ? realFunctionName : "transfer", 0)
        
        if kind == 1:
            _magic = feedbackFactory.checkForgedNotificationBug(ArgumentFactory.forgedNotificationAgentName, setting.contractName)
            if _magic == 1:
                pass # success
                logging.info("Fake Transfer")
                # results.add(true, successExit, "transfer", kind, ty.testArgument)
                # logger.log("Has forged notification bug")
                # logger.log("Check forged notification bug")
            
            elif _magic == 0:
                # results.add(false, successExit, "transfer", kind)
                pass

        elif kind == 2:
            if feedbackFactory.hasFakeTransferBug(ArgumentFactory.fakeTransferAgentName, setting.contractName):
                # results.add(true, successExit, "transfer", kind, ty.testArgument)
                # logger.log("Has fake transfer bug")
                #success
                logging.info("Fake EOS kind=2")
                pass
            else:
                pass
                # results.add(false, successExit, "transfer", kind)
        
        elif kind == 3:
            acceptEOSToken = feedbackFactory.acceptEOSToken() #|| pipe.find("3080006: Transaction took too long")
            if acceptEOSToken:
                # success
                pass
                # logger.log("Accept EOS token")
                logging.info("Fake EOS kind=3")
            else:
                pass
                # logger.log("Not accept EOS token")
            # pipe.exe = "cleos"
            # pipe.args = "get currency balance eosio.token " + contractName + " EOS"
            # pipe.execute()
            # if(pipe.output.size() == 1) :
            #     originBalance = eosio::chain::asset::from_string(pipe.output[0])
            
        # compare currency
        # =========================== end bug detect =======================================

    
        basicblocks = feedbackFactory.genBasicblocks()
        for bb in basicblocks:
            touchedBBs.add(bb.name)
        cbrs = feedbackFactory.calConfm(basicblocks, touchedBBs)
        path = [cbr[0] for cbr in cbrs]
        cpathVal = sum([cbr[1] for cbr in cbrs])
        allPaths = [cbrs]
        # ====================== end initlog ========================

        # init queue
        pqueue = PriorityQueue()
        initNode = Node(seed=inputDataStream, cbbVal=cpathVal, path=path)
        pqueue.push(initNode)
        
        # analyze log & update touchedBBs
        while fuzzerCount >= 0 and not pqueue.empty():
            # print('cnt:', fuzzerCount)
            fuzzerCount -= 1
            # allPaths = [item.path for item in pqueue._queue]
            
            # detect each node once
            if feedbackFactory.exploitDetector(basicblocks):
                print('[+] Fake EOS Found')
                print('[+] ================== Found Vulnerability ==================')
                break
            
            qhead = pqueue.pop() # contain the highest conformance
            for seed in qhead.seeds.copy():   
                # mutating one existed seed and generate logs
                brPtys = brPriority()
                for mseed in mutateSeeds(brPtys, qhead, inputDataStream):
                    try:    
                        testArgumentStr = testDataFactory.deserializeStream2JsonStr(actionName, mseed)
                    except:
                        exit(0)
                        logger.warning(f"Can't serialize data@\{{{mseed}}}")
                        continue
                    # mseed = excuteTx(pathContract, tx, seed)
                    # excuteTx(pathContract, tx, mseed)
                    
                    # mutate
                    # testDataFactory.generateNewData(action['name'], 3)
                    # testArgumentStr = testDataFactory.testArgument
                    
                    # rpsJson = json.loads(response)
                    # inputDataStream = rpsJson['processed']['action_traces'][0]['act']['hex_data']

                    # print('===================', inputDataStream, '='*10)
                    # exit(0)

        
                    os.system("rm %s" % (setting.plogPath))
                    
                    pushAction(setting.contractName, actionName, testArgumentStr, 'eosio', mustExecute=True, rpsRequired=False) 
                
                    # feedback phase
            
                    feedbackFactory.processLog() 
                
                    basicblocks = feedbackFactory.genBasicblocks()
                    for bb in basicblocks:
                        touchedBBs.add(bb.name)
                    cbrs = feedbackFactory.calConfm(basicblocks, touchedBBs)
                    path = [cbr[0] for cbr in cbrs]
                    cbbs = [cbr[1] for cbr in cbrs]
                    cpath = sum(cbbs)
                    
                    
                    # touched all branches already
                    if cpath == 0:
                        continue
                    # updating priority queue according to GREYONE
                    if isNewPath(path, allPaths):
                        logger.debug(f"Find new path by calling action@{actionName}:data@{testArgumentStr}")
                        pqueue.push(qhead)
                        pqueue.push(Node(seed=mseed, cbbVal=cpath, path=path))
                    else:
                        if cpath > qhead.cbbVal:
                            logger.debug(f"Find path with larger cbbVal by calling action@{actionName}:data@{testArgumentStr}")
                            
                            pqueue.push(Node(seed=mseed, cbbVal=cpath, path=path))
                        elif cpath == qhead.cbbVal and cbbs in allPaths: # and Cbranch different
                            logger.debug(f"Find path with the same cbbVal")
                            qhead.seeds.append(mseed)
                            pqueue.push(qhead)
                        else:
                            logger.debug(f"Find path with smaller cbbVal")
                            # do nothing for nodes with lower comformance
                            # pqueue.push(qhead)
            
                    allPaths.append(cbrs)
        
        foundBBsCnt += len(touchedBBs)
    

    logger.info(f"Visited {foundBBsCnt}/{feedbackFactory.userBlocksCnt} basicblocks")



    
    
    


def entryFilter(path):
    # TODO
    return True
    '''
    static analyze:
        旧思路：
        1. 分析每一个function最终使用到的库函数
        2. 检查库函数内容, 如果只是打印了一下则过滤
        新思路：
        事实上显示的log用户也看不到。。所以只分析那些允许用户调用的就好了
    '''
    with open(setting.importsFuncPathBase + '/' + setting.contractName + '.txt', 'r') as f:
        lines = f.readlines()
        importsCnt, applyFuncId = int(lines[0]), int(lines[1])
        importsFunc = lines[2:]
    func_id = -1
    tmp = path[::-1]
    for idx, bb in enumerate(tmp):
        fid = utils.getBBFuncId(bb)
        if fid == applyFuncId:
            func_id = tmp[idx + 1]
            break
    
    with open(setting.instrsJsonPath, 'r') as f:
        staticinstrs = json.load(f)
    with open(setting.edgesJsonPath, 'r') as f:
        staticedges = json.load(f)

    touched = set()
    queue = list()
    for node, to_nodes in staticedges.items(): 
        if utils.getBBFuncId(node) == func_id:
            queue += to_nodes
    
    while queue and not isTest:
        head = queue.pop(0)
        if head in touched:
            continue
        for instr in staticinstrs[head]:
            if instr in ['call 0']: # TODO filter
                return True
        touched.add(head)
        queue.append(staticedges[head])

    return False

    # read all basicblocks of this entry invoked
    # extract all function_id
    # remove those without any sensitive libary functions 


def mutateSeeds(brPtys, node, tmp):
    # process log generate several action_data
    ''' 
    # random part
    mutSeed = seed.copy()
    for argument in mutSeed:
        if 'int' in argument['type']:
            argument['value'] += 1
        elif 'asset' == argument['type']:
            origin = float(argument['value'].split(' ')[0]) 
            new = origin + 1
            argument['value'] = '%.4f EOS' % (new)
    # print(mutSeed)
    '''
    # direct-copy TODO
    actionDataList = [tmp,
                      tmp]
    return actionDataList

def brPriority(logPath='./log.txt'):
    # TODO read log and calculate priority for each branch
    
    return [(0, 1)]

'''
def genInitLog(pathContract, tx, seed):
    # init for each transaction :# genInitLog(pathContract, tx, initSeed)   
    # params = "["
    # for item in seed:
    #     if 'float' in item['type'] or 'int' in item['type']:
    #         params += str(item['value']) + ',' 
    #     else:
    #         params += '\"' + item['value'] + '\"' + ','
    # params = params[:-1] + "]"
    # print("[-] params:", params, 'action:', tx['name'])


    # generate wasabi log

    os.system("rm %s" % (setting.plogPath))
    pushAction(setting.contractName, tx['name'], params, 'eosio', False)
    processLog() # remove libary functions

def geninitSeed(fields):
    # generate the inital seed : initSeed = geninitSeed(tx['fields'])
    
    preDefined = {'name':"bob", 'string':"payback", 'asset':"1.0000 EOS",'int8':'a', 'int32':0, 'float32':0.0, 'float64':0.0}
    seed = [{'name':field['name'],'type': field['type'],'value':preDefined[field['type']]} for field in fields]
    return seed


def excuteTx(pathContract, tx, mseed):
    # init for each transaction
    # init(setting.contractName)

    # vulCBefore = getCurrency(setting.contractName, 'eosio.token')
    # for tx in txs:
    #     pushAction(setting.contractName, tx['name'], '["testeosfrom","1000.000 EOS"]', 'eosio', False)
    
    params = "["
    for item in mseed:
        if 'float' in item['type'] or 'int' in item['type']:
            params += str(item['value']) + ',' 
        else:
            params += '\"' + item['value'] + '\"' + ','
    params = params[:-1] + "]"

    # print("[-] params:", params, 'action:', tx['name'])

    os.system("rm %s" % (setting.plogPath))
    pushAction(setting.contractName, tx['name'], params, 'eosio', True) # generate log
    processLog() # remove libary functions

    # pushAction(setting.contractName, 'hi', '["testeosfrom","1000.000 EOS"]', 'eosio', False)
    # pushAction(setting.contractName, 'payme', '["testeosfrom", "1000.0000 EOS", "payback",1]', 'eosio', True)

    # verify currency
    # vulCAfter = getCurrency(setting.contractName, 'eosio.token')
    # cruyAtk = getCurrency('testeosfrom', 'eosio.token')
    # print('dddd', vulCBefore, vulCAfter, cruyAtk)
    # if vulCBefore > vulCAfter:
    #     print("[+] Attack Success")
    #     return True
    # else:
    #     return False
'''




'''
cleos get table ${field} ${contract} ${table}
{
  "rows": [{
      "account": "account",
      "balance": 50
    }
  ],
  "more": true
}
'''