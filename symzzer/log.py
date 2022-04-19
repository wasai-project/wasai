import os

nameTable = [
    "",
    "unreachable",
    "nop",
    "block",
    "loop",
    "if",
    "else",
    "end",
    "br",
    "br_if",
    "br_table",
    "return",
    "call",
    "call_indirect",
    "drop",
    "select",
    "local.get",
    "local.set",
    "local.tee",
    "global.get",
    "global.set",
    "memory.size",
    "memory.grow",
    "i32.const",
    "i64.const",
    "f32.const",
    "f64.const",
    "i32.load",
    "i64.load",
    "f32.load",
    "f64.load",
    "i32.load8_s",
    "i32.load8_u",
    "i32.load16_s",
    "i32.load16_u",
    "i64.load8_s",
    "i64.load8_u",
    "i64.load16_s",
    "i64.load16_u",
    "i64.load32_s",
    "i64.load32_u",
    "i32.store",
    "i64.store",
    "f32.store",
    "f64.store",
    "i32.store8",
    "i32.store16",
    "i64.store8",
    "i64.store16",
    "i64.store32",
    "i32.eqz",
    "i64.eqz",
    "i32.clz",
    "i32.ctz",
    "i32.popcnt",
    "i64.clz",
    "i64.ctz",
    "i64.popcnt",
    "f32.abs",
    "f32.neg",
    "f32.ceil",
    "f32.floor",
    "f32.trunc",
    "f32.nearest",
    "f32.sqrt",
    "f64.abs",
    "f64.neg",
    "f64.ceil",
    "f64.floor",
    "f64.trunc",
    "f64.nearest",
    "f64.sqrt",
    "i32.wrap_i64",
    "i32.trunc_f32_s",
    "i32.trunc_f32_u",
    "i32.trunc_f64_s",
    "i32.trunc_f64_u",
    "i64.extend_i32_s",
    "i64.extend_i32_u",
    "i64.trunc_f32_s",
    "i64.trunc_f32_u",
    "i64.trunc_f64_s",
    "i64.trunc_f64_u",
    "f32.convert_i32_s",
    "f32.convert_i32_u",
    "f32.convert_i64_s",
    "f32.convert_i64_u",
    "f32.demote_f64",
    "f64.convert_i32_s",
    "f64.convert_i32_u",
    "f64.convert_i64_s",
    "f64.convert_i64_u",
    "f64.promote_f32",
    "i32.reinterpret_f32",
    "i64.reinterpret_f64",
    "f32.reinterpret_i32",
    "f64.reinterpret_i64",
    "i32.eq",
    "i32.ne",
    "i32.lt_s",
    "i32.lt_u",
    "i32.gt_s",
    "i32.gt_u",
    "i32.le_s",
    "i32.le_u",
    "i32.ge_s",
    "i32.ge_u",
    "i64.eq",
    "i64.ne",
    "i64.lt_s",
    "i64.lt_u",
    "i64.gt_s",
    "i64.gt_u",
    "i64.le_s",
    "i64.le_u",
    "i64.ge_s",
    "i64.ge_u",
    "f32.eq",
    "f32.ne",
    "f32.lt",
    "f32.gt",
    "f32.le",
    "f32.ge",
    "f64.eq",
    "f64.ne",
    "f64.lt",
    "f64.gt",
    "f64.le",
    "f64.ge",
    "i32.add",
    "i32.sub",
    "i32.mul",
    "i32.div_s",
    "i32.div_u",
    "i32.rem_s",
    "i32.rem_u",
    "i32.and",
    "i32.or",
    "i32.xor",
    "i32.shl",
    "i32.shr_s",
    "i32.shr_u",
    "i32.rotl",
    "i32.rotr",
    "i64.add",
    "i64.sub",
    "i64.mul",
    "i64.div_s",
    "i64.div_u",
    "i64.rem_s",
    "i64.rem_u",
    "i64.and",
    "i64.or",
    "i64.xor",
    "i64.shl",
    "i64.shr_s",
    "i64.shr_u",
    "i64.rotl",
    "i64.rotr",
    "f32.add",
    "f32.sub",
    "f32.mul",
    "f32.div",
    "f32.min",
    "f32.max",
    "f32.copysign",
    "f64.add",
    "f64.sub",
    "f64.mul",
    "f64.div",
    "f64.min",
    "f64.max",
    "f64.copysign",
    "start",
    "call_post",
    "begin_function",
    "begin_block",
    "begin_loop",
    "begin_if",
    "begin_else",
    "end_function",
    "end_block",
    "end_loop",
    "end_if",
    "end_else"
]

def gettype(id):
    low8 = id & 255
    return nameTable[low8]


