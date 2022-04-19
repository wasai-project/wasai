from z3 import *
import symzzer.tainter.utils as utils


def intBinary(instrName, arg1, arg2):
    # ============================= arithmetic ==================================
    if instrName == 'sub':
        result = simplify(arg2 - arg1)
    elif instrName == 'add':
        result = simplify(arg2 + arg1)
    elif instrName == 'mul':
        result = simplify(arg2 * arg1)
    elif instrName == 'div_s':
        result = simplify(arg2 / arg1)
    elif instrName == 'div_u':
        result = simplify(UDiv(arg2, arg1))
    elif instrName == 'rem_s':
        result = simplify(SRem(arg2, arg1))
    elif instrName == 'rem_u':
        result = simplify(URem(arg2, arg1))
    elif instrName == 'ne':
        result = simplify(arg1 != arg2)

    # ============================ bitwise ==================================
    elif instrName == 'and':
        result = simplify(arg1 & arg2)
    elif instrName == 'or':
        result = simplify(arg1 | arg2)
    elif instrName == 'xor':
        result = simplify(arg1 ^ arg2)
    elif instrName == 'shr_s':
        result = simplify(arg2 >> arg1)
    elif instrName == 'shr_u':
        result = simplify(LShR(arg2, arg1))
    elif instrName == 'shl':
        result = simplify(arg2 << arg1)
    elif instrName == 'rotl':
        result = simplify(RotateLeft(arg2, arg1))
    elif instrName == 'rotr':
        result = simplify(RotateRight(arg2, arg1))

    # ================================= logical =================================
    elif instrName == 'eq':
        result = simplify(arg1 == arg2)
    elif instrName == 'ne':
        result = simplify(arg1 != arg2)
    elif instrName == 'lt_s':
        result = simplify(arg2 < arg1)
    elif instrName == 'lt_u':
        result = simplify(ULT(arg2, arg1))
    elif instrName == 'gt_s':
        result = simplify(arg2 > arg1)
    elif instrName == 'gt_u':
        result = simplify(UGT(arg2, arg1))
    elif instrName == 'le_s':
        result = simplify(arg2 <= arg1)
    elif instrName == 'le_u':
        result = simplify(ULE(arg2, arg1))
    elif instrName == 'ge_s':
        result = simplify(arg2 >= arg1)
    elif instrName == 'ge_u':
        result = simplify(UGE(arg2, arg1))
    else:
        raise Exception(
            'Instruction:', instrName, 'not match in binary_int function')
    if instrName == 'eq' or instrName == 'ne' or instrName == 'lt_s' or instrName == 'lt_u' or instrName == 'le_s' or instrName == 'le_u' or instrName == 'gt_s' or instrName == 'gt_u' or instrName == 'ge_s' or instrName == 'ge_u':
        result = simplify(If(result, BitVecVal(1, 32), BitVecVal(0, 32)))
    return result


def intUnary(instrName, arg1):
    # =================== arithmetic =========================
    if instrName in ['clz', 'ctz']:
        # wasm documentation says:
        # This instruction is fully defined when all bits are zero; it returns the number of bits in the operand type.
        # state.symbolic_stack.append(BitVecVal(32, 32))
        raise Exception("No need to handel")

    elif instrName == 'popcnt':
        # wasm documentation says:
        # This instruction is fully defined when all bits are zero; it returns 0.
        # state.symbolic_stack.append(BitVecVal(0, 32))
        raise Exception("No need to handel")

    # ==================== bitwise ==========================

    # ==================== logical =============================
    elif instrName == 'eqz':
        # assert arg0.size() == 32, f"in eqz the argument popped size is {arg1.size()} instead of 32"
        result = simplify(If(arg1 == 0, BitVecVal(1, 32), BitVecVal(0, 32)))
        return result

    else:
        raise Exception(
            'Instruction:', instrName, 'not match in int unary function')


