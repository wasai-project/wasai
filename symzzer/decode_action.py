import json
import struct
import binascii
import re

import symzzer.setting as setting

def decodeActionData(linepos=-2):
    # TODO decode one specific line
    setting.contractName = 'hello'
    pathABI  = setting.pathHookContract + setting.contractName + '/' + setting.contractName + '.abi'

    with open('/home/szh/action_data.txt', 'r') as f:
        lines = f.readlines()
        
        account, actionName, startMemAdr, data =  lines[linepos].strip().split(' ')
        startMemAdr = int(startMemAdr, 16)
        actionRawData = binascii.unhexlify(data)
        # print(actionRawData)
        # actionRawData = lines[-1].strip().decode('hex')

    with open(pathABI, 'r') as f:
        abiJson = json.load(f)

    # print( abiJson['structs'])
    actionArgTypes = list(filter(lambda action: action['name'] == actionName, abiJson['structs']))[0]["fields"]


    rts = []
    pos = 0
    for arg in actionArgTypes:
        argType = arg['type']
        argName = arg['name']
        # print(f'pos=', pos)
        startPos = pos
        
        # uint/int 8/16/32/64/128
        
        # floatRes = re.match('^float(32|64|128)$', argType)
        if argType.startswith('int') or argType.startswith('uint'):
            intRes = re.match('^(int|uint)(8|16|32|64|128)$', argType)
            prex, bitLen = intRes.group(1), int(intRes.group(2))
            if bitLen == 128:
                pass
            else:
                lenMap = {8:'b', 16:'h', 32:'i', 64:'q'}
                sym = lenMap[bitLen].upper() if prex == 'uint' else lenMap[bitLen]
                byteLen = bitLen//8
                # print(sym, byteLen, argType)
                data = struct.unpack(sym, actionRawData[pos:pos+ byteLen])
            pos += byteLen

        elif argType == 'bool':
            data = struct.unpack('?', actionRawData[pos:pos+1])
            pos += 1
        # elif floatRes:
        #     byteLen = intRes.group(1)//8
        #     data = struct.unpack(f'i', actionRawData[pos:pos+4])
        elif argType == 'string':
            # print('- string')
            # print(actionRawData[pos], type(actionRawData[pos]))
            slen = actionRawData[pos]
            pos += 1
            data = struct.unpack(f'{slen}s', actionRawData[pos:pos+slen])
            pos += slen
        # elif argType == 'int8':
        #     # print('- int')
        #     data = struct.unpack(f'c', actionRawData[pos:pos+1])
        #     pos += 1
        # elif argType == 'int32':
        #     # print('- int')
        #     data = struct.unpack(f'i', actionRawData[pos:pos+4])
        #     pos += 4
        elif argType == 'float32':
            # print('- int')
            data = struct.unpack(f'f', actionRawData[pos:pos+4])
            pos += 4
        elif argType == 'float64':
            # print('- int')
            data = struct.unpack(f'd', actionRawData[pos:pos+8])
            pos += 8

        elif argType == 'asset':
            # print('- asset')
            tokenLen = actionRawData[pos+8]
            data = struct.unpack(f'Q{tokenLen}s', actionRawData[pos:pos + 8 + tokenLen])
            pos += 16
        elif argType =='name':
            # print('- user')
            data = actionRawData[pos:pos + 8]
            pos += 8

        elif argType.startswith('checksum'):
            bitLen = int(re.match('^checksum(160|256|512)$', argType).group(1))
            pos += bitLen//8
        else:
            print('ERROR ', argType)
            raise(f'ERROR - No find type. exit')
        rts.append((argName, data, startMemAdr + startPos, startMemAdr + pos))

        print(argType, actionRawData[startPos:pos])
    return rts

rts = decodeActionData(-5)
for argName, data, begAdr, endAdr in rts:
    print(f'[-] {argName} :{hex(begAdr)}-{hex(endAdr)}@{data}') # output bytes 