def getFixedTp(instr):
    if instr == "if":
        return ["I32"]
    elif instr == "br_if":
        return ["I32", "I32", "I32"]
    elif instr == "br_table":
        return ["I32", "I32"]
    # elif instr == "call_indirect":
    #     return ["I32"]
    elif instr == "memory.size":
        return ["I32"]
    elif instr == "memory.grow":
        return ["I32", "I32"]
    elif instr == "i32.const":
        return ["I32"]
    elif instr == "i64.const":
        return ["I64"]
    elif instr == "f32.const":
        return ["F32"]
    elif instr == "f64.const":
        return ["F64"]
    elif instr == "i32.load" or instr == "i32.load8_s" or instr == "i32.load8_u" or instr == "i32.load16_s" or instr == "i32.load16_u":
        return ["I32", "I32", "I32", "I32"]
    elif instr == "i64.load" or instr == "i64.load8_s" or instr == "i64.load8_u" or instr == "i64.load16_s" or instr == "i64.load16_u" or instr == "i64.load32_s" or instr == "i64.load32_u":
        return ["I32", "I32", "I32", "I64"]
    elif instr == "f32.load":
        return ["I32", "I32", "I32", "F32"]
    elif instr == "f64.load":
        return ["I32", "I32", "I32", "F64"]
    elif instr == "i32.store" or instr == "i32.store8" or instr == "i32.store16":
        return ["I32", "I32", "I32", "I32"]
    elif instr == "i64.store" or instr == "i64.store8" or instr == "i64.store16" or instr == "i64.store32":
        return ["I32", "I32", "I32", "I64"]
    elif instr == "f32.store":
        return ["I32", "I32", "I32", "F32"]
    elif instr == "f64.store":
        return ["I32", "I32", "I32", "F64"]
    elif instr == "i32.eqz" or instr == "i32.clz" or instr == "i32.ctz" or instr == "i32.popcnt":
        return ["I32", "I32"]
    elif instr == "i64.eqz" or instr == "i64.clz" or instr == "i64.ctz" or instr == "i64.popcnt":
        return ["I64", "I32"]
    elif instr == "f32.abs" or instr == "f32.neg" or instr == "f32.ceil" or instr == "f32.floor" or instr == "f32.trunc" or instr == "f32.nearest" or instr == "f32.sqrt":
        return ["F32", "F32"]
    elif instr == "f64.abs" or instr == "f64.neg" or instr == "f64.ceil" or instr == "f64.floor" or instr == "f64.trunc" or instr == "f64.nearest" or instr == "f64.sqrt":
        return ["F64", "F64"]
    elif instr == "i32.wrap_i64":
        return ["I64", "I32"]
    elif instr == "i32.trunc_f32_s" or instr == "i32.trunc_f32_u":
        return ["F32", "I32"]
    elif instr == "i32.trunc_f64_s" or instr == "i32.trunc_f64_u":
        return ["F64", "I32"]
    elif instr == "i64.extend_i32_s" or instr == "i64.extend_i32_u":
        return ["I32", "I64"]
    elif instr == "i64.trunc_f32_s" or instr == "i64.trunc_f32_u":
        return ["F32", "I64"]
    elif instr == "i64.trunc_f64_s" or instr == "i64.trunc_f64_u":
        return ["F64", "I64"]
    elif instr == "f32.convert_i32_s" or instr == "f32.convert_i32_u":
        return ["I32", "F32"]
    elif instr == "f32.demote_f64":
        return ["F64", "F32"]
    elif instr == "f32.convert_i64_s" or instr == "f32.convert_i64_u":
        return ["I64", "F32"]
    elif instr == "f64.convert_i32_s" or instr == "f64.convert_i32_u":
        return ["I32", "F64"]
    elif instr == "f64.convert_i64_s" or instr == "f64.convert_i64_u":
        return ["I64", "F64"]
    elif instr == "f64.promote_f32":
        return ["F32", "F64"]
    elif instr == "i32.reinterpret_f32":
        return ["F32", "I32"]
    elif instr == "i64.reinterpret_f64":
        return ["F64", "I64"]
    elif instr == "f32.reinterpret_i32":
        return ["I32", "F32"]
    elif instr == "f64.reinterpret_i64":
        return ["I64", "F64"]
    elif instr == "i32.eq" or instr == "i32.ne" or instr == "i32.lt_s" or instr == "i32.lt_u" or instr == "i32.gt_s" or instr == "i32.gt_u" or instr == "i32.le_s" or instr == "i32.le_u" or instr == "i32.ge_s" or instr == "i32.ge_u":
        return ["I32", "I32", "I32"]
    elif instr == "i64.eq" or instr == "i64.ne" or instr == "i64.lt_s" or instr == "i64.lt_u" or instr == "i64.gt_s" or instr == "i64.gt_u" or instr == "i64.le_s" or instr == "i64.le_u" or instr == "i64.ge_s" or instr == "i64.ge_u":
        return ["I64", "I64", "I32"]
    elif instr == "f32.eq" or instr == "f32.ne" or instr == "f32.lt" or instr == "f32.gt" or instr == "f32.le" or instr == "f32.ge":
        return ["F32", "F32", "I32"]
    elif instr == "f64.eq" or instr == "f64.ne" or instr == "f64.lt" or instr == "f64.gt" or instr == "f64.le" or instr == "f64.ge":
        return ["F64", "F64", "I32"]
    elif instr == "i32.add" or instr == "i32.sub" or instr == "i32.mul" or instr == "i32.div_s" or instr == "i32.div_u" or instr == "i32.rem_s" or instr == "i32.rem_u" or instr == "i32.and" or instr == "i32.or" or instr == "i32.xor" or instr == "i32.shl" or instr == "i32.shr_s" or instr == "i32.shr_u" or instr == "i32.rotl" or instr == "i32.rotr":
        return ["I32", "I32", "I32"]
    elif instr == "i64.add" or instr == "i64.sub" or instr == "i64.mul" or instr == "i64.div_s" or instr == "i64.div_u" or instr == "i64.rem_s" or instr == "i64.rem_u" or instr == "i64.and" or instr == "i64.or" or instr == "i64.xor" or instr == "i64.shl" or instr == "i64.shr_s" or instr == "i64.shr_u" or instr == "i64.rotl" or instr == "i64.rotr":
        return ["I64", "I64", "I64"]
    elif instr == "f32.add" or instr == "f32.sub" or instr == "f32.mul" or instr == "f32.div" or instr == "f32.min" or instr == "f32.max" or instr == "f32.copysign":
        return ["F32", "F32", "F32"]
    elif instr == "f64.add" or instr == "f64.sub" or instr == "f64.mul" or instr == "f64.div" or instr == "f64.min" or instr == "f64.max" or instr == "f64.copysign":
        return ["F64", "F64", "F64"]
    else:
        return []

