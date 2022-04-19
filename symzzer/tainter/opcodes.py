
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