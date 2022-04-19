import os
import sys

'''
生成 traces， bugs
'''
def main():
    if sys.args < 2 or sys.args > 4:
        print('Usage: %s <path_to_benchmark> <savefile> [count]' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)

    base = sys.argv[1]
    targetDir = sys.argv[2]
    os.system(f'mkdir -p {targetDir} && rm -r {targetDir}/*')
    if sys.argv[3] != None:
        _cnt = int(sys.argv[3])
        contractsList = os.listdir(base)[:_cnt]
    else:
        contractsList = os.listdir(base)

    for contractDir in contractsList:
        abiPath = False
        wasmPath = False
        _dirBase = os.path.join(base, contractDir)
        for contractFile in os.listdir(_dirBase):
            if contractFile == contract + '.abi':
                abiPath = os.path.join(_dirBase, contractFile)
            if contractFile == contract + '.wasm':
                wasmPath = os.path.join(_dirBase, contractFile)
        
        if abiPath != False and wasmPath != False:
            fuzzTarget = './rt/'
            contractName = contractDir.split('_')[0].split('-')[0]
            cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 10 120 {target} --detect_vuls 0111 --inject'
            os.system(f'mv {fuzzTarget} {targetDir}/{contractName}')

    print(f'[+] files save in {targetDir}')

main()