def getArgTp(id, instr):
    id = id >> 8
    if id & 7 == 0:
        return getFixedTp(instr)
    argtps = []
    while True:
        low3 = id & 7
        if low3 == 0:
            break
        elif low3 == 1:
            argtps.append("I32")
        elif low3 == 2:
            argtps.append("I64")
        elif low3 == 3:
            argtps.append("F32")
        elif low3 == 4:
            argtps.append("F64")
        id >>= 3
    return argtps


def singleLogBin2Json(path, isFirst=True):
    '''processing raw log into readable format
    
    the format of each line: instruction_name [func_id, instr, arg1, agr2...] [type1,type2...]
    func_id :指令所在的函数（原wasm）instr表示从函数开始第几条指令（从0开始，begin_function等表示块开始和结束的，instr为-1）
    arg     :指令从栈上取出的参数和压入栈中的结果，若类型为I64，单个拆分成两个，若为[arg1, arg2]，原I64表示为(arg2<<32) | arg1
    type    :指令可以作用于多种数据类型时，作为参数的数据的具体类型
    '''
    # 多线程log处理. 当log完成输出时打印\nDONE, 我们以此为标志进行同步
    
    # first time to read. Check Flag here
    # flog = open(path, 'rb+')
    # flog.seek(-5, os.SEEK_END)
    # flag = flog.read(5).strip() #\nDONE
    # # print('flag=', flag)
    # if flag != b'DONE':
    #     if isFirst:
    #         raise RuntimeError("Read Unfinished")
    # else:
    #     # remove signal
    #     for _ in range(5):
    #         flog.seek(-1 ,os.SEEK_END)
    #         flog.truncate()
    # flog.close()
    
    instrs = []
    # argss = []
    # argtpss = []    

    with open(path, "r", encoding='utf-8') as f:
        s = f.read()
        orinums = s.split("α")
        # print(len(orinums))
        nums = []
        for n in orinums:
            ok = True
            if not ok:
                continue
            if str.isdigit(n) or len(n) > 1:
                if '.' in n or 'e' in n or '+' in n or '-' in n:
                    nums.append(float(n))
                else:
                    nums.append(int(n))
    pos = 0
    rts = []
    call_indirect_pos = -1
    idx = 0
    try:
        while pos < len(nums):
            instr = gettype(nums[pos])
            argtps = getArgTp(nums[pos], instr)
            sb = nums[pos]
            instrs.append(instr)
            pos += 1
            cnt = nums[pos]
            pos += 1
            args = nums[pos:pos + cnt]
            # filter 
            # if len(args) < 2 :
            #     raise RuntimeError("Read Unfinished")
            # argss.append(args)
            # argtpss.append(argtps)
            rts.append([sb, instr, args, argtps])
            if 'call_indirect' in instr and call_indirect_pos == -1: # record first action
                call_indirect_pos = idx
            idx += 1
            pos += cnt
    except:
        pass # return logs as more as you can

    return rts, call_indirect_pos

def test():
    # pls fix singleLogBin2Json() 
    logJson, entry = singleLogBin2Json("/home/szh/LOGS/log_3.txt")
    # import pickle
    # print(logJson, entry)
    # with open("/home/szh/dynamicAnalyze/EOSFuzzer/symzzer/1.json", 'w') as f:
        # pick.dump([logJson, entry], f)
    for i in logJson:
        print(i)
     
# test()