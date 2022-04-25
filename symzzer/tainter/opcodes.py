
START = "start"
NOP = "nop"
UNREACHABLE = "unreachable"
IF_ = "if_"
BR = "br"
BR_IF = "br_if"
BR_TABLE = "br_table"
BEGIN = "begin"
END = "end"
DROP = "drop"
SELECT = "select"
CALL_PRE = "call_pre"
CALL_POST = "call_post"
RETURN_ = "return_"
CONST_ = "const_"
UNARY = "unary"
BINARY = "binary"
LOAD = "load"
STORE = "store"
MEMORY_SIZE = "memory_size"
MEMORY_GROW = "memory_grow"
LOCAL = "local"
GLOBAL = "global"




opcodeToType = {
       # control
       "unreachable":UNREACHABLE,
       "nop":NOP,
    #    "block":BEGIN,
    #    "loop":BEGIN, 
       "br":BR,  # 1
       "br_if":BR_IF,  # 1
       "br_table":BR_TABLE,
       "return":RETURN_,  # 1
       "call":CALL_PRE,  # 1
       "call_indirect":CALL_PRE,
       
       'if': IF_,
       'else': IF_,
       'then': IF_,

       "drop":DROP,  # 1
       "select":SELECT,  # 1

       #local & global
       "local.get":LOCAL,  # 1
       "local.set":LOCAL,  # 1
       "local.tee":LOCAL,  # 1
       "global.get":GLOBAL,  # 1
       "global.set":GLOBAL,  # 1

       # memory
       "i32.load":LOAD,  # 1
       "i64.load":LOAD,
       "f32.load":LOAD,
       "f64.load":LOAD,
       "i32.load8_s":LOAD,
       "i32.load8_u":LOAD,  # 1
       "i32.load16_s":LOAD,
       "i32.load16_u":LOAD,
       "i64.load8_s":LOAD,
       "i64.load8_u":LOAD,
       "i64.load16_s":LOAD,
       "i64.load16_u":LOAD,
       "i64.load32_s":LOAD,
       "i64.load32_u":LOAD,
       "i32.store":STORE,  # 1
       "i64.store":STORE,  # 1
       "f32.store":STORE,
       "f64.store":STORE,
       "i32.store8":STORE,  # 1
       "i32.store16":STORE,  # 1
       "i64.store8":STORE,
       "i64.store16":STORE,
       "i64.store32":STORE,
       "memory.size":MEMORY_SIZE,  # 1
       "memory.grow":MEMORY_GROW,  

       # constant
       "i32.const":CONST_,  # 1
       "i64.const":CONST_,  # 1
       "f32.const":CONST_,
       "f64.const":CONST_,

       "i32.eqz":UNARY ,
       "i32.eq":BINARY ,
       "i32.ne":BINARY ,
       "i32.lt_s":BINARY ,
       "i32.lt_u":BINARY ,
       "i32.gt_s":BINARY ,
       "i32.gt_u":BINARY ,
       "i32.le_s":BINARY ,
       "i32.le_u":BINARY ,
       "i32.ge_s":BINARY ,
       "i32.ge_u":BINARY ,
       "i64.eqz":UNARY ,
       "i64.eq":BINARY ,
       "i64.ne":BINARY ,
       "i64.lt_s":BINARY ,
       "i64.lt_u":BINARY ,
       "i64.gt_s":BINARY ,
       "i64.gt_u":BINARY ,
       "i64.le_s":BINARY ,
       "i64.le_u":BINARY ,
       "i64.ge_s":BINARY ,
       "i64.ge_u":BINARY ,
       "f32.eq":BINARY ,
       "f32.ne":BINARY ,
       "f32.lt":BINARY ,
       "f32.gt":BINARY ,
       "f32.le":BINARY ,
       "f32.ge":BINARY ,
       "f64.eq":BINARY ,
       "f64.ne":BINARY ,
       "f64.lt":BINARY ,
       "f64.gt":BINARY ,
       "f64.le":BINARY ,
       "f64.ge":BINARY ,
       "i32.clz":UNARY ,
       "i32.ctz":UNARY ,
       "i32.popcnt":UNARY ,
       "i32.add":BINARY ,
       "i32.sub":BINARY ,
       "i32.mul":BINARY ,
       "i32.div_s":BINARY ,
       "i32.div_u":BINARY ,
       "i32.rem_s":BINARY ,
       "i32.rem_u":BINARY ,
       "i32.and":BINARY ,
       "i32.or":BINARY ,
       "i32.xor":BINARY ,
       "i32.shl":BINARY ,
       "i32.shr_s":BINARY ,
       "i32.shr_u":BINARY ,
       "i32.rotl":BINARY ,
       "i32.rotr":BINARY ,
       "i64.clz":UNARY ,
       "i64.ctz":UNARY ,
       "i64.popcnt":UNARY ,
       "i64.add":BINARY ,
       "i64.sub":BINARY ,
       "i64.mul":BINARY ,
       "i64.div_s":BINARY ,
       "i64.div_u":BINARY ,
       "i64.rem_s":BINARY ,
       "i64.rem_u":BINARY ,
       "i64.and":BINARY ,
       "i64.or":BINARY ,
       "i64.xor":BINARY ,
       "i64.shl":BINARY ,
       "i64.shr_s":BINARY ,
       "i64.shr_u":BINARY ,
       "i64.rotl":BINARY ,
       "i64.rotr":BINARY ,
       "f32.abs":UNARY ,
       "f32.neg":UNARY ,
       "f32.ceil":BINARY ,
       "f32.floor":BINARY ,
       "f32.trunc":BINARY ,
       "f32.nearest":BINARY ,
       "f32.sqrt":BINARY ,
       "f32.add":BINARY ,
       "f32.sub":BINARY ,
       "f32.mul":BINARY ,
       "f32.div":BINARY ,
       "f32.min":BINARY ,
       "f32.max":BINARY ,
       "f32.copysign":BINARY ,
       "f64.abs":UNARY ,
       "f64.neg":UNARY ,
       "f64.ceil":BINARY ,
       "f64.floor":BINARY ,
       "f64.trunc":BINARY ,
       "f64.nearest":BINARY ,
       "f64.sqrt":BINARY ,
       "f64.add":BINARY ,
       "f64.sub":BINARY ,
       "f64.mul":BINARY ,
       "f64.div":BINARY ,
       "f64.min":BINARY ,
       "f64.max":BINARY ,
       "f64.copysign":BINARY ,
       "i32.wrap_i64":UNARY ,
       "i32.trunc_s_f32":UNARY ,
       "i32.trunc_u_f32":UNARY ,
       "i32.trunc_s_f64":UNARY ,
       "i32.trunc_u_f64":UNARY ,
       "i64.extend_i32_s":UNARY,
       "i64.extend_i32_u":UNARY,
       "i64.extend_s_i32":UNARY ,
       "i64.extend_u_i32":UNARY ,
       "i64.trunc_s_f32":UNARY ,
       "i64.trunc_u_f32":UNARY ,
       "i64.trunc_s_f64":UNARY ,
       "i64.trunc_u_f64":UNARY ,
       "f32.convert_s_i32":UNARY ,
       "f32.convert_u_i32":UNARY ,
       "f32.convert_s_i64":UNARY ,
       "f32.convert_u_i64":UNARY ,
       "f32.demote_f64":UNARY ,
       "f64.convert_s_i32":UNARY ,
       "f64.convert_u_i32":UNARY ,
       "f64.convert_s_i64":UNARY ,
       "f64.convert_u_i64":UNARY ,
       "f64.promote_f32":UNARY ,
       "i32.reinterpret_f32":UNARY ,
       "i64.reinterpret_f64":UNARY ,
       "f32.reinterpret_i32":UNARY ,
       "f64.reinterpret_i64":UNARY,

       "start":START,
       "call_post":CALL_POST,  # 1
       "begin_function":BEGIN,  # 1
       "begin_block":BEGIN,  # 1
       "begin_loop":BEGIN,  # 1
       "begin_if":BEGIN,  # 1
       "begin_else":BEGIN,  # 1
       "end_function":END,  # 1,
       "end_block":END,  # 1
       "end_loop":END,  # 1
       "end_if":END,  # 1
       "end_else":END  # 1
}