def floatBinary(instrName, arg1, arg2):

    # TODO need to be clarified
    # wasm default rounding rules
    rm = RNE()
    # ==================== arithmetic ==========================
    if instrName == 'add':
        result = simplify(fpAdd(rm, arg2, arg1))
    elif instrName == 'sub':
        result = simplify(fpSub(rm, arg2, arg1))
    elif instrName == 'mul':
        result = simplify(fpMul(rm, arg2, arg1))
    elif instrName == 'div':
        result = simplify(fpDiv(rm, arg2, arg1))
    elif instrName == 'min':
        result = simplify(fpMin(arg2, arg1))
    elif instrName == 'max':
        result = simplify(fpMax(arg2, arg1))
    elif instrName == 'copysign':
        # extract arg2's sign to overwrite arg1's sign
        if arg2.isPositive() ^ arg1.isPositive():
            result = simplify(fpNeg(arg1))
    # =================== bitwise =================================
    # None
    # =================== logical =================================
    elif instrName == 'eq':
        result = simplify(fpEQ(arg1, arg2))
    elif instrName == 'ne':
        result = simplify(fpNEQ(arg1, arg2))
    elif instrName == 'lt':
        result = simplify(fpLT(arg2, arg1))
    elif instrName == 'le':
        result = simplify(fpLEQ(arg2, arg1))
    elif instrName == 'gt':
        result = simplify(fpGT(arg2, arg1))
    elif instrName == 'ge':
        result = simplify(fpGEQ(arg2, arg1))
    else:
        raise Exception(
            'Instruction:', instrName, 'not match in emul_arithmetic_f32 function')
    
    if instrName == 'eq' or instrName == 'ne' or instrName == 'lt' or instrName == 'le' or instrName == 'gt' or instrName == 'ge':
        result = simplify(If(result, BitVecVal(1, 32), BitVecVal(0, 32)))
    return result


def floatUnary(instrName, arg1):

    ftype = utils.getFPType(arg1)

    # ====================== arithmetic ===========================
    if instrName == 'sqrt':
        result = simplify(fpSqrt(rm, arg1))
    elif instrName == 'floor':
        # round toward negative
        rm = RTN()
        result = simplify(fpFPToFP(rm, arg1, ftype))
    elif instrName == 'ceil':
        # round toward positive
        rm = RTP()
        result = simplify(fpFPToFP(rm, arg1, ftype))
    elif instrName == 'trunc':
        # round toward zero
        rm = RTZ()
        result = simplify(fpFPToFP(rm, arg1, ftype))
    elif instrName == 'nearest':
        # round to integeral ties to even
        rm = RNE()
        result = simplify(fpFPToFP(rm, arg1, ftype))
    elif instrName == 'abs':
        result = simplify(fpAbs(arg1))
    elif instrName == 'neg':
        result = simplify(fpNeg(arg1))

    # ===================== logical =============================
    elif instrName == 'eq':
        result = simplify(fpEQ(arg1, arg2))
    elif instrName == 'ne':
        result = simplify(fpNEQ(arg1, arg2))
    elif instrName == 'lt':
        result = simplify(fpLT(arg2, arg1))
    elif instrName == 'le':
        result = simplify(fpLEQ(arg2, arg1))
    elif instrName == 'gt':
        result = simplify(fpGT(arg2, arg1))
    elif instrName == 'ge':
        result = simplify(fpGEQ(arg2, arg1))

    else:
        raise Exception('Instruction:', instrName,
                        'not match in floatUnary function')
    return result



