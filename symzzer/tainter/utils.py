import collections
from z3 import BitVecVal, FPSortRef, Float32, Float64, FPVal, FPNumRef, BitVecRef
import re
from numbers import Number

Location_t = collections.namedtuple('Location', ['func', 'shift', 'instr'])
Location_FB = collections.namedtuple('Location_FB', ['func', 'shift', 'jump'])

Memarg_t = collections.namedtuple("Memarg_t", ["addr", "offset", "align"])


def getFPType(arg):
    # assert isinstance(arg, FPSortRef), "Processing is not Float()"
    # assert isinstance(arg, FPNumRef), "Processing is not Float()"
    size = (arg.ebits(), arg.sbits())
    return Float32() if size == (8, 24) else Float64()

def get_concrete(exp):
    if isinstance(exp, BitVecRef):
        return exp.as_long()
    elif isinstance(exp, Number):
        return exp
    else:
        raise RuntimeError("Not concrete:", exp)

def tp2len(typeName):
    # print(typeName)
    return int(typeName[1:])

def localPos(name):
    name = str(name).strip()
    assert name[0] == 'L', "ERROR local symbolc"
    t = re.search(r"L(\d+)", name)
    return int(t.group(1)) 

def structEPos(name):
    name = str(name).strip()
    assert name.startswith("struct_L") , "ERROR <struct>"
    t = re.search(r"struct_L(\d+)_(\d+)", name)
    return int(t.group(2)) 

# def buildArgs(instr, args, types):
#     DynamicArg = collections.namedtuple('DynamicArg', ['type', 'value'])
#     rts = []
#     if 'load' in instr or 'store' in instr:
#         if len(args) == 7:
#             return args[:5] + [(args[6] << 32) | args[5]]
#         else:
#             return args
#     if 'const' in instr:
#         if len(args) == 4:
#             return args[:2] + [BitVecVal((args[3] << 32) | args[2], 32)]
#         else:
#             return args[:2] + [BitVecVal(args[2], 32)]

#     idx = 0
#     alen = types.count('F64') + types.count('F32') + \
#         types.count('I32') + types.count('I64') * 2
#     realArgs = args[len(args) - alen:]
#     print("REAL ARGS", realArgs)
#     for t in types:
#         if t == 'I32' or t == 'F32' or t == 'F64':
#             print("IDX", idx)
#             val = realArgs[idx]
#             idx += 1
#         elif t == 'I64':
#             arg1 = realArgs[idx]
#             arg2 = realArgs[idx+1]
#             val = (arg2 << 32) | arg1
#             idx += 2
#         dataSize = tp2len(t)
#         if t[0] == 'I':
#             result = BitVecVal(val, dataSize)
#         else:  # Float
#             if dataSize == 32:
#                 result = FPVal(val, Float32())
#             elif dataSize == 64:
#                 result = FPVal(val, Float64())
#         rts.append(result)

#         # rts.append(val)
#     return args[:len(args)-alen] + rts

def buildArgs(instr, args, types):
    # DynamicArg = collections.namedtuple('DynamicArg', ['type', 'value'])
    rts = []
    # if 'load' in instr or 'store' in instr:
    #     if len(args) == 7:
    #         return args[:5] + [BitVecVal((args[6] << 32) | args[5], 64)]
    #     else:
    #         args[-1] = BitVecVal(args[-1], 32)
    #         return args
    # if 'const' in instr:
    #     if len(args) == 4:
    #         return args[:2] + [BitVecVal((args[3] << 32) | args[2], 64)]
    #     else:
    #         return args[:2] + [BitVecVal(args[2], 32)]
    idx = 0
    alen = types.count('F64') + types.count('F32') + \
        types.count('I32') + types.count('I64') * 2
    realArgs = args[len(args) - alen:]
    # print('--buildArg---', instr, args, types)
    for t in types:
        if t == 'I32' or t == 'F32' or t == 'F64':
            val = realArgs[idx]
            idx += 1
        elif t == 'I64':
            arg1 = realArgs[idx]
            arg2 = realArgs[idx+1]
            val = (arg2 << 32) | arg1
            idx += 2
        
        dataSize = tp2len(t)
        if t[0] == 'I':
            result = BitVecVal(val, dataSize)
        else:  # Floatvim
            if dataSize == 32:
                result = FPVal(val, Float32())
            elif dataSize == 64:
                result = FPVal(val, Float64())
        rts.append(result)

        # rts.append(val)
    args = args[:len(args)-alen] + rts
    return args[:2] + [instr] + args[2:]
