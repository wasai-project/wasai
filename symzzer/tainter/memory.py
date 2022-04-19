import z3

class SymbolMemory:
    def __init__(self):
        self.z3Array = z3.Array("memory", z3.BitVecSort(32), z3.BitVecSort(8))#32, 32#
        self.written = set()
        self.qmem = dict()

    # check if the memory has been written, if not, fill with a constant
    def prefill(self, addr, l, value):
        # carch ?
        for i in range(addr, addr + l):
            if i not in self.written:
                self.written.add(i)
                shr = z3.simplify(z3.Extract(7, 0, value >> ((i - addr) << 3)))
                self.z3Array = z3.simplify(z3.Store(self.z3Array, i, shr))

    # load tp1 in memory and convert it to tp2
    def load(self, z3Addr, addrVal, tp1, l1, tp2, l2, value):
        # cache
        if (addrVal, l2) in self.qmem:
            return self.qmem[(addrVal, l2)]

        if 'pointer' in str(z3Addr):
            if tp1 == 'I':
                self.store(z3.BitVecVal(addrVal, 32), addrVal, tp1, l1, l1, z3.BitVec("vector_" + argName, l1 * 8))
            elif tp1 == 'F':
                if l1 == 4:
                    self.store(z3.BitVecVal(addrVal, 32), addrVal, tp1, l1, l1, z3.FP("vector_" + argName, z3.Float32()))
                else:
                    self.store(z3.BitVecVal(addrVal, 32), addrVal, tp1, l1, l1, z3.FP("vector_" + argName, z3.Float64()))
            self.load(z3.BitVecVal(addrVal, 32), addrVal, tp1, l1, tp2, l2, value)

        if tp1 == "F":
            value = z3.simplify(z3.fpToIEEEBV(value))
        self.prefill(addrVal, l1, value)
        ret = z3.simplify(z3.Select(self.z3Array, z3Addr))
        for i in range(1, l1):
            ret = z3.simplify(
                z3.Concat(z3.Select(self.z3Array, z3Addr + i), ret))
        if l2 > l1:
            if tp2[-1] == "U":
                ret = z3.ZeroExt((l2 - l1) << 3, ret)
            else:
                ret = z3.SignExt((l2 - l1) << 3, ret)
        if tp2 == "F":
            if l1*8 == 32: # revise, pls
                ret = z3.fpBVToFP(ret, z3.Float32())
            elif l1*8 == 64:
                ret = z3.fpBVToFP(ret, z3.Float64())
    
        return z3.simplify(ret)

    # save tp1 l1 in memory as tp1 l2
    def store(self, z3Addr, addrVal, tp, l1, l2, value):
        # =============== cache ====================
        drops = list()
        for (_addr, _offset), _val in self.qmem.items():
            if max(_addr, addrVal) < min(_addr+_offset, addrVal+l2):
                # overlap
                drops.append((_addr, _offset))
        
        # remove overlapped
        for (_addr, _offset) in drops:
            self.qmem.pop((_addr, _offset))
        
        # cache
        self.qmem[(addrVal, l2)] = value

        # ============== model =====================
        if tp == "F":
            value = z3.simplify(z3.fpToIEEEBV(value))
        for i in range(0, l1):
            self.written.add(addrVal + i)
            shr = z3.simplify(z3.Extract(7, 0, value >> (i << 3)))
            self.z3Array = z3.simplify(z3.Store(self.z3Array, z3Addr + i, shr))
