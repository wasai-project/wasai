import os
import re

from genEvil.injectWasm import getWasmBody, parse


def reduceCoverage(rawPath, funcID={'apply': -1, 'transfer':-1}):
    print("start")
    os.system(f"eosio-wasm2wast {rawPath} > raw.wat")
    with open("raw.wat", 'r') as f:
        raw = f.read().strip()

    evil = "(module\n"
    body = getWasmBody(raw)
    for t in parse(body):
        if not t.strip().startswith('(func'):
            evil += t
        else:
            contents = t.split('\n')
            fid = int(re.search(r";(\d+);", contents[0]).group(1))

            if fid == funcID['apply']:
                # obfuscate magic number
                newContents = list()
                idx = 0 
                while idx < len(contents) - 1:
                    if contents[idx].strip() == 'get_local 2' and \
                        contents[idx+1].strip() == 'i64.const -3617168760277827584':

                        newContents.append('get_local 2')
                        newContents.append('get_local 2')
                        newContents.append('i64.popcnt')
                        newContents.append('i64.const -3617168760277827607')
                        newContents.append('i64.add')
                        idx += 2
                        continue

                    else:
                        newContents.append(contents[idx])
                        idx += 1
                newContents.append(contents[-1])
                contents = newContents

            
            elif fid == funcID['transfer']:
                for idx, line in enumerate(contents):
                    if not line.strip().startswith('('):
                        break
                code  = "(if (i64.ne (get_local 3)  (i64.load) (i64.const 100000) ) (then   (unreachable) ) )\n" 
                code += "(if (i64.ne (get_local 3) (i64.load offset=8) (i64.const 1397703940) ) (then  (unreachable) ) )\n"
                contents = contents[:idx] + [code] + contents[idx:]

            evil += '\n'.join(contents) 
    evil += ')'
    with open('temp.wat', 'w') as f:
        f.write(evil)

    if os.system(f"eosio-wast2wasm temp.wat -o temp.wasm") != 0:
        raise Exception("eosio-wast2wasm Error")


reduceCoverage("/tmp/tokenlock.wasm", {'apply': 30, 'transfer':31})
