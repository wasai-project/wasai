import json
import collections
from z3 import *
import re
import numbers
import struct
import copy

import symzzer.tainter.utils as utils
from symzzer.tainter.emulator import intUnary, floatUnary, intBinary, floatBinary, convertion
from symzzer.tainter.memory import SymbolMemory
import symzzer.setting as setting


RUNTIMEVALUE = 'RuntimeValue'
GLOBALVALUE = 'GlobalValue'
LOCALVALUE = 'LocalValue'
COMPAREOP = 'compareableOp'

LOCALPRIX = 'L'
GLOBALPRIX = 'G'

'''
 customelize list()
'''


class AssetEOS:
    def __init__(self, val):
        self.value = val & ((1 << 64) - 1)
        self.symbol = (val >> 64) & ((1 << 64) - 1)
        self.precision = (self.symbol & 255) % 19 # precision should be <= 18

    def toString(self):
        fmt = '.' + str(self.precision) + 'f'
        s = format(self.value/(10**self.precision), fmt)
        s += ' '
        sym = self.symbol >> 8
        while sym != 0:
            s += chr(sym & 255)
            sym >>= 8
        return s

class NameEOS:
    def __init__(self, val):
        self.value = val

    def toString(self):
        val = self.value
        charmap = '.12345abcdefghijklmnopqrstuvwxyz'
        ret = ['.'] * 13
        for i in range(0, 13):
            c = charmap[val & (0x0f if i == 0 else 0x1f)]
            ret[12 - i] = c
            val >>= (4 if i == 0 else 5)
        for i in range(12, -1, -1):
            if ret[i] != '.':
                break
            ret.pop()
        if len(ret) == 0:
            return '.............'
        retName = ''.join(ret)
    
    @property
    def clesoArg(self):
        if self.value == 0:
            return 'test'
        else:
            return self.toString()


class listProto(list):
    def __init__(self, element=None):
        if element != None:
            self.items = [element]
        else:
            self.items = list()

    def size(self):
        return len(self.items)

    def __setitem__(self, idx, item):
        idx = nowSize if idx == -1 else idx
        if idx < nowSize:
            self.items[idx] = item
            # return self.items[idx]
        for _ in range(idx - nowSize):
            self.push(listProto())
        self.push(item)

    def __getitem__(self, idx):
        nowSize = self.size()
        idx = nowSize-1 if idx == -1 else idx
        if idx < nowSize:
            return self.items[idx]
        else:
            self.__setitem__(idx, listProto())
            return listProto()

    def isEmpty(self):
        return self.size() == 0

    def push(self, element):
        self.items.append(element)

    def peek(self):
        if self.size() == 0:
            self.push(listProto())

        return self.items[-1]

    def pop(self):
        if self.size():
            return self.items.pop()
        else:
            # raise RuntimeError("List is empty")
            return []
    
    def insert(self, idx, element):
        self.items.insert(idx, element)

    def __len__(self):
        return self.size()

    def __eq__(self, cmpObj):
        if isinstance(cmpObj, listProto):
            return cmpObj.items == self.items
        elif isinstance(cmpObj, list):
            return cmpObj == self.items
        else:
            return item == self.items

    def __str__(self):
        return str(self.size()) + ' ' + str(self.items)


'''
Function Call Stack
call_pre x # call/indirect_call
....
begin_function # get locals & create new stack for x
..........
...body...
..........
return         # leave the function
end_function   # clear the stack of x
post_function  # push retVals to mother's stack
'''

