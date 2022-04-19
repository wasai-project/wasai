import os
import sys
import json
import time


'''
测试公网数据 /devdata/cwmdata/symzzerDataset/cleanet
'''
def run():
    _begSt = time.time()

    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print('Usage: %s <path_to_benchmark> <savefile> [count]' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)

    base = sys.argv[1]
    targetDir = sys.argv[2]

    # if os.path.exists(targetDir) and len(os.listdir(targetDir)) > 0:
    #     _c = input(f"Do your want to remove {targetDir}? Y/n")
    #     if _c != 'Y':
    #         print("Do nothing, leave.")
    #         return

    if len(sys.argv) == 4 and sys.argv[3] != None:
        _cnt = int(sys.argv[3])
        if _cnt == -1:
            contractsList = os.listdir(base)
        else:
             contractsList = os.listdir(base)[:_cnt]
    else:
        contractsList = os.listdir(base)
    
    os.system(f'mkdir -p {targetDir} && rm -r {targetDir}/*')

    # print(contractsList)
    # exit(0)
    # tmps = os.listdir("/devdata/cwmdata/symzzerDataset/rq2/res/vul_notif/")
    for contractDir in contractsList:
        # if contractDir != "zlkggamerobs":
        #     continue

        '''
        efxstakepool
        xxxsevensxxx
        '''

        abiPath = False
        wasmPath = False
        contractName = contractDir.split('_')[0].split('-')[0]
        _dirBase = os.path.join(base, contractDir)
        for contractFile in os.listdir(_dirBase):
            if contractFile.endswith('.abi'):
                abiPath = os.path.join(_dirBase, contractFile)
            if contractFile.endswith('.wasm'):
                wasmPath = os.path.join(_dirBase, contractFile)
        
        if abiPath != False and wasmPath != False:
            fuzzTarget = './rt/'
            '''
            setting.isChkOOB       = config['vuls'][0] 
            setting.isFakeEos      = config['vuls'][1] 
            setting.isFakeNot      = config['vuls'][2] 
            setting.isChkPems      = config['vuls'][3]
            setting.isRollback     = config['vuls'][4]
            setting.isBlockinfoDep = config['vuls'][5]
            '''
            # print(wasmPath, abiPath)

            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} NULL 500000 300 {fuzzTarget} --detect_vuls 200000 --nostdout' # OOB
            cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 30000 300 {fuzzTarget} --detect_vuls 002000' #FAKE NOTIF
            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 300 300 {fuzzTarget} --detect_vuls 020000 --nostdout'   #FAKE EOS
            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} -1 120 {fuzzTarget} --detect_vuls 011100 --inject --nostdout'   # 
            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 30000 300 {fuzzTarget} --detect_vuls 000200'   #PM
            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 500000000 300 {fuzzTarget} --detect_vuls 000000 --nostdout'   # coverage
            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 300 300 {fuzzTarget} --detect_vuls 000002'   # blockinfoDep
            # cmd = f'python -m bin.fuzz {wasmPath} {abiPath} {contractName} 300000  300 {fuzzTarget} --detect_vuls 000020'   # rollback

            os.system("rm ./rt/* -r")
            if os.system(cmd) == 0:
                os.system(f'mv {fuzzTarget} {targetDir}/{contractDir}')
                print(f"[+] Finish and Save in {targetDir}/{contractDir}")
            else:
                print(f"[+] An Error Occur for {fuzzTarget}")

    print(f'[+] files save in {targetDir}')
    
    print('[+] Finish Analysis with ', "%.2f" % (time.time() - _begSt), 's')
    print('[+] Avg Times ', "%.2f" % ((time.time() - _begSt)/len(contractsList)), 's')

def analyze():
    if len(sys.argv) != 2:
        print('Usage: %s <savefile>' % \
               sys.argv[0], file=sys.stderr)
        exit(-1)
    targetDir = sys.argv[1]

    bugMap = {
        1:'fake notification',
        2:'fake eos',
        3:'OOB',
        6:'AuthMissing',
        7:'BlockinfoDep',
        8:'Rollback',
        -11:'guard notification'
    }
    result = dict()
    atk = 0
    print(f"[+] Scanned {len(os.listdir(targetDir))} contracts in total.")
    rbcnt = 0
    for contractDir in os.listdir(targetDir):
        if not os.path.exists(os.path.join(targetDir, contractDir, 'report.json')):
            # print(contractDir, '#')
            continue
        with open(os.path.join(targetDir, contractDir, 'report.json'), 'r') as f:
            _r = json.load(f)

        # if _r['lava_notif'] != []:
        #     atk += 1
        
   
    

        for bid in _r['bugs']:
            if bid == -11:
                if bid not in result:
                    result[bid] = [contractDir]
                else:
                    result[bid].append(contractDir)
            else:
                if bid not in result:
                    result[bid] = [contractDir]
                else:
                    result[bid].append(contractDir)
    if result:
        for key, val in result.items():
            print(f'[+] {bugMap[key]}: {len(val)} :\n', val, "\n")
            # print(f'- {bugMap[key]}: {len(val)} : {set(os.listdir(targetDir)) - set(val)}')
    else:
        print('- ALL Safe.')
    print(atk)


def main():
    if len(sys.argv) == 2:
        analyze()
    else:
        run()

main()
# run() 
# analyze()