def convertion(instrName, arg0):
    if instrName == 'wrap_i64':
        assert arg0.size() == 64, f'wrap_i64 has wrong arg type ;arg0:{arg0}, {arg0.size()}'
        divisor = BitVecVal(2 ** 32, 64)
        # mod
        result = simplify(Extract(31, 0, arg0 % divisor))

    elif instrName == 'extend_i32_s':
        assert arg0.size() == 32, 'extend_s_i32 has wrong arg type'
        result = simplify(SignExt(32, arg0))
        
    elif instrName == 'extend_i32_u':
        assert arg0.size() == 32, 'extend_u_i32 has wrong arg type'
        result = simplify(ZeroExt(32, arg0))

    elif instrName == 'trunc_s_f32':
        assert arg0.ebits() == 8, 'trunc_s_f32 has wrong arg type'
        assert arg0.sbits() == 24, 'trunc_s_f32 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToSBV(rm, arg0, BitVecSort(32)))
        assert result.size() == 32, 'trunc_s_f32 convert fail'
    elif instrName == 'trunc_s_f64':
        assert arg0.ebits() == 11, 'trunc_s_f64 has wrong arg type'
        assert arg0.sbits() == 53, 'trunc_s_f64 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToSBV(rm, arg0, BitVecSort(32)))
        assert result.size() == 32, 'trunc_s_f64 convert fail'
    elif instrName == 'trunc_s_f32':
        assert arg0.ebits() == 8, 'trunc_s_f32 has wrong arg type'
        assert arg0.sbits() == 24, 'trunc_s_f32 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToSBV(rm, arg0, BitVecSort(64)))
        assert result.size() == 64, 'trunc_s_f32 convert fail'
    elif instrName == 'trunc_s_f64':
        assert arg0.ebits() == 11, 'trunc_s_f64 has wrong arg type'
        assert arg0.sbits() == 53, 'trunc_s_f64 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToSBV(rm, arg0, BitVecSort(64)))
        assert result.size() == 64, 'trunc_s_f64 convert fail'
    elif instrName == 'trunc_u_f32':
        assert arg0.ebits() == 8, 'trunc_u_f32 has wrong arg type'
        assert arg0.sbits() == 24, 'trunc_u_f32 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToUBV(rm, arg0, BitVecSort(32)))
        assert result.size() == 32, 'trunc_u_f32 convert fail'
    elif instrName == 'trunc_u_f64':
        assert arg0.ebits() == 11, 'trunc_u_f64 has wrong arg type'
        assert arg0.sbits() == 53, 'trunc_u_f64 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToUBV(rm, arg0, BitVecSort(32)))
        assert result.size() == 32, 'trunc_u_f64 convert fail'
    elif instrName == 'trunc_u_f32':
        assert arg0.ebits() == 8, 'trunc_u_f32 has wrong arg type'
        assert arg0.sbits() == 24, 'trunc_u_f32 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToUBV(rm, arg0, BitVecSort(64)))
        assert result.size() == 64, 'trunc_u_f32 convert fail'
    elif instrName == 'trunc_u_f64':
        assert arg0.ebits() == 11, 'trunc_u_f64 has wrong arg type'
        assert arg0.sbits() == 53, 'trunc_u_f64 has wrong arg type'

        rm = RTZ()
        result = simplify(fpToUBV(rm, arg0, BitVecSort(64)))
        assert result.size() == 64, 'trunc_u_f64 convert fail'
    elif instrName == 'demote_f64':
        assert arg0.ebits() == 11, 'demote_f64 has wrong arg type'
        assert arg0.sbits() == 53, 'demote_f64 has wrong arg type'

        rm = RNE()
        result = simplify(fpFPToFP(rm, arg0, Float32()))
        assert result.ebits() == 8, 'demote_f64 conversion fail'
        assert result.sbits() == 24, 'demote_f64 conversion fail'
    elif instrName == 'promote_f32':
        assert arg0.ebits() == 8, 'promote_f32 has wrong arg type'
        assert arg0.sbits() == 24, 'promote_f32 has wrong arg type'

        rm = RNE()
        result = simplify(fpFPToFP(rm, arg0, Float64()))
        assert result.ebits() == 11, 'promote_f32 conversion fail'
        assert result.sbits() == 53, 'promote_f32 conversion fail'
    elif instrName == 'convert_s_i32':
        assert arg0.size() == 32, 'convert_s_i32 has wrong arg type'

        rm = RNE()
        result = simplify(fpSignedToFP(rm, arg0, Float32()))
        assert result.ebits() == 8, 'convert_s_i32 conversion fail'
        assert result.sbits() == 24, 'convert_s_i32 conversion fail'
    elif instrName == 'convert_s_i64':
        assert arg0.size() == 64, 'convert_s_i64 has wrong arg type'

        rm = RNE()
        result = simplify(fpSignedToFP(rm, arg0, Float32()))
        assert result.ebits() == 8, 'convert_s_i64 conversion fail'
        assert result.sbits() == 24, 'convert_s_i64 conversion fail'
    elif instrName == 'convert_s_i32':
        assert arg0.size() == 32, 'convert_s_i32 has wrong arg type'

        rm = RNE()
        result = simplify(fpSignedToFP(rm, arg0, Float64()))
        assert result.ebits() == 11, 'convert_s_i32 conversion fail'
        assert result.sbits() == 53, 'convert_s_i32 conversion fail'
    elif instrName == 'convert_s_i64':
        assert arg0.size() == 64, 'convert_s_i64 has wrong arg type'

        rm = RNE()
        result = simplify(fpSignedToFP(rm, arg0, Float64()))
        assert result.ebits() == 11, 'convert_s_i64 conversion fail'
        assert result.sbits() == 53, 'convert_s_i64 conversion fail'
    elif instrName == 'convert_u_i32':
        assert arg0.size() == 32, 'convert_u_i32 has wrong arg type'

        rm = RNE()
        result = simplify(fpUnsignedToFP(rm, arg0, Float32()))
        assert result.ebits() == 8, 'convert_u_i32 conversion fail'
        assert result.sbits() == 24, 'convert_u_i32 conversion fail'
    elif instrName == 'convert_u_i64':
        assert arg0.size() == 64, 'convert_u_i64 has wrong arg type'

        rm = RNE()
        result = simplify(fpUnsignedToFP(rm, arg0, Float32()))
        assert result.ebits() == 8, 'convert_u_i64 conversion fail'
        assert result.sbits() == 24, 'convert_u_i64 conversion fail'
    elif instrName == 'convert_u_i32':
        assert arg0.size() == 32, 'convert_u_i32 has wrong arg type'

        rm = RNE()
        result = simplify(fpUnsignedToFP(rm, arg0, Float64()))
        assert result.ebits() == 11, 'convert_u_i32 conversion fail'
        assert result.sbits() == 53, 'convert_u_i32 conversion fail'
    elif instrName == 'convert_u_i64':
        assert arg0.size() == 64, 'convert_u_i64 has wrong arg type'

        rm = RNE()
        result = simplify(fpUnsignedToFP(rm, arg0, Float64()))
        assert result.ebits() == 11, 'convert_u_i64 conversion fail'
        assert result.sbits() == 53, 'convert_u_i64 conversion fail'
    elif instrName == 'reinterpret_f32':
        assert arg0.ebits() == 8, 'reinterpret_f32 has wrong arg type'
        assert arg0.sbits() == 24, 'reinterpret_f32 has wrong arg type'

        result = simplify(fpToIEEEBV(arg0))
        assert result.size() == 32, 'reinterpret_f32 conversion fail'
    elif instrName == 'reinterpret_f64':
        assert arg0.ebits() == 11, 'reinterpret_f64 has wrong arg type'
        assert arg0.sbits() == 53, 'reinterpret_f64 has wrong arg type'

        result = simplify(fpToIEEEBV(arg0))
        assert result.size() == 64, 'reinterpret_f64 conversion fail'
    elif instrName == 'reinterpret_i32':
        assert arg0.size() == 32, 'reinterpret_i32 has wrong arg type'

        result = simplify(fpBVToFP(arg0, Float32()))
        assert result.ebits() == 8, 'reinterpret_i32 conversion fail'
        assert result.sbits() == 24, 'reinterpret_i32 conversion fail'
    elif instrName == 'reinterpret_i64':
        assert arg0.size() == 64, 'reinterpret_i64 has wrong arg type'

        result = simplify(fpBVToFP(arg0, Float64()))
        assert result.ebits() == 11, 'reinterpret_i64 conversion fail'
        assert result.sbits() == 53, 'reinterpret_i64 conversion fail'
    else:
        raise Exception('Instruction:', instrName,
                        'not match in emul_conversion function')
    return result


