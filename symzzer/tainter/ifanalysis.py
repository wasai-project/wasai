import json
import collections


class Analysis(object):
    debug = False
    print("=========================")
    print("Starting taint analysis")

    '''
    /*
     * Mirror program state track taints instead of actual value
     * TODO: Move memory tracking into reusable analysis component
     */
     '''
    class listProto(object):
        def __init__(self, element=None):
            if element:
                self.items = [element]
            else:
                self.items = []

        def size(self):
            return len(self.items)

        def isEmpty(self):
            return self.size ==0

        def push(self, element):
            self.items.append(element)

        def peek(self):
            if self.size:
                return self.items[-1]
            else:
                return []
        def pop(self):
            if self.size:
                return self.items.pop()
            else:
                return []


    stackPrototype = collections.namedtuple('stack', ['blocks', 'locals'])(listProto(), listProto())
    stack = listProto(stackPrototype.copy())

    def values():
        # FIXME || [] is a hack to get it to run without exceptions
        try:
            return stack.peek().blocks.peek()
        except:
            return []

    memory = []
    glovalsArg = []

    returnValue # to propagate return value's taint from end() to call_post()

    '''
     * Taint policy: sources and sink
    '''
    def findSourceSinkFcts() {
        sourceFctIdx = -1
        sinkFctIdx = -1
        for (i = 0 i < Wasabi.module.info.defs.length i++) {
            fct = Wasabi.module.info.defs[i]
            if (fct.export === "taint_source" || fct.export === "_markSource") {
                sourceFctIdx = i
            }
            if (fct.export === "taint_sink" || fct.export === "_sink") {
                sinkFctIdx = i
            }
        }
        if (sourceFctIdx === -1) print("Warning: No exported source def found.")
        if (sinkFctIdx === -1) print("Warning: No exported sink def found.")
        return {sourceFctIdx:sourceFctIdx, sinkFctIdx:sinkFctIdx}
    }

    {sourceFctIdx, sinkFctIdx} = findSourceSinkFcts()

    class Taint(object):
        def __init__(self, tag= 1):
            self.label = 1 if tag else 0# can hold any kind of more complex label for now, just 0 (not tainted) and 1 (tainted)
        def __str__(self):
            return "taint-" + str(self.label)

    def join(taint1, taint2):
        resultTaint = Taint()
        if taint1.label == 1 or taint2.label == 1:
            resultTaint.label = 1
        return resultTaint
    

    def ensureTaint(value, location):
        if instanceof(value, Taint):
            return value
        else:
            if debug:
                print("ensureTaint: creating taint for value at ", location)
            return Taint()


    def run():
        for instruction in xxx:
            exec_one(instruction)

    def exec_one(instr, args):
        if instr == 'start':
            for i in range(12):
                _t = Taint()
                _t.label = 1
                stack.peek().locals.append(_t)

            # create taints for all glovals
            # for (i = 0 i < Wasabi.module.info.glovalsArg.length i++) {
            #     const global = Wasabi.module.info.glovalsArg[i]
            #     if debug:print("Creating taint for glovals[" + i + "]")
            #     glovalsArg[i] = Taint()
            # }

            # any other data for which need to initialize taints?
        elif instr == "if":
            values().pop()
        
        elif instr == 'br':#(location, target) {
            stack.peek().blocks.pop()
        # },

        elif  instr =='br_if':#(location, conditionalTarget, condition) {
            values().pop()
            if (condition) {
                stack.peek().blocks.pop()
            }
        # },

        elif instr == 'br_table':#(location, table, defaultTarget, tableIdx) {
            values().pop()
            stack.peek().blocks.pop()
        # },

        elif instr == 'drop':#(location, value) {
            values().pop()
        # },

        elif instr == 'select':#(location, cond, first, second) {
            values().pop()
            values().pop()
            values().pop()
        # },

        elif instr == 'begin':#(location, type) {
            stack.peek().blocks.push(listProto)
        # },

        elif instr == 'end':#(location, atype, beginLocation) {
            resultTaintArr = stack.peek().blocks.pop()
            # FIXME sometimes pop() returns undefined, not just an empty []. Why? 
            # hacky workaround: just return early if [resultTaint] pattern match would fail
            if (resultTaintArr == []) return
            resultTaint = resultTaintArr
            if atype == "function" and resultTaint:
                returnValue = ensureTaint(resultTaint, location):
                    if debug :
                        print("end(): Storing return value's taint ", returnValue, " at ", location)
            

        elif instr == 'call_pre':#(location, targetFunc, args, indirectTableIdx) {
            if indirectTableIdx != None:
                values().pop()
            
            argTaints = []
            for arg in args:
                taint = ensureTaint(values().pop(), location)
                argTaints.push(taint)
                if targetFunc == sourceFctIdx:
                    taint.label = 1
                    print("Source: Marking value as ", taint)
                
                if targetFunc == sinkFctIdx and taint.label == 1:
                    print("Tainted value reached sink at ", location)
             
            _ = collections.namedtuple('stack', ['blocks', 'locals'])(listProto(), argTaints)
            stack.push(_)
      

        elif instr == 'call_post':#(location, vals) {
            stack.pop()
            if returnValue != None
                if debug:
                    print("Found return value's taint in call_post at ", location)
                values().push(returnValue)
                returnValue = None
            

        elif instr =='return':#_(location, values) {
            # Note on interaction between end() and return_():
            #  * end() may or may not be called on def returns
            #  * return_() may or may not be called on def returns
            #  * end() always happens before return_()
            #  * We try to retrieve the return value taint in end(),
            #    and if none found, we try to retrieve it in return_()
            if returnValue == None and stack.peek().blocks.size != 0) {
                resultTaint = stack.peek().blocks.pop()
                returnValue = ensureTaint(resultTaint, location)
                if debug:
                    print("return_(): Storing return value's taint ", returnValue, " at ", location)
            

        elif 'const' in instr:#_(location, op, value) {
            if debug:
                print("New taint at ", location)
            values().push(Taint())
 
        #TODO
        elif instr == 'unary':#(location, op, input, result) { #一元
            taint = ensureTaint(values().pop(), location)
            taintResult = Taint()
            taintResult.label = taint.label
            values().push(taintResult)
    

        elif instr == 'binary':#(location, op, first, second, result) { # 二元
            taint1 = ensureTaint(values().pop(), location)
            taint2 = ensureTaint(values().pop(), location)
            taintResult = join(taint1, taint2)
            if debug:
                print("Result of binary is ", taintResult, " at ", location)
            values().push(taintResult)

        elif instr == 'load':#(location, op, memarg, value) {
            values().pop()
            effectiveAddr = memarg.addr + memarg.offset #TODO
            taint = ensureTaint(memory[effectiveAddr], location)
            if debug:
                print("Memory load from address " + effectiveAddr + " with taint " + taint)
            values().push(taint)
        

        elif instr == 'store':#(location, op, memarg, value) {
            taint = ensureTaint(values().pop(), location)
            values().pop()
            effectiveAddr = memarg.addr + memarg.offset
            if debug:
                print("Memory store to address " + effectiveAddr + " with taint " + taint)
            memory[effectiveAddr] = taint
        

        elif instr == 'memory.size':#(location, currentSizePages) {
            values().push(Taint())
    

        elif instr == 'memory.grow':#(location, byPages, previousSizePages) {
            values().pop()
            values().push(Taint())
      

        elif 'local' in instr:#(location, op, localIndex, value) {
            if instr == "local.set": 
                taint = ensureTaint(values().pop(), location)
                stack.pop().locals[localIndex] = taint
                if debug:
                    print("Setting local variable with ", taint, " at ", location)
                return
            
            elif instr== "local.tee": 
                taint = ensureTaint(values().pop(), location)
                stack.pop().locals[localIndex] = taint
                return
            
            elif instr == "local.get":
                taint = ensureTaint(stack.pop().locals[localIndex], location)
                values().push(taint)
                if debug:
                    print("Getting local variable with ", taint, " at ", location)
                return
        
        elif 'global' in instr:#(location, op, globalIndex, value) {
            if op == "global.set":
                taint = ensureTaint(values().pop(), location)
                glovalsArg[globalIndex] = taint
                return
            elif op == "global.get":
                taint = ensureTaint(glovalsArg[globalIndex], location)
                values().push(taint)
                return
