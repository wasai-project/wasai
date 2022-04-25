from symzzer.tainter.analysis import Analysis
from symzzer.tainter.opcodes import opcodeToType
from symzzer.tainter.utils import Location_t, Memarg_t
import collections


class Wasabi(object):
    def __init__(self, inputTp, inputJson, libf, actFuncID):
        # self.Location_t = collections.namedtuple('Location', ['func', 'instr'])

        # self.module = collections.namedtuple('module', ['info'])({})
        # with('...wasabi.js', 'r') as f:
        #     _pattern = "Wasabi.module.info ="
        #     for line in f.readlines():
        #         if line.startswith() == _pattern:
        #             self.module.info = json.loads(line[len(_pattern):])
        #             break
        # if  self.module.info not:
        #     raise RuntimeError("Cannot prase wasabi hooker")
        # self.info = {"functions":[{"type":"|i","import":["env","action_data_size"],"export":[],"locals":"","instrCount":0},{"type":"ii|i","import":["env","read_action_data"],"export":[],"locals":"","instrCount":0},{"type":"ii|","import":["env","eosio_assert"],"export":[],"locals":"","instrCount":0},{"type":"i|","import":["env","prints"],"export":[],"locals":"","instrCount":0},{"type":"iii|i","import":["env","memcpy"],"export":[],"locals":"","instrCount":0},{"type":"I|","import":["env","printn"],"export":[],"locals":"","instrCount":0},{"type":"ii|","import":["env","send_inline"],"export":[],"locals":"","instrCount":0},{"type":"I|","import":["env","printi"],"export":[],"locals":"","instrCount":0},{"type":"ii|","import":["env","prints_l"],"export":[],"locals":"","instrCount":0},{"type":"I|","import":["env","printui"],"export":[],"locals":"","instrCount":0},{"type":"|","import":["env","abort"],"export":[],"locals":"","instrCount":0},{"type":"iii|i","import":["env","memset"],"export":[],"locals":"","instrCount":0},{"type":"iii|i","import":["env","memmove"],"export":[],"locals":"","instrCount":0},{"type":"IIII|i","import":["env","__unordtf2"],"export":[],"locals":"","instrCount":0},{"type":"IIII|i","import":["env","__eqtf2"],"export":[],"locals":"","instrCount":0},{"type":"iIIII|","import":["env","__multf3"],"export":[],"locals":"","instrCount":0},{"type":"iIIII|","import":["env","__addtf3"],"export":[],"locals":"","instrCount":0},{"type":"iIIII|","import":["env","__subtf3"],"export":[],"locals":"","instrCount":0},{"type":"IIII|i","import":["env","__netf2"],"export":[],"locals":"","instrCount":0},{"type":"II|i","import":["env","__fixunstfsi"],"export":[],"locals":"","instrCount":0},{"type":"ii|","import":["env","__floatunsitf"],"export":[],"locals":"","instrCount":0},{"type":"II|i","import":["env","__fixtfsi"],"export":[],"locals":"","instrCount":0},{"type":"ii|","import":["env","__floatsitf"],"export":[],"locals":"","instrCount":0},{"type":"iF|","import":["env","__extenddftf2"],"export":[],"locals":"","instrCount":0},{"type":"if|","import":["env","__extendsftf2"],"export":[],"locals":"","instrCount":0},{"type":"iIIII|","import":["env","__divtf3"],"export":[],"locals":"","instrCount":0},{"type":"IIII|i","import":["env","__letf2"],"export":[],"locals":"","instrCount":0},{"type":"II|F","import":["env","__trunctfdf2"],"export":[],"locals":"","instrCount":0},{"type":"IIII|i","import":["env","__getf2"],"export":[],"locals":"","instrCount":0},{"type":"II|f","import":["env","__trunctfsf2"],"export":[],"locals":"","instrCount":0},{"type":"ii|","import":["env","set_blockchain_parameters_packed"],"export":[],"locals":"","instrCount":0},{"type":"ii|i","import":["env","get_blockchain_parameters_packed"],"export":[],"locals":"","instrCount":0},{"type":"|","import":null,"export":[],"locals":"","instrCount":1},{"type":"III|","import":null,"export":["apply"],"locals":"iIIiIiI","instrCount":301},{"type":"iIIii|","import":null,"export":[],"locals":"","instrCount":5},{"type":"ii|i","import":null,"export":[],"locals":"iiiiII","instrCount":225},{"type":"iIi|","import":null,"export":[],"locals":"","instrCount":11},{"type":"ii|i","import":null,"export":[],"locals":"iiiiiiIiIi","instrCount":289},{"type":"iIIIiii|","import":null,"export":[],"locals":"iIIiII","instrCount":443},{"type":"ii|i","import":null,"export":[],"locals":"iiiiIiI","instrCount":229},{"type":"ii|","import":null,"export":[],"locals":"ii","instrCount":110},{"type":"ii|","import":null,"export":[],"locals":"iiIIii","instrCount":153},{"type":"i|","import":null,"export":[],"locals":"iiIiIIiiiII","instrCount":120},{"type":"ii|","import":null,"export":[],"locals":"ii","instrCount":160},{"type":"ii|","import":null,"export":[],"locals":"iiIIIiii","instrCount":161},{"type":"ii|","import":null,"export":[],"locals":"iiiiii","instrCount":167},{"type":"ii|","import":null,"export":[],"locals":"ii","instrCount":110},{"type":"ii|","import":null,"export":[],"locals":"iiiiiiI","instrCount":166},{"type":"ii|","import":null,"export":[],"locals":"iI","instrCount":141},{"type":"ii|i","import":null,"export":[],"locals":"iiIiiii","instrCount":132},{"type":"ii|i","import":null,"export":[],"locals":"iIiiii","instrCount":147},{"type":"ii|i","import":null,"export":[],"locals":"iIiiiii","instrCount":107},{"type":"ii|i","import":null,"export":[],"locals":"iiiiii","instrCount":208},{"type":"ii|i","import":null,"export":[],"locals":"iiIiii","instrCount":132},{"type":"i|i","import":null,"export":["_Znwj"],"locals":"ii","instrCount":28},{"type":"i|i","import":null,"export":["_Znaj"],"locals":"","instrCount":3},{"type":"i|","import":null,"export":["_ZdlPv"],"locals":"","instrCount":8},{"type":"i|","import":null,"export":["_ZdaPv"],"locals":"","instrCount":3},{"type":"i|","import":null,"export":[],"locals":"","instrCount":3},{"type":"ii|i","import":null,"export":[],"locals":"iii","instrCount":99},{"type":"ii|","import":null,"export":[],"locals":"iiiiiii","instrCount":203},{"type":"i|","import":null,"export":[],"locals":"","instrCount":3},{"type":"i|","import":null,"export":[],"locals":"","instrCount":1},{"type":"i|i","import":null,"export":[],"locals":"","instrCount":4},{"type":"ii|i","import":null,"export":[],"locals":"iiiiiiiiiiii","instrCount":290},{"type":"i|i","import":null,"export":[],"locals":"iiiiiiii","instrCount":322},{"type":"i|","import":null,"export":[],"locals":"iii","instrCount":63}],"globals":"iii","start":null,"tableExportName":"__wasabi_table","brTables":[]}

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
        # print('--- ', opcode, opcodeToType[opcode], args)
        # lambda opcode, args: self.defaultHooks[opcodeToType[opcode]](*args)
        # print("OP", opcode, args)
        # print(args)
        # print([type(a) for a in args])
        # location = Location_t(*args[:3])
        # args = [location] + args[3:]
        # self.defaultHooks[opcodeToType[opcode]](*args)

        try:
            # print("???",args)
            location = Location_t(*args[:3])
            args = [location] + args[3:]
            # print(opcode, args)
            self.defaultHooks[opcodeToType[opcode]](*args)
        except Exception as e:
            print(e)
            print(f'[-] {opcode} @@ {args}')
            raise RuntimeError(f"ERROR hooker for [{opcode}] @ {args}")
            