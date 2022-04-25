# copyright from https://github.com/pventuzelo/octopus/blob/master/octopus/core/basicblock.py:class BasicBlock

class BasicBlock(object):
    """BasicBlock """
    def __init__(self, start_offset=0x00, start_instr=None,
                 name='block_default_name'):
        self.start_offset = start_offset
        self.start_instr = start_instr
        self.name = name
        self.end_offset = start_offset
        self.end_instr = start_instr
        self.instructions = list()
        self.function_id = int(name.split('_')[1], 16)
        self.to_nodes = []

    # @property
    # def size(self):
    #     return self.end_offset - self.start_offset


class Instruction(object):
    """Instruction """
    def __init__(self, opcode, name, args, targs):
        self.opcode = opcode
        self.name = name
        self.args = args
        self.targs = targs
        self.related_idx = args[1]
        self.function_id = args[0]
