import json
import subprocess
import binascii
import struct
import os
import time
import collections

import symzzer.setting as setting
from symzzer.setting import logger

from symzzer.basicBlock import BasicBlock, Instruction
import symzzer.utils as utils

from symzzer.log import singleLogBin2Json
from symzzer.utils import EOSPonserException


class FeedbackFactory(object):
    def __init__(self):
        self.invalidCount = 0
        self.acceptEOSToken = False
        # =================== static info ======================
        self.customTable = ["start","call_post","begin_function","begin_block","begin_loop","begin_if","begin_else","end_function","end_block","end_loop","end_if","end_else"]
        self.opcodeSetLen = 173
        self.sideEffectsFuncs = setting.SIDE_EFFECTS

        with open(f'{setting.pathHookContract}/{setting.contractName}.txt', 'r') as f:
            lines = f.readlines()
            self.importsCnt, self.applyFuncId = int(lines[0]), int(lines[1])
            self.importsFunc = [line.strip() for line in lines[2:]]
            self.importsFuncDict = collections.defaultdict(list)
            for idx, funcName in enumerate(self.importsFunc):
                self.importsFuncDict[funcName] = idx
    

        self.logScope = list()
        # self.healthyFuncPath =list()

        self.dbFlow = collections.defaultdict(list)
        self.rdb = collections.defaultdict(list)

        self.seedDict = collections.defaultdict(list)
        self.touchedBrs = collections.defaultdict(set)
        #================ cahce ==============
        self.name2uint64Cache = dict()
        
        self.transferEntry = -1
        self.firstActLog = []
        self.firstActPos = -1
        self.firstActEntry = -1
        self.usedFuncList = []
        # ======================== end ============================ 
        self.cmds = list() # for debug

    def initSession(self):
        self.logScope = list()
        self.firstActLog = []
        self.firstActPos = -1
        self.firstActEntry = -1

    def seeds(self, kind, function):
        funcSeeds = self.seedDict[(kind, function)] # ref
        
        if len(funcSeeds) > 0:
            t = funcSeeds.pop()
        else:
            t = []

        if t != []: # DFS
            funcSeeds.insert(0, t)
            return t[1]
        else:
            return []

    def extendSeeds(self, kind, function, newSeeds):  
        self.seedDict[(kind, function)].extend([(loc, json.dumps(arg)) ])
        self.touchedBrs[(kind, function)].update([loc for loc, _, _ in newSeeds])


    def isImportFunc(self, fid):
        if fid < len(self.importsFunc):
            return self.importsFunc[fid]
        else:
            return None
    
    def getFuncPath(self):
        # checking the first action
        with open(setting.plogPath, 'r') as f:
            lines = json.load(f)[:self.logScope[0]]
        # apply() -> action1() -> __apply()
        funcList = list()
        for line in lines:
            _, _, args, _ = line
            func = args[0]

            if not funcList or funcList[-1] != func:
                # if func == self.applyFuncId and self.applyFuncId in funcList:
                #     break
                funcList.append(func)
            else:
                continue

        return funcList

  
    def processLog(self, flag=True):
        self.initSession()
        # empty dir
        logsNames = os.listdir(setting.logPath)
        if not logsNames:
            return False
        print('[-] logAnalyzer.processLog():: ', os.listdir(setting.logPath))

        # sort by execution order
        logs = sorted(logsNames, key=lambda fname: int(fname[4:-4]))
        for singleLogPath in logs: 
            plogList, indirectPos = singleLogBin2Json(f'{setting.logPath}/{singleLogPath}') # byte -> json
            
            # cannot find call_indirect
            if indirectPos == -1:
                continue

            print('[-] _processLog:', indirectPos, plogList[indirectPos], plogList[indirectPos+1], plogList[-1]) 
            self.logScope.append(len(plogList))
            self.firstActLog = plogList
            self.firstActPos = indirectPos 
            self.firstActEntry = plogList[indirectPos+1][2][0] # the action id 
            with open(setting.plogPath, 'w') as f:
                json.dump(plogList, f)
            break
        
        # print("[-] cannot find an executed action\n\n")
        if not self.logScope:
           return False
        else:
            return True
        
    def getTransferEntry(self):
        print(os.listdir(setting.logPath))
        _ = self.processLog()
        if self.firstActPos == -1 or self.firstActLog == []:
            print(f'[-] no eosponser !!!')
            raise EOSPonserException
            # raise RuntimeError("Cannot find Action Entry for eosponser")
 
        self.transferEntry = self.firstActEntry
        print(f'[+] ======= eosponser:{self.transferEntry} ==')


    '''
     * @description: Check a log including tapos functions.
     * @param
     *      -
     * @return: True if it includes.
    '''
    def usedTaposFunctionThenEosioTokenTransfer(self):
        taposFuncs = {"tapos_block_num", "tapos_block_prefix"}
        print("[-]:::", self.usedFuncList)
        return True if len(self.usedFuncList) > 0 and len(taposFuncs & set(self.usedFuncList)) > 0 else False

    '''
     * @description: Check an inline action is invoked.
     * @param
     *      -
     * @return: True if it includes.
    '''
    def rollback(self):
        print('\n\n=============================')
        print(self.usedFuncList)
        print('=============================\n\n')
        return "send_inline" in self.usedFuncList


    def authCheckFault(self):
        print('\n\n=============================')
        print(self.usedFuncList)
        print('=============================\n\n')
        require_auth = ['has_auth', 'require_auth', 'require_auth2']
        safe = False
        for func in self.usedFuncList:
            if func in self.sideEffectsFuncs and safe == False:
                return True
            elif func in require_auth:
                safe = True
                break
        return False



    def name2uint64(self, nameStr):
        def char_to_value(c):
            if c == '.':
                return 0
            elif c >= '1' and c <= '5':
                return int(c)
            elif c >= 'a' and c <= 'z':
                return (ord(c) - ord('a')) + 6
            return 0

        if nameStr in self.name2uint64Cache:
            return self.name2uint64Cache[nameStr]

        s = nameStr
        v = 0
        n = len(s) if len(s) < 12 else 12
        for i in range(n):
            v <<= 5
            v |= char_to_value(s[i])

        v <<= (4 + 5 * (12 - n))
        if len(s) == 13:
            v1 = char_to_value(s[12])
            v |= v1

        # if v > 2**63 - 1:
        #     v = v - 2**64
        self.name2uint64Cache[nameStr] = v
        return v 


    '''
    寻找action位置，如果为transfer则返回 eosponse
    '''
    def locateActionPos(self, index=0, txFuncName=':ALL'):
        self.caseInfo = None
        self.usedFuncList = []

        # only check the first action
        if index == 0:
            lines = self.firstActLog
            size = len(lines)
            currentActionId = self.firstActEntry
            startPos = self.firstActPos + 1 # begin_function

        else:
            with open(setting.plogPath, 'r') as f:
                lines = json.load(f)[self.logScope[index-1]:self.logScope[index]]
            size = len(lines)
            startPos = 0
            currentActionId = -1
            while startPos < size:
                _, instr, args, _ = lines[startPos]
                if 'call_indirect' in instr:
                    startPos += 1
                    currentActionId = lines[startPos][2][0]
                    break
                startPos += 1
            if currentActionId == -1:
                raise RuntimeError("lost action entry")
        

        sensitiveFuncList = list()
        # extracting traces of the current action
        endPos = startPos + 1
        callStack = [currentActionId]
        while endPos < size:
            _ , instr , args, types = lines[endPos]
            # print('--debug-- @feedback:args=', args, '\nline=', lines[endPos])
            if args == []:
                endPos += 1 # ignore
                continue

            func = args[0]
            if instr == 'begin_function':
                callStack.append(func)
            elif instr == 'end_function':
                callStack.pop()
                if not callStack:
                    print('[-] logAnalyzer.locateActionPos::', lines[startPos], lines[endPos])
                    break

            elif instr == 'call':
                # print(lines[endPos])
                target = args[2]
                # print('---', target)
                funcName = self.isImportFunc(target)
                # print('--------> ', funcName)
                if funcName:
                    self.usedFuncList.append(funcName)
                    if funcName in self.sideEffectsFuncs:#or funcName.startswith('db_')  or target > self.applyFuncId ):
                        #and not funcName.startswith('db_find_')
                        sensitiveFuncList.append(funcName)
                
                    # table handle
                    if funcName.startswith('db_'):
                        # print(funcName,' ')
                        fargs = args[3:] 
                        if funcName.startswith('db_find'):
                            code, scope, table, =  [ (fargs[i*2+1] << 32) | fargs[i*2]  for i in range(0, 3)]
                            if table not in self.dbFlow:
                                self.dbFlow[table] = {"r":[], "w":[]}
                            self.dbFlow[table]['r'].append(txFuncName)

                            if txFuncName not in self.rdb:
                                self.rdb[txFuncName] = [table]
                            else:
                                self.rdb[txFuncName].append(table)

                        elif funcName.startswith('db_store'):
                            scope, table = [ (fargs[i*2+1] <<32) | fargs[i*2]  for i in range(0, 2)]
                            if table not in self.dbFlow:
                                self.dbFlow[table] = {"r":[], "w":[]}
                            self.dbFlow[table]['w'].append(txFuncName)

                        else:
                            # tion: db_get_i64 in initgame
                            pass
                            # print(f'[-] debug ignore dbfunction: {funcName} in {txFuncName}')
                        '''
                        db constrains
                        '''
            else:
                pass
            endPos += 1

        # 收集eosponse信息
        self.caseInfo = (startPos, endPos, currentActionId, sensitiveFuncList)
        print("==============================================================")
        print("[-] Sensitive Funcs:", sensitiveFuncList)
        # exit(0)
        '''
        indirect_call
        function_start      # starPos ----+
        ...                               | the scope of action function
        function_end        # endPos -----+
        ...
        '''
        if False:
            for item in lines[startPos-1:endPos+10]:
                print(item)
            print(sensitiveFuncList)
            exit(0)
        


    '''
     * @description: Check a operation list checking _self and to.
     * @param
     *      attacker: the string of attacker's account.
     *      attackee: the string of attackee's aacount.
     * @return: True if it checked.
    '''
    '''
    apply() ------>  any action  -----> apply()
                  |   ...       |
                  | _self != to |
                  | side-effects|
                  |   ...       |
    1. side effect & no check
    2. cover mostly & no check
    3. check    
    '''
    def checkForgedNotificationBug(self, attackerString, attackeeString, isExecuted):
        startPos, endPos, currentActionId, sensitiveFuncList = self.caseInfo
        if currentActionId != self.transferEntry:
            return -1 # keep trying

        lines = self.firstActLog
        # in first action, contract is safe with (to != self / !(to == self))
        a = self.name2uint64(attackerString)
        b = self.name2uint64(attackeeString)

        # tmpidx = 0
        for tmpidx, item in enumerate(lines[startPos:endPos]):
            _ , instr , args, _ = item
            if args[0] != self.transferEntry:
                continue
            
            if instr in ['i64.ne', 'i64.eq']:
                operand1 = args[3]<<32 | args[2] 
                operand2 = args[5]<<32 | args[4] 
                # _res = args[6]
                if ((a, b) == (operand1, operand2) or (a, b) == (operand2, operand1)):
                    # print(item, '\n----------------------')
                    logger.info(f'Fake Notification has fix:: ' +\
                        f'action@{currentActionId}:row_{args[1]} checks to({a}) != _self({b})')

                    return 0

                    # debug
                    if False:
                        for kk in lines[startPos-1:startPos+ tmpidx + 20]:
                            print(kk)
              
                        touchInstrCnt = 0
                        for line in lines[startPos:endPos+1]:
                            if line[1] not in self.customTable and line[2][1] != 0xffffffff:
                                # print(line)
                                # touchedInstr.add(tuple(line[2][:2]))
                                touchInstrCnt += 1
                        print(touchInstrCnt)
                        exit(0)
        
        # try to generate side effects
        if sensitiveFuncList:
            print('=======================', sensitiveFuncList)
            print(f'++++++++++++++===Found Fake Notification:: action@{currentActionId}: no check to != _self, but execute functions:{sensitiveFuncList}', currentActionId)
            logger.info(f'Found Fake Notification:: ' +\
                f'action@{currentActionId}: no check to != _self, but execute functions:{sensitiveFuncList}')
            return 1

        return -1

    def findATKFakeNotif(self, attackerString, attackeeString):
        startPos, endPos, currentActionId, sensitiveFuncList = self.caseInfo
        if currentActionId != self.transferEntry:
            return -1 # keep trying
        lines = self.firstActLog
        # in first action, contract is safe with (to != self / !(to == self))
        a = self.name2uint64(attackerString)
        b = self.name2uint64(attackeeString)
        hasCheck = False
        for tmpidx, item in enumerate(lines[startPos:endPos]):
            _ , instr , args, _ = item
            if args[0] != self.transferEntry:
                continue  
            if instr in ['i64.ne', 'i64.eq']:
                operand1 = args[3]<<32 | args[2] 
                operand2 = args[5]<<32 | args[4] 
                _res = args[6]
                if ((a, b) == (operand1, operand2) or (a, b) == (operand2, operand1)):
                    # bug fixed
                    return (args[0], args[1])
        return ()

    '''
     * @description: Check a operation list calling an user's function after excuating apply()
     * @param
     *      -
     * @return: True if it has.
     *********************************
     apply() -> one user's function(action)
    '''

    def loacteActionEntry(self, lines, _actioName):
        '''
        i64.const uint64_t( action_name )   # 
        local.get 2                         # lines[_prePox-1]
        i64.eq                              # lines[_prePox]
        ...
        call entry                          # lines[startPos]
        '''
        actioNameUint64 = self.name2uint64(_actioName)
        
        size = len(lines)
        startPos = 0

        while startPos < size:
            _ , instr , args, _ = lines[startPos]
            # print('starpos=', startPos)
            # apply() prepare to execute one action
            if 'call' == instr and args[0] == self.applyFuncId:
                entry = args[2]
                _prePox = startPos - 1
                while _prePox > 0 and startPos - _prePox < 64:
                    _, _instr, _args, _ = lines[_prePox]
                    if _instr == 'i64.ne':
                        operand1 = _args[3]<<32 | _args[2] 
                        operand2 = _args[5]<<32 | _args[4] 
                        if actioNameUint64 == operand1 == operand2:
                            break
                    _prePox -= 1
                tmp1 = lines[_prePox-1]
                tmp2 = lines[_prePox-2]
                # print(tmp1, tmp2)
                if tmp1[1] == 'local.get' and tmp1[2][2] == 2: # ..., uint64_t action, ...
                    return startPos
                elif tmp2[1] == 'local.get' and tmp2[2][2] == 2: # ..., uint64_t action, ...
                    return startPos
                else:
                    pass
            
            startPos += 1
        return None

    def hasFakeTransferBug(self):# never increase balance
        startPos, endPos, currentActionId, _ = self.caseInfo
        print("[-] in hasFakeTransferBug()::", self.caseInfo, self.transferEntry)
        if currentActionId != self.transferEntry:
            return False # keep trying
        else:
            logger.info(f'Fake EOS. After passing the checks in the apply(), action:{currentActionId} was excuted')
            return True

    def exploitDetector(self,basicblocks, kind, isExecuted, isVulBalance):
        # detect bug
        self.invalidCount += 1
        if self.usedTaposFunctionThenEosioTokenTransfer():
            # success
            logging.info("Tapos Bug")
            return True
            # results.add(true, successExit, realContractName == contractName ? realFunctionName : "transfer", 0, ty.testArgument)
        # payload increases the balance of the fuzzing contract
        if not isVulBalance: 
            return False
        
        if kind == 1:
            _magic = self.checkForgedNotificationBug(setting.forgedNotificationAgentName, setting.contractName, isExecuted)
            if _magic == 1:
                logger.info("Fake Notification")
                return True

        elif kind == 2 or kind == 3:
            if self.hasFakeTransferBug():
                self.acceptEOSToken = True
                # results.add(true, successExit, "transfer", kind, ty.testArgument)
                # logger.log("Has fake transfer bug")
                logger.info(f"Has fake transfer bug;Fake EOS kind={kind}")
                return True

        # compare currency
        # =========================== end bug detect =======================================
        return False
    
    
    '''
    插入 hard-constraint
    '''
    def injectConstraint(self, argTypes):# never increase balance
        _, _, currentActionId, _ = self.caseInfo
        eosassertFID = self.importsFuncDict['eosio_assert']
        if eosassertFID == []:
            eosassertFID = len(self.importsFunc)
            # inject eosio_assert()
        
        constraints = list()
        for idx, argType in enumerate(argTypes):
            if re.search(r'^[u]int\d+$', argType):
                snipt =  f'get_local {idx+1}'
                snipt += f'i32.const 0'
                snipt += f'i32.eq'
                snipt += f'i32.const 0'
                snipt += f'call {eosassertFID}'
            
            elif re.search(r'^float\d+$', argType) or re.search(r'^double\d+$', argType):
                snipt =  f'get_local {idx+1}'
                snipt += f'i32.const 0'
                snipt += f'f32.eq'
                snipt += f'f32.const 0'
                snipt += f'call {eosassertFID}'

            elif re.search(r'name', argType):
                snipt =  f'get_local {idx+1}'
                snipt += f'i64.const 0'
                snipt += f'i64.eq'
                snipt += f'i64.const 0'
                snipt += f'call {eosassertFID}'

