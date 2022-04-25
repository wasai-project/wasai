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
        
        # for basicblock. now dropped
        # with open(setting.bbsJsonPath, 'r') as f:
        #     self.staticBBs = json.load(f)
        # self.userBlocksCnt = 0
        # for fid, bbs in self.staticBBs.items():
        #     if int(fid) > self.applyFuncId:
        #         self.userBlocksCnt += len(bbs)

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

    # def _processLog(self, flag):


    # def _processLog(self, flag):
    #     self.logScope = list()
    #     logs = os.listdir(setting.logPath)
    #     logs = sorted(logs, key=lambda fname: int(fname[4:-4]))

    #     rt = list()
        
    #     for singleLogPath in logs: 
    #         plogList, indirectPos = singleLogBin2Json(f'{setting.logPath}/{singleLogPath}') # byte -> json
    #         if indirectPos == -1:
    #             continue

    #         print('[-] _processLog:', singleLogPath,  indirectPos, plogList[indirectPos], plogList[indirectPos+1]) 
    #         # print(plogList)
    #         # rt += plogList
    #         # self.logScope.append(len(plogList))
    #         # break # maybe we just need the trace of the first action 

    #         if flag:
    #             try:
    #                 beg = (plogList[0][1], plogList[0][2][0])
    #                 end = (plogList[-1][1], plogList[-1][2][0])
    #                 if (beg[0], end[0]) == ('begin_function', 'end_function') and beg[1] == end[1]:
    #                     rt += plogList
    #                     self.logScope.append(len(plogList))
    #                     break # maybe we just need the trace of the first action 
    #             except:
    #                 pass
    #         else:
    #             rt += plogList
    #             self.logScope.append(len(plogList))
    #             break # maybe we just need the trace of the first action 

    #     if len(self.logScope) == 0:
    #         plogList, indirectPos = singleLogBin2Json(f'{setting.logPath}/{logs[0]}') # byte -> json
    #         rt += plogList
    #         self.logScope.append(len(plogList))


    #     self.firstActLog = rt[:self.logScope[0]]
    #     self.firstActPos = indirectPos        # the idx of call_indirect in logs[]
    #     self.firstActEntry = self.firstActLog[self.firstActPos + 1][2][0] # the action id 
    #     # print("[-] ---process log:", self.firstActPos,  self.firstActLog )
    #     # map actions
    #     # print('- ', self.firstActEntry)
    #     with open(setting.plogPath, 'w') as f:
    #         json.dump(rt, f)
    #     if not rt:
    #         raise RuntimeError("Empty Log")
        

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

        # if setting.isMeasureCoverage:
        #     # for calculating coverage
        #     clogs = sorted(logs, key=lambda fname: int(fname[4:-4]))
        #     currentTime = time.time()
        #     # copy in raw
        #     for idx, p in enumerate(clogs):
        #         fName = str(currentTime + 0.0000001 * idx) + '.txt'
        #         os.system(f"cp {setting.logPath}/{p} /devdata/cwmdata/symzzerDataset/articles/{setting.contractName}/{fName}")


        # parse bin to json
        # _cnt = 1
        # try:
        #     self._processLog(flag)
        # except:
        #     pass
        # while _cnt >= 0:
        #     try:
        #         self._processLog(flag)
        #         break
        #     except:
        #         _cnt -= 1
        #         time.sleep(1)

        # return False if _cnt < 0 else True
        

    def genBasicblocks(self):
        #  instruction_name [func_id, instr, arg1, agr2...] [type1,type2...]
        with open(setting.plogPath, 'r') as f:
            lines = json.load(f)

        # with open(setting.edgesJsonPath, 'r') as f:
        #     staticEdges = json.load(f)

        # split bb by the order of execution
        basicblocks = []

        # enumerate blocks
        new_block = True
        for line in lines:
            instrution = Instruction(line[0], line[1], line[2], line[3]) # opcode, name, args, targs
            ridx = instrution.related_idx
            inst = instrution.name
            fid = instrution.function_id
            if str(fid) not in self.staticBBs:
                continue
            # creation of a block
            if new_block:
                block = BasicBlock(start_offset=ridx, start_instr=inst, name=utils.format_bb_name(fid, ridx))
                new_block = False
            # add current instruction to the basicblock
            block.instructions.append(instrution)
            if ridx < 1024: #TODO remove new opcode
                for bs, bn, toNodes in self.staticBBs[str(fid)]:
                    if ridx == bn: # locate one bb
                        new_block = True
                        block.to_nodes = [node for node in toNodes if utils.getBBFuncId(node) >= self.applyFuncId ]
                        break

            if new_block:
                block.end_offset = ridx
                block.end_instr = inst
                basicblocks.append(block)
                new_block = True
        return basicblocks


    def calConfm(self, basicblocks, touchedBBs):
        # paths=[bb.name for bb in basicblocks]
        # fbCase = Feedback(path=[bb.name for bb in basicblocks])
        cBlockVal = 0
        cbrs = []
        for idx, bb in enumerate(basicblocks):
            # print(bb.name, basicblocks[idx+1].name,bb.to_nodes)
                # [node for node in bb.to_nodes if node in touchedBBs], [node for node in bb.to_nodes if node not in touchedBBs], '\n-------------')
            # continue
            if bb.end_instr in ['br_if', 'if', 'br_table']:
                toNodes = [node for node in bb.to_nodes if node not in touchedBBs]
                # print(toNodes)
                oprand1, oprand2 = bb.instructions[-2].args[-2:]
                cbr = len(toNodes) * utils.num1bits(oprand1 ^ oprand2)
                cBlockVal += cbr
                
                cbrs.append((bb.name, cbr))
            else:
                cbrs.append((bb.name, 0))

        # print(cBlockVal)
        # print('========== cpath', cBlockVal)
        # print('===========\n', len(touchedBBs))
        logger.debug(f"get the CBB of current path: val@{cBlockVal}")

        '''
        start: 'block', 'loop', 'if', 'else'
        end  : 'else', 'end', 'return'
        loop_out : 'br', 'br_if', 'br_table'
        '''
        return cbrs
        
    def evolute(self, stream):
        return []

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

        # analyzing every action
        # check all actions
        '''
        startPos, endPos, currentActionId, sensitiveFuncList = self.caseInfo
        lines = self.firstActLog
        # in first action, contract is safe with (to != self / !(to == self))
        a = self.name2uint64(attackerString)
        b = self.name2uint64(attackeeString)
        hasCheck = False
        # tmpidx = 0
        for tmpidx, item in enumerate(lines[startPos:endPos]):
            _ , instr , args, _ = item
            if args[0] != self.transferEntry:
                continue

        with open(setting.plogPath, 'r') as f:
            lines = json.load(f)
            size = len(lines)

        isPermissionCheck = False
        idx = 0
        while idx < size:
            _, instr, args, _ = lines[idx]
            if instr == 'call':
                funcName = self.isImportFunc(args[2])
                if funcName != None and funcName in require_auth:
                    isPermissionCheck = True
                    logger.info(f"Permission Checking: The action:{args[0]} executes \'{funcName}\'")
                    return False

                if funcName != None and funcName in ['send_inline', 'send_deferred', 'db_store_i64', 'db_update_i64', 'db_remove_i64'] and isPermissionCheck == False:
                    logger.info(f"Missing Permission Checking Vulnerability: The action:{args[0]} executes \'{funcName}\'")
                    return True
            idx += 1

        return False
        '''



    def uint2name(self, value):
        charmap = ".12345abcdefghijklmnopqrstuvwxyz"
        str = 13 * ["."]
        tmp = value
        i = 0
        while i <= 12:
            c = charmap[tmp & (0x0f if i == 0 else 0x1f)]
            str[12-i] = c
            tmp >>= (4 if i == 0 else 5)
            i += 1
        return ''.join(str).rstrip(".")

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
        os.system('rm /tmp/tmpName2Hex.txt')
        _magic = subprocess.call(["node", setting.name2HexBin, f"--data={nameStr}"])
        if _magic != 0:
            logger.fatal(f"Fail to serialize : {nameStr}")
            print('fall')
            raise RuntimeError("Fail to deserialize")
        with open('/tmp/tmpName2Hex.txt', 'r') as f:
            data = f.readline().strip()
                
        uint64Data = struct.unpack('<Q', binascii.unhexlify(data))[0]
        self.name2uint64Cache[nameStr] = uint64Data
        # print('..end...')
        return uint64Data
        '''



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
                funcName = self.isImportFunc(target)
                # print('---', target, '->', funcName)
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

                        # elif funcName.startswith('db_update'):
                        #     itr, player = [fargs[i*2+1] <<32) | fargs[i*2]  for i in range(0, 2)]
                        #     self.dbFlow[table]['w'].append(txFuncName)
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
        # print('\n\n\n---------------- fake notif -------------------')
        # print(sensitiveFuncList)
        # print(self.usedFuncList)
        # for item in self.firstActLog[self.firstActPos:]:
        #     print(item)
        # print('-----------------------???------------------------\n')

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
                        iii = 0
                        for kk in lines[startPos-1:startPos+ tmpidx + 20]:
                            print(kk)
                            # if iii == 20:
                                # print('-------------')
                            iii+=1
                        # print(sensitiveFuncList)

                        # ouchedInstr = set()
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
        '''
        # don't find (to != self / !(to == self))
        funcEndOffset = max([item[1] for item in self.staticBBs[str(currentActionId)]])
        if funcEndOffset == 0:
            return -1
        # executedIntrs = list()
        # for line in lines[startPos:endPos+1]:
        #     # if line[0] >= self.opcodeSetLen:
        #     #     continue
        #     func, offset = line[2][:2]
        #     if func == currentActionId and offset <= funcEndOffset \
        #         and offset not in executedIntrs:
        #         executedIntrs.append(line[2][1])

        touchInstrCnt = 0
        for line in lines[startPos:endPos+1]:
            # print(line)
            if line[1] not in self.customTable and line[2][1] != 0xffffffff and line[2][0] == currentActionId:
                # print(line)
                touchInstrCnt += 1
        
        if touchInstrCnt >= 256 or touchInstrCnt >= setting.forgedPerct * funcEndOffset:
            logger.info(f'Found Fake Notification:: ' +\
                f'action@{currentActionId}: execute too much instruction:{touchInstrCnt}:{touchInstrCnt / funcEndOffset}% code')
            return 1

        # keep going
        return -1
        '''


    def checkForgedNotificationBug1(self, attackerString, attackeeString, isExecuted):
        startPos, endPos, currentActionId, sensitiveFuncList = self.caseInfo
        if currentActionId != self.transferEntry:
            return -1 # keep trying

        lines = self.firstActLog
        # in first action, contract is safe with (to != self / !(to == self))
        a = self.name2uint64(attackerString)
        b = self.name2uint64(attackeeString)
        hasCheck = False
        tmpidx = 0
        for item in lines[startPos:endPos]:
            _ , instr , args, _ = item
            # print(item)
            if instr in ['i64.ne', 'i64.eq']:
                operand1 = args[3]<<32 | args[2] 
                operand2 = args[5]<<32 | args[4] 
                _res = args[6]
                if ((a, b) == (operand1, operand2) or (a, b) == (operand2, operand1)):
                    hasCheck = True
                    # safe
                    logger.info(f'Fake Notification has fix:: ' +\
                        f'action@{currentActionId}:row_{args[1]} checks to({a}) != _self({b})')
                    # print(a,attackerString ,b,attackeeString, '\n=============')
                    # print(item, '\n----------------------')
                    # exit(0)
                    if True:
                        iii = 0
                        for kk in lines[startPos + tmpidx - 25 :startPos+ tmpidx + 20]:
                            print(kk)
                            if iii == 20:
                                print('-------------')
                            iii+=1
                        print(sensitiveFuncList)

                        # ouchedInstr = set()
                        touchInstrCnt = 0
                        for line in lines[startPos:endPos+1]:
                            if line[1] not in self.customTable and line[2][1] != 0xffffffff:
                                # print(line)
                                # touchedInstr.add(tuple(line[2][:2]))
                                touchInstrCnt += 1
                        # funcEndOffset = max([item[1] for item in self.staticBBs[str(currentActionId)]])
                        print(touchInstrCnt)

                        exit(0)
                    break
            tmpidx += 1
        
        # for kk in lines[startPos -1:]:
        #     print(kk)
        # print(sensitiveFuncList)
        
        # exit(0)
        if not hasCheck:
            # touchInstrCnt = 0
            # for line in lines[startPos:endPos+1]:
            #     if line[1] not in self.customTable and line[2][1] != 0xffffffff and line[2][0] == currentActionId:
            #         # print(line)
            #         touchInstrCnt += 1
        
            # for kk in lines[startPos -1:startPos+ 130]:
            #     print(kk)
        
            # print(sensitiveFuncList)
            # exit(0)
            logger.info(f"Found Fake Notification::action@{currentActionId} no check to != _self {sensitiveFuncList}")
            return 1

        # try to generate side effects
        if sensitiveFuncList and not hasCheck:
            logger.info(f'Found Fake Notification:: ' +\
                f'action@{currentActionId}: no check to != _self, but execute functions:{sensitiveFuncList}')
            return 1

        # don't find (to != self / !(to == self))
        funcEndOffset = max([item[1] for item in self.staticBBs[str(currentActionId)]])
        if funcEndOffset == 0:
            return -1
        # executedIntrs = list()
        # for line in lines[startPos:endPos+1]:
        #     # if line[0] >= self.opcodeSetLen:
        #     #     continue
        #     func, offset = line[2][:2]
        #     if func == currentActionId and offset <= funcEndOffset \
        #         and offset not in executedIntrs:
        #         executedIntrs.append(line[2][1])

        touchInstrCnt = 0
        for line in lines[startPos:endPos+1]:
            if line[1] not in self.customTable and line[2][1] != 0xffffffff and line[2][0] == currentActionId:
                # print(line)
                touchInstrCnt += 1
        
        if touchInstrCnt >= 256 or touchInstrCnt >= setting.forgedPerct * funcEndOffset:
            logger.info(f'Found Fake Notification:: ' +\
                f'action@{currentActionId}: execute too much instruction:{touchInstrCnt}:{touchInstrCnt / funcEndOffset}% code')
            return 1

        # keep going
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
        # locate apply()
        # while startPos < size:
        #     _ , _,  args, _ = lines[startPos]
        #     if args[0] == self.applyFuncId:
        #         break
        #     startPos += 1

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

    def hasFakeTransferBug(self, executedContractName):# never increase balance
        _, _, currentActionId, _ = self.caseInfo
        print("[-] in hasFakeTransferBug()::", self.caseInfo, self.transferEntry)
        if currentActionId != self.transferEntry:
            return False # keep trying
        else:
            print("[+] Executed EOSPONSER#", currentActionId)
            # for item in self.firstActLog[-10:]:
            # print(item)
            _tmp = self.name2uint64(executedContractName)
            argCode = [_tmp & 0xffffffff, _tmp >> 32]
            argEosio = [880977408, 1429268995] 
            argmisc = [1232182624, 1456830293]# everipediaiq
            '''
            https://bloks.io/account/everipediaiq
            '''
            #[880977408, 1429268995] #eosio.token
            
            idx = len(self.firstActLog)-1
            while idx >= 0:
                _ , instr , args, _  = self.firstActLog[idx]
                if instr in ['i64.ne', 'i64.eq'] and args[2:6] in (argCode+argEosio, argEosio+argCode, argCode+argmisc, argmisc+argCode):
                    print("+++++++++++++====GUADRD++++++++++++++++++++++=", instr, args)
                    return False
                idx -= 1
            
            logger.info(f'Fake EOS. After passing the checks in the apply(), action:{currentActionId} was excuted')
            return True


        '''
        # callIndirectCount = 0

        # for _, instr, args, _ in lines:
        #     #apply() -> transfer()
        #     if 'call_indirect' in instr:
        #         currentActionId = args[0]
        #         logger.info(f'Fake EOS. After passing the checks in the apply(), action:{currentActionId} was excuted')
        #         return True
        #         # print(instr)
        #     #     callIndirectCount += 1  
        #     # if callIndirectCount >= 1: #apply() -> transfer()
        #     #     return True
        # return False


        currentActionId = -1
        # only check the first action
        with open(setting.plogPath, 'r') as f:
            lines = json.load(f)[:self.logScope[0]]

        # locate apply()
        linePos = -1
        for idx, item in enumerate(lines):
            _, instr, args, _ = item
            func = args[0]
            if func == self.applyFuncId:
                linePos = idx
                break

        if linePos == len(lines)-1 or linePos == -1:
            return False
        
        # excuate a user's function(action)

        ignoreFuncList = list()
        for idx, item  in enumerate(lines[linePos+1:]):
            _, instr, args, _ = item
            func = args[0]
            if func in ignoreFuncList:
                continue
            # if instr == 'call':
            #     target = args[2]
            if func > self.applyFuncId:
                if instr == 'begin_function' and lines[linePos+1+idx+1][1] == 'return':
                    ignoreFuncList.append(func)
                    continue
                currentActionId = func
                logger.info(f'Fake EOS. After passing the checks in the apply(), action:{currentActionId} was excuted')
                # print(lines[linePos+1+idx:linePos+idx+5])
                # exit(0)
                return True
   
        return False
        '''

    def exploitDetector(self,basicblocks, kind, isExecuted, isVulBalance):
        # detect bug

        # with open(setting.plogPath, 'r') as f:
        #     lines = json.load(f)
        # lineOfTaposFunction = -1
        # for i, item in enumerate(lines):
        #     _, instr, args, _ = item
        #     if 6 == args[0]:
        #         print(item)
        #         if int(args[0]) == 6:
        #             print("found", item)
        # exit(0)
        # return False

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
                # results.add(true, successExit, "transfer", kind, ty.testArgument)
                # logger.log("Has forged notification bug")
                # logger.log("Check forged notification bug")
            
            # elif _magic == 0:
            #     # results.add(false, successExit, "transfer", kind)
            #     pass

        elif kind == 2 or kind == 3:
            if self.hasFakeTransferBug():
                self.acceptEOSToken = True
                # results.add(true, successExit, "transfer", kind, ty.testArgument)
                # logger.log("Has fake transfer bug")
                logger.info(f"Has fake transfer bug;Fake EOS kind={kind}")
                return True
            # pipe.exe = "cleos"
            # pipe.args = "get currency balance eosio.token " + contractName + " EOS"
            # pipe.execute()
            # if(pipe.output.size() == 1) :
            #     originBalance = eosio::chain::asset::from_string(pipe.output[0])
            
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

