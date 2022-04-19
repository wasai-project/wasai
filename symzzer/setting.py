import os
import logging 
import symzzer.utils

'''
switching mode:
0 : flat test      . hightlight the analysis of log
1 : multi test     . hightlight the queue
2 : evolution test . hightlight the direct-copy processing
3 : full test      . ultra version
'''
mode = 0


# =======================

# ===== vul detection mode =======
detectVul = False
isChkOOB  = False
isFakeEos = True
isFakeNot = True
isChkPems = True
isRollback = True
isBlockinfoDep = True

solverTimeout = 3000# 3s
maxPeriod = 20#501#100#200
maxActionLoop = 16

timeoutSeconds = 300 #2 min
fuzzCount = 4
roundCount = 1
useAccountPool = False

isProxy = False
eosFilePath = os.getenv('HOME') + '/.local/share/eosio/'
logPath = os.getenv('HOME') + '/LOGS/'



contractName = ''
pathHookContract = './.rt/'



pathBaseContract = "/devdata/cwmdata/symzzerDataset/cleanet/"

# ======================= LAVA =============================
lavaPath = "/devdata/cwmdata/symzzerDataset/logs/"

cleosExecutable = 'cleos'
nodeosExecutable = 'nodeos'


eosioTokenContract = '/home/szh/eosio.contracts/contracts/eosio.token/'
atkforgContract = './agents/tokenlock'
atknotiContract = './agents/atknoti'

atkreroContract = './agents/atkrero'

atkforgContractSource = './agents/atkforg/atkforg.cpp'
atkforgContractBinary = './agents/atkforg/atkforg.wasm'


forgedNotificationAgentName = "atkforg"
forgedNotificationTokenFromName = "pokpokpokpok"#"atkforgfrom"#


fakeTransferAgentName = "fake.token"
fakeTransferUserName = 'fakeosio'
testEOSTokenFromName = "testeosfrom"


eosioTokenPublicKey = 'EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV' 
aPublicKey =          'EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV'
aPasswordToKeosd = 'PW5JJCpLY8BpYsHVYqRMn216Q1KLYSYvfsdNqDm2GGduzsu8XPaiL'

# setting logging module
loggerfile= '/home/szh/dynamicAnalyze/EOSFuzzer/symzzer/logger.log'
os.system(f'rm {loggerfile}')

globalDebug = False
logging.basicConfig(level = logging.DEBUG if globalDebug else logging.INFO ,
                    format = '%(name)s - %(levelname)s - %(message)s',
                    filename=loggerfile)
logger = logging.getLogger()

bugSet = list()
timePoints = list()

'''
– Changes to state in the EOS persistent storage
    db_*
– Notiﬁcations to the recipients of the current transaction
    require_recipient 
– Inline action requests to send to a new receiver
    inline_send
– Generation of new (deferred) transactions
    send_defer
– Cancellation of existing (in-ﬂight) deferred transactions (i.e. cancel already-submitted deferred transaction requests)
    cancel_defer

内存信息不会打包到block，属于runtime的内容，所以mem*无所谓

send_inline 142
send_deferred 11
send_context_free_inline 1
cancel_deferred 6
require_auth 397
require_auth2 54
require_recipient 86
db_find_i64 684
db_get_i64 528
db_update_i64 385
db_store_i64 279
db_lowerbound_i64 213
db_next_i64 178
db_remove_i64 119
db_idx64_find_primary 75
db_idx64_store 41
db_idx64_update 41
db_previous_i64 40
db_idx64_remove 27
db_idx128_find_primary 26
db_end_i64 20
db_idx128_update 13
db_idx64_lowerbound 9
db_idx128_store 8
db_idx128_lowerbound 7
db_idx128_remove 6
db_idx128_next 5
db_idx64_next 5
db_idx128_previous 4
db_idx64_previous 4
db_idx64_upperbound 2
db_idx128_end 2
db_idx64_end 2
db_idx256_find_primary 1
db_idx256_remove 1
db_idx256_store 1
'''

SIDE_EFFECTS = ['send_inline', 'send_deferred', 'send_context_free_inline', 'cancel_deferred', 
                'db_find_i64', 'db_lowerbound_i64', 'db_get_i64',
                'db_update_i64', 'db_store_i64', 'db_remove_i64', 'db_idx64_store', 'db_idx64_update', 'db_idx64_remove', 'db_idx128_update',
                'db_idx128_store', 'db_idx128_remove', 'db_idx256_remove', 'db_idx256_store']
# 'db_find_i64', 'db_lowerbound_i64', 'db_get_i64',
