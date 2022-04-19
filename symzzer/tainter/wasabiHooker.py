from symzzer.tainter.analysis import Analysis
from symzzer.tainter.opcodes import opcodeToType
from symzzer.tainter.utils import Location_t, Memarg_t
import collections


class Wasabi(object):
    def __init__(self, inputTp, inputJson, libf, actFuncID):

        self.analysis = Analysis(inputTp, inputJson, libf, actFuncID)
        self.initHooker()

    def initHooker(self):
        self.defaultHooks = {
            "start":       lambda location:                                      self.analysis.start        (location),
            "nop":         lambda location:                                      self.analysis.nop          (location),
            "unreachable": lambda location:                                      self.analysis.unreachable  (location),
            "if_":         lambda location, condition:                           self.analysis.if_          (location, condition),
            "br":          lambda location, targetLabel, targetInstr:            self.analysis.br           (location, []),
            "br_if":       lambda location, condition, targetLabel, targetInstr: self.analysis.br_if        (location, [], condition),
            "br_table":    lambda location, tableIdx, brTablesInfoIdx:           self.analysis.br_table     (location, [], [], tableIdx),
            "begin":       lambda location:                                      self.analysis.begin        (location, location.instr.split('_')[1]),
            "end":         lambda location, *beginInstr:                         self.analysis.end          (location, location.instr.split('_')[1], []),
            "drop":        lambda location, value:                               self.analysis.drop         (location, value),
            "select":      lambda location, condition, input0, input1:           self.analysis.select       (location, condition, input0, input1),
            "call_pre":    lambda location, targetFunc, *args:                   self.analysis.call_pre     (location, targetFunc, args, targetFunc if location.instr.startswith('call_indirect') else []),
            "call_post":   lambda location, *results:                            self.analysis.call_post    (location, results),
            "return_":     lambda location, *results:                            self.analysis.return_      (location, results),
            "const_":      lambda location, value:                               self.analysis.const_       (location, location.instr, value),
            "unary":       lambda location, input0, result0:                     self.analysis.unary        (location, location.instr, input0, result0),
            "binary":      lambda location, input0, input1, result0:             self.analysis.binary       (location, location.instr, input0, input1, result0),
            "load":        lambda location, offset, align, addr, value:          self.analysis.load         (location, location.instr, Memarg_t(addr, offset, align), value),
            "store":       lambda location, offset, align, addr, value:          self.analysis.store        (location, location.instr, Memarg_t(addr, offset, align), value),
            "memory_size": lambda location, currentSizePages:                    self.analysis.memory_size  (location, currentSizePages),
            "memory_grow": lambda location, byPages, previousSizePages:          self.analysis.memory_grow  (location, byPages, previousSizePages),
            "local":       lambda location, index, value:                        self.analysis.local        (location, location.instr.split('_')[0], index, value),
            "global":      lambda location, index, value:                        self.analysis.globalh      (location, location.instr.split('_')[0], index, value),
        }

    def lowlevelHooks(self, opcode, args):
        try:
            location = Location_t(*args[:3])
            args = [location] + args[3:]
            self.defaultHooks[opcodeToType[opcode]](*args)
        except Exception as e:
            print(e)
            print(f'[-] {opcode} @@ {args}')
            raise RuntimeError(f"ERROR hooker for [{opcode}] @ {args}")
            