class Analysis(object):
    def __init__(self, inputTp, inputJson, libf, actFuncID):
        self.debug = False
        if self.debug:
            print("=========================")
            print("Starting taint analysis")

        # self.stackItemProto = collections.namedtuple('stackItemProto', ['blocks', 'locals'])
        self.stack = listProto(listProto())
        self.memory = dict()
        self.syMemory = SymbolMemory()
        self.locals = listProto()
        self.glovals = listProto()
        self.lastStack = listProto()

        self.pathConstratins = list()

        self.inputType = ['I32'] + inputTp
        self.libFunc = libf
        
        self.inputArgs = inputJson
        self.cleosArgs = []
        self.timeoutCnt = 0
        self.actFuncId = actFuncID

        self.queue = list()

        self._cache = set()
    
    def newSession(self):
        self.stack = listProto(listProto())
        self.memory = dict()
        self.syMemory = SymbolMemory()
        self.locals = listProto()
        self.glovals = listProto()
        self.lastStack = listProto()

        self.inputType = ['I32']
        
        self.inputArgs = []
        self.cleosArgs = []
        self.timeoutCnt = 0

    def constructOriArgs(self, args):
        # print( self.inputType)
        # exit()
        argLocals = listProto()
        argLocals.push(args[0])
        if self.debug:
            print(self.inputType, self.inputArgs, args)
        for idx, arg in enumerate(args):
            if idx == 0:
                continue
            argName = f"{LOCALPRIX}{idx}"
            tp = self.inputType[idx]

            # TODO 修改成递归算法，使得能够对struct的string建模
            if isinstance(arg, BitVecRef): # <I32/I64>: immediate number / pointer
                if isinstance(tp, list):
                    # struct with depth one. TODO for the data with deeper struct
                    isOneDepth = True
                    for t in tp:
                        if isinstance(t, list):
                            isOneDepth = False
                            break
                    if not isOneDepth:
                        continue # ignore the argument<struct>
                    
                    result = arg
                    compTp = tp
                    st = int(str(arg))
                    for i, subTp in enumerate(compTp):
                        if subTp == 'int8' or subTp == 'uint8':
                            self.syMemory.store(BitVecVal(st, 32), st, 'I', 1, 1, BitVec("struct_" + argName + "_" + str(i), 8))
                            st += 1
                        elif subTp == 'int16' or subTp == 'uint16':
                            st += (2 - st % 2) % 2
                            self.syMemory.store(BitVecVal(st, 32), st, 'I', 2, 2, BitVec("struct_" + argName + "_" + str(i), 16))
                            st += 2
                        elif subTp == 'int32' or subTp == 'uint32':
                            st += (4 - st % 4) % 4
                            self.syMemory.store(BitVecVal(st, 32), st, 'I', 4, 4, BitVec("struct_" + argName + "_" + str(i), 32))
                            st += 4
                        elif subTp == 'int64' or subTp == 'uint64':
                            st += (8 - st % 8) % 8
                            self.syMemory.store(BitVecVal(st, 32), st, 'I', 8, 8, BitVec("struct_" + argName + "_" + str(i), 64))
                            st += 8
                        elif subTp == 'float32':
                            st += (4 - st % 4) % 4
                            self.syMemory.store(BitVecVal(st, 32), st, 'F', 4, 4, FP("struct_" + argName + "_" + str(i), Float32()))
                            st += 4
                        elif subTp == 'float64':
                            st += (8 - st % 8) % 8
                            self.syMemory.store(BitVecVal(st, 32), st, 'F', 8, 8, FP("struct_" + argName + "_" + str(i), Float64()))
                            st += 8
                elif tp[:6] == 'vector':
                    result = arg
                    self.syMemory.store(arg, int(str(arg)), 'I', 4, 4, BitVec("pointer_" + argName, 32))
                elif tp == 'asset':
                    result = arg
                    val  = BitVec(f"MEM{argName}", 128)
                    val1 = simplify(Extract(63, 0, val)) # 64bit
                    val2 = simplify(Extract(127, 64, val))
                    self.syMemory.store(arg              , int(str(arg))    , 'I', 8, 8, val1)
                    self.syMemory.store(simplify(arg + 8), int(str(arg)) + 8, 'I', 8, 8, val2)
    
                elif tp == 'string':
                    baseAdr = arg

                    key = list(self.inputArgs.keys())[idx-1]
                    cleosVal = self.inputArgs[key]
                    slen = len(cleosVal)
                    if self.debug:
                        print(f'[-] string saved in {baseAdr}')
                    
                    # result = BitVec(f"MEM{argName}Len", 32)
                    result = arg # TODO
                    self.syMemory.store(baseAdr, int(str(baseAdr)), 'I', 1, 1, result)
                    for i in range(1, slen+1):
                        self.syMemory.store(baseAdr + i, int(str(simplify(baseAdr + i))), 'I', 1, 1, BitVec(f'MEM{argName}Byt{i-1}', 8))
                    
                    if self.debug:
                        symValue = z3.simplify(z3.Select(self.syMemory.z3Array, baseAdr+16))
                        # symValue = self.syMemory.load(
                        #     symAddr, effectiveAddr, 'I', 1, 'IU', 4, value)
                        print('string::',symValue)
                else:
                    # otherwise:  name
                    result = BitVec(argName, arg.size())
            
            elif isinstance(arg, FPNumRef):
                # F32/F64,
                s_bit, e_bit = arg.sbits(), arg.ebits()
                if e_bit == 8 and s_bit == 24:
                    result = FP(argName, Float32())
                elif e_bit == 11 and s_bit == 53:
                    result = FP(argName, Float64())
                else:
                    raise RuntimeError("ERROR type for input data", arg, type(arg), s_bit, e_bit)

            argLocals.push(result)
        if self.debug:
            print("[+] ORI_ARGS",argLocals)
        self.locals.push(argLocals)


    def handleLibfunc(self, location, targetFunc, args, indirectTableIdx):
        if self.libFunc[targetFunc] == 'eosio_assert':
            if self.debug:
                print("Handing library function :EOSIO_ASSERT@", self.locals.peek()[0],
                    type(self.locals.peek()[0])) 

            # 1st parameter    :bool
            cond = utils.get_concrete(args[0])
            symCondition = copy.deepcopy(self.locals.peek()[-2]) # the second top 
            # 2nd parameter    :pointer
            _ = copy.deepcopy(self.locals.peek()[-1]) # the first top 
            if self.debug:
                print(f"[-] condition for asseet: @@@concrete:{cond}----symbolic{symCondition}")
            self.solve(location, cond, -1, symCondition) 

        
        # config stack for libf TODO
        libStack = listProto()
        self.lastStack.push(libStack) 
        
    def solve(self, location, currentCondition, conditionalTarget, symCondition):
        if location.func != self.actFuncId:
            return
        # print('begin-solve()')
        if self.debug:
            print("---debug--", location, symCondition)
        # print("[+] ===== CONDITION", simplify(symCondition), location)
    
        _allFuncArgsCnt = len(re.findall(r"(L\d+)|(MEM)", str(symCondition)))
        _LgsCnt = len(set(re.findall(r"(L\d+)", str(symCondition))))
        # print('-----------', _allFuncArgsCnt)
        
        '''
        if _allFuncArgsCnt == 0 or _allFuncArgsCnt > 100 or _LgsCnt >= 4:
            # print('=======================',symCondition)
            # no args or constraints too complex
            return
        '''


        if symCondition.decl().name() == str(symCondition): # symCondition is not a bool expression
            return

        # set constraint. only one
        flag = None
        if conditionalTarget == -1:
            # assert
            flag = -1
            e = simplify(symCondition == BitVecVal(1, 32)) # must satisify
        else:
            if currentCondition == 0:
                flag = 1
                e = simplify(symCondition == BitVecVal(1, 32)) # jump 
            else:
                flag = 0
                e = simplify(symCondition == BitVecVal(0, 32)) #  don't jump 

        fbTuple = utils.Location_FB(location.func, location.shift, flag)

        rese = e
        for c in self.pathConstratins:
            ct, et = z3util.get_vars(c), z3util.get_vars(e)
            if len(ct) == len(et) == 1 and str(ct) == str(et):
                rese = And(rese, c)
        self.queue.append((fbTuple, rese))
        


        self.pathConstratins.append(simplify(symCondition == BitVecVal(0 if currentCondition == 0 else 1, 32)))
        return 

        s = Solver()
        s.set("timeout", setting.solverTimeout)  # mills second
        s.add(e)

        if self.debug or True:
            print(f"IF ### {s} ### ===== JUMP ===> {conditionalTarget}")
            print(location)

        if s.check() != sat:
            print('check---', s.check())
            self._cache.add(str(e))
            # print('end-check-timeout', s.check())
            self.timeoutCnt += 1
            if self.debug:
                print(s)
                print("[-] symzzer: UNSAT here")
            return
        print('check---', s.check())
        mod = s.model()
        # print(setting.solverTimeout)
        if self.debug or True:
            print("----------MOD----------", mod)

    def seedMining(self, fbTuple, mod):
        for val in mod: 
            symSolved = mod[val]
            # find argPos. The first argument is 'self'
            name = val.name()
            # print(name)
            # exit()
            if name.startswith('MEM'):
                # pointer@asset, struct
                localPos = utils.localPos(name[3:])
            elif name.startswith('L'):
                localPos = utils.localPos(name)
            elif name.startswith('G'):
                # global ;pass
                continue
            elif name.startswith('struct_'):
                localPos = utils.localPos(name[7:])
                structEIdx = utils.structEPos(name)

            elif name == 'memory':
                continue
            elif name == 'fp.to_ieee_bv':
                continue
            else:
                raise RuntimeError("[-] Defind your type.@", name)

            if localPos == 0:
                # cannot modify 'self'
                continue
            
            tp = self.inputType[localPos]
            _key = list(self.inputArgs.keys())[localPos-1]
            originalStructData = self.inputArgs[_key]
            

            f = lambda data, k : data[list(data.keys())[k]] # find the k th element of <dict>data

            if tp.endswith('[]'): 
                # array TODO
                pass
            elif isinstance(tp, list):
                # struct
                originalData = f(originalStructData, structEIdx)
                newVal = self.arg2abiType(val, symSolved, tp[structEIdx], originalData)
                if newVal is None:
                    continue
                self.cleosArgs.append((fbTuple, (localPos-1, structEIdx), newVal))

            else:
                # basic data
                newVal = self.arg2abiType(val, symSolved, tp, originalStructData)
                if newVal is None:
                    continue
                self.cleosArgs.append((fbTuple, (localPos-1, -1), newVal))    
                                

    def arg2abiType(self, symbol, symExpr, tp, oriData):
        if self.debug or True:
            print('----debug----arg2abiType---tp=', tp, 'symExpr=', symExpr)

        if  tp == 'asset':
            assetval = AssetEOS(symExpr.as_long())
            aVal, aSym = assetval.toString().split(' ', 1)

            oriVal, oriSym = oriData.split(' ', 1)
            oriprecision = len(oriVal.split('.', 1)[1]) % 19 if '.' in oriVal else 0 # precision should be <= 18

            # asset 检查仅限symbol or value
           
            if assetval.symbol == 0:
                # 1. require value
                newVal = format(assetval.value/(10**oriprecision), f'.{oriprecision}f')  + ' ' + oriSym
            else:
                # 2. require symbol
                newVal = format((float(oriVal)*oriprecision)/(10**assetval.precision), f'.{assetval.precision}f')  + ' ' + aSym
           
        elif tp == 'name':

            nameval = NameEOS(symExpr.as_long() ) 
            newVal = nameval.clesoArg
    

        elif tp.startswith('float'):
            if symExpr.isNaN():
                # cannot solve
                return None
            sizeTp = int(tp[5:])
           
            if '-oo' == str(symExpr):
                newVal = -100000000000000000
            elif '+oo' == str(symExpr) or 'oo' == str(symExpr):
                newVal =  100000000000000000
            else:
                newVal = simplify(fpToIEEEBV(symExpr)).as_long()
                if sizeTp == 32:
                    newVal = struct.pack('<I', newVal) # unsigned here, check IEEE standard
                    newVal = struct.unpack('<f', newVal)[0]
                    # exit()
                else:
                    newVal = struct.pack('<Q', newVal)  # the same
                    newVal = struct.unpack('<d', newVal)[0]

        elif tp == 'string':
            stringArg = oriData
            byt = symExpr
            r = re.search(r"Byt(\d+)", str(symbol))
            if r:
                # update byte
                stringIndex = int(r.group(1))
                newVal = stringArg[:stringIndex] + chr(byt.as_long()) + stringArg[stringIndex+1:]
                if self.debug:
                    print(f'stringVal;{stringArg};<--{newVal}')
            else:
                # update len
                slen = byt.as_long() % 255
                newVal = 'A'*slen
                if self.debug:
                    print('len;;;', slen)

        else:
            # Int[32|64|128]
            newVal = symExpr.as_long()
        return newVal

    def start(self, location):
        pass

    def nop(self, location):
        pass

    def unreachable(self, location):
        print("Unreachable!!!")
        return

    def if_(self, location,  condition):
        self.solve(location, condition, -2, self.stack.peek().pop())

    def br(self, location,  target):
        # self.stack.peek().pop()
        pass

    def br_if(self, location,  conditionalTarget, condition):
        # print("[+]br_if-->", self.stack.peek(), self.locals.peek())
        self.solve(location, condition, conditionalTarget, self.stack.peek().pop())

    def br_table(self, location,  table, defaultTarget, tableIdx):
        # TODO
        self.stack.peek().pop()

    def drop(self, location,  value):
        self.stack.peek().pop()

    def select(self, location,  cond, first, second):
        condition = self.stack.peek().pop() #c
        arg1 = self.stack.peek().pop()      #a
        arg2 = self.stack.peek().pop()      #b
        if is_bool(condition):
            self.stack.peek().push(If(condition, arg2, arg1))
        else:
            self.stack.peek().push(If(simplify(condition != 0), arg2, arg1))


    def begin(self, location,  type):
        if type == 'function':
            # new scope for callee
            self.stack.push(listProto())
            # self.locals.push(listProto())


    def end(self, location, type, beginLocation):
        if type == 'function':
            self.lastStack.push(self.stack.pop())
  
    def call_pre(self, location, targetFunc, args, indirectTableIdx):
        isnIndirect = True
        if indirectTableIdx != []:
            isnIndirect = False
        
        if (not isnIndirect) and len(self.locals) == 0: #original args
            # print('---debug--- oriargs',args)
            self.constructOriArgs(args)
            return

        # init scope for callee
        argLocals = listProto()
        for _ in args:
            argLocals.insert(0, self.stack.peek().pop())
        self.locals.push(argLocals)
    
        # handling library function
        targetFunc = int(str(targetFunc))
        if isnIndirect and targetFunc < len(self.libFunc):
            if self.debug:
                print("CALL Library Function:", self.libFunc[targetFunc])
            
            # locals and stack for libf
            self.handleLibfunc(location, targetFunc, args, indirectTableIdx)


    def call_post(self, location,  vals):
        lastStack = self.lastStack.pop()

        # Wasm 隐式传参. 返回值在callee's stack
        trueRtCnt = len(vals)
        if len(lastStack) == trueRtCnt:
            # return symbolic value if model callee successfully
            for _ in range(trueRtCnt):
                val = lastStack.pop()
                self.stack.peek().push(val) 
        else:
            # return runtime value if fail to model callee 
            for val in vals:
                self.stack.peek().push(val) 

        self.locals.pop() # drop the scope of the callee

    def return_(self, location,  values):
        pass

    def const_(self, location,  op, value):
        if self.debug:
            print("New taint at ", location)
        self.stack.peek().push(value)

    def unary(self, location,  op, input, aresult):
        instrType, instrName = op.split('.')
        arg0 = self.stack.peek().pop()


        try:
            # convertion
            if any([item in instrName for item in ['wrap', 'trunc', 'extend', 'convert', 'demote', 'promote', 'reinterpret']]):
                result = convertion(instrName, arg0)
            # Int32, Int64
            elif instrType in ['i32', 'i64']:
                result = intUnary(instrName, arg0)
            # Float32, Float64
            elif instrType in ['f32', 'f64']:
                result = floatUnary(instrName, arg0)
            else:
                raise Exception(
                    f"does't match any kind of unary instrument@{instrName}")
        except Exception as e:
            print('[-] Handing analysis.unary@',instrName, e, "continue")
            result = aresult

        self.stack.peek().push(result)

    def binary(self, location,  op, afirst, asecond, aresult):
        instrType, instrName = op.split('.')
        arg1, arg2 = self.stack.peek().pop(), self.stack.peek().pop()
        # print("BINARY",type(arg1),type(arg2),arg1,arg2)


        try:
            # Int32, Int64
            if instrType in ['i32', 'i64']:
                result = intBinary(instrName, arg1, arg2)
            # Float32, Float64
            elif instrType in ['f32', 'f64']:
                result = floatBinary(instrName, arg1, arg2)
        except Exception as e:
            print("EXCP", e)
            result = aresult

        self.stack.peek().push(result)


    def load(self, location,  op, memarg, value):
        offset = memarg.offset.as_long() # to int
        baseAddr = memarg.addr.as_long() # to_int

        sbaseAdr = self.stack.peek().pop()
        if self.debug:
            print(sbaseAdr , offset)
        symAddr = simplify(sbaseAdr + offset)
        effectiveAddr = baseAddr + offset
        symValue = ""
        # symValue = self.memory[effectiveAddr]
        if op == "i32.load":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 4, 'I', 4, value)
        elif op == "i64.load":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 8, 'I', 8, value)
        elif op == "f32.load":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'F', 4, 'F', 4, value)
        elif op == "f64.load":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'F', 8, 'F', 8, value)
        elif op == "i32.load8_s":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 1, 'IS', 4, value)
        elif op == "i32.load8_u":
            if self.debug:
                print("[+] i32.load8_u:effectadr=", effectiveAddr, type(effectiveAddr), symAddr)

            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 1, 'IU', 4, value)

        elif op == "i32.load16_s":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 2, 'IS', 4, value)
        elif op == "i32.load16_u":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 2, 'IU', 4, value)
        elif op == "i64.load8_s":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 1, 'IS', 8, value)
        elif op == "i64.load8_u":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 1, 'IU', 8, value)
        elif op == "i64.load16_s":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 2, 'IS', 8, value)
        elif op == "i64.load16_u":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 2, 'IU', 8, value)
        elif op == "i64.load32_s":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 4, 'IS', 8, value)
        elif op == "i64.load32_u":
            symValue = self.syMemory.load(
                symAddr, effectiveAddr, 'I', 4, 'IU', 8, value)
        if (self.debug):
            print("Memory load from address " +
                  effectiveAddr + " with taint " + taint)
        self.stack.peek().push(symValue)

    def store(self, location, op, memarg, value):
        symValue = self.stack.peek().pop()
        symAddr = simplify(self.stack.peek().pop() + memarg.offset.as_long())
        if self.debug:
            print("Handling STORE ", symValue, type(symValue), symAddr, type(symAddr))
        effectiveAddr = int(str(memarg.addr)) + int(str(memarg.offset))
        #self.memory[effectiveAddr] = value
        if op == "i32.store":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 4, 4, symValue)
        if op == "i64.store":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 8, 8, symValue)
        if op == "f32.store":
            self.syMemory.store(symAddr, effectiveAddr, 'F', 4, 4, symValue)
        if op == "f64.store":
            self.syMemory.store(symAddr, effectiveAddr, 'F', 8, 8, symValue)
        if op == "i32.store8":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 4, 1, symValue)
        if op == "i32.store16":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 4, 2, symValue)
        if op == "i64.store8":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 8, 1, symValue)
        if op == "i64.store16":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 8, 2, symValue)
        if op == "i64.store32":
            self.syMemory.store(symAddr, effectiveAddr, 'I', 8, 4, symValue)
        if self.debug:
            print("Memory store to address " +
                  effectiveAddr + " with value@ " + symValue)

    def memory_size(self, location,  currentSizePages):
        self.stack.peek().push(currentSizePages)

    def memory_grow(self, location,  byPages, previousSizePages):
        symByPages = self.stack.peek().pop()
        self.stack.peek().push(previousSizePages)

    def local(self, location,  op, localIndex, value):
        # symval = self.stack.peek().pop() CHANGED BY SZH
        if op == "local.set":
            symval = self.stack.peek().pop()
            if localIndex < len(self.inputType): 
                # on-demand implement
                if self.debug:
                    print(localIndex, len(self.inputType), self.inputType, self.inputArgs )
                tp = self.inputType[localIndex]
                if tp == 'string':
                    # init new string
                    baseAdr = utils.get_concrete(value)
                    key = list(self.inputArgs.keys())[localIndex-1]
                    cleosVal = self.inputArgs[key]
                    slen = len(cleosVal)
                    if self.debug:
                        print(f'[-] string saved in {baseAdr}', value)
                    if baseAdr >= 2000: # mem address
                        for i in range(0, slen):
                            self.syMemory.store(simplify(value + i), baseAdr + i, 'I', 1, 1, BitVec(f'MEML{localIndex}Byt{i}', 8))
                    elif baseAdr == len(cleosVal):
                        symval = BitVec(f'MEML{localIndex}Len', 32)

            self.locals[-1][localIndex] = symval

            if self.debug:
                print("Setting local variable with ", symval, " at ", location)

        elif op == "local.tee":
            # print('---local-tee, ', localIndex, '--', self.locals.peek())
            symval = self.stack.peek().peek()
            self.locals[-1][localIndex] = symval

        elif op == "local.get":
            symval = self.locals.peek()[localIndex]
            # print("[+} local---get ", localIndex, '---', symval, self.locals.peek())
            result = value if isinstance(symval, list) else symval
            self.stack.peek().push(result)
            if self.debug:
                print("Getting local variable with ", result, " at ", location)

        else:
            raise Exception('Instruction:', op,
                            'not match in local function')

    def globalh(self, location,  op, globalIndex, value):
        if op == "global.set":
            self.glovals[globalIndex] = self.stack.peek().pop()
            # print('-global set--', globalIndex, '--', self.locals.peek())

        elif op == "global.get":
            symval = self.glovals[globalIndex]
            # print(type(symval), symval)
            result = value if isinstance(symval, list) and symval == [] else symval
            self.stack.peek().push(result)
        else:
            raise Exception('Instruction:', op,
                            'not match in globalh function')