'''
        def i32sub_Hook(args):
            func, instr, input0, input1, result0 = args
            self.analysis.binary(Location_t(func, instr), "i32.sub", input0, input1, result0) 
        
        def beginfunction_Hook(args):
            func, instr = args
            self.analysis.begin(Location_t(func, instr), "function")

        def endfunction_Hook(args):
            func, instr = args
            self.analysis.end(Location_t(func, instr), "function", Location_t(func, -1)) 

        def return_Hook(args):
            func, instr = args
            self.analysis.return_(Location_t(func, instr), [])

        def i32const_Hook (args):
            func, instr, value = args
            self.analysis.const_(Location_t(func, instr), "i32.const", value) 

        def localtee_Hook(args):
            # print(args)
            func, instr, index, value = args[:4]
            self.analysis.local(Location_t(func, instr), "local.tee", index, value) 

        def beginblock_Hook(args ):
            func, instr = args
            self.analysis.begin(Location_t(func, instr), "block") 

        def globalset_Hook(args ):
            func, instr, index, value = args
            self.analysis.globalh(Location_t(func, instr), "global.set", index, value) 
        def i32ne_Hook(args):
            func, instr, input0, input1, result0 = args
            self.analysis.binary(Location_t(func, instr), "i32.ne", input0, input1, result0)

        def globalget_Hook(_args):
            func, instr, index, value = _args
            self.analysis.globalh(Location_t(func, instr), "global.get", index, value)
        def callindirect_Hook (_args):
            func, instr, tableIndex = _args[:3]
            args = _args[3:]
            # print('callindirect:',args)
            #targetfunc= Wasabi.resolveTableIdx(tableIndex)
            self.analysis.call_pre(Location_t(func, instr), [], args, tableIndex)

        def localget_Hook(_args):
            func, instr, index, value = _args
            self.analysis.local(Location_t(func, instr), "local.get", index, value)
        def  brif_Hook(_args):
            func, instr, condition, targetLabel, targetInstr = _args
            self.analysis.br_if(Location_t(func, instr), [], condition == 1)
        
        def endblock_Hook(_args):
            func, instr, beginInstr = _args
            self.analysis.end(Location_t(func, instr), "block", [])

        def i32add_Hook (_args):
            func, instr, input0, input1, result0 = _args
            self.analysis.binary(Location_t(func, instr), "i32.add", input0, input1, result0)
            

self.AlowlevelHooks = {
       "br_if":brif_Hook,
       "begin_block":  beginblock_Hook,
       "end_block":endblock_Hook,
       "call_indirect": callindirect_Hook,
       "begin_function": beginfunction_Hook,
       "end_function": endfunction_Hook,
       "return":  return_Hook,

       "local.get": localget_Hook,
       "local.tee":  localtee_Hook,
       "global.set":  globalset_Hook,
       "global.get": globalget_Hook,

       "i32.const":  i32const_Hook,
       "i32.sub":  i32sub_Hook,
       "i32.ne":  i32ne_Hook,
       "i32.add": i32add_Hook,
}
'''

'''
wasm = Wasm()
instr = 'i32.add'
wasm._group[wasm.reverse_table[instr]]
def group():
""" Instruction classification per group """
last_class = _groups.get(0)
for k, v in _groups.items():
       if self.opcode >= k:
       last_class = v
       else:
       return last_class
return last_class

if group(opcode) == 'Arithmetic_i32':
if xx[2] == 2：
       binary
elif xx[2] == 1:
       unary
else:
       raise Exception("fail select hokker")

for key, item in opcodes._table.items():
if 0x45 <= key  <0xa7:
       if item[2] == 2:



_groups = {
0x00: UNREACHABLE,
0x01: NOP,
0x02: ('block', BlockImm(), 0, 0, 'begin a sequence of expressions'),
0x03: ('loop', BlockImm(), 0, 0, 'begin a block which can also form control flow loops'),
0x04: ('if', BlockImm(), 1, 0, 'begin if expression'),
0x05: ('else', None, 0, 0, 'begin else expression of if'),
0x0b: ('end', None, 0, 0, 'end a block, loop, or if'),
0x0c: ('br', BranchImm(), 0, 0, 'break that targets an outer nested block'),
0x0d: ('br_if', BranchImm(), 1, 0, 'conditional break that targets an outer nested block'),
0x0e: ('br_table', BranchTableImm(), 1, 0, 'branch table control flow construct'),
0x0f: ('return', None, 1, 0, 'return zero or one value from this function'),
0x10: ('call', CallImm(), 0, 0, 'call a function by its index'),
0x11: ('call_indirect', CallIndirectImm(), 1, 0, 'call a function indirect with an expected signature'),

0x1A: 'Parametric',
0x20: 'Variable',
0x28: 'Memory',
0x41: 'Constant',
0x45: 'Logical_i32',
0x50: 'Logical_i64',
0x5b: 'Logical_f32',
0x61: 'Logical_f64',
0x67: 'Arithmetic_i32',
0x71: 'Bitwise_i32',
0x79: 'Arithmetic_i64',
0x83: 'Bitwise_i64',
0x8b: 'Arithmetic_f32',
0x99: 'Arithmetic_f64',
0xa7: 'Conversion'
}

'''

