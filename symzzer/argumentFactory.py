"""
Author: Weimin Chen
Time  : 10/21/2020
Ref   : A Python implement of https://github.com/gongbell/EOSFuzzer/blob/master/eos/programs/fuzzer/type.hpp
"""
import json
import random
import re
import string
import os
import subprocess

import symzzer.setting as setting

class ABIObj(object):
    """Parse ABI file
    Args:
        path: the path of ABI file
    Attributes:
        abiJson: the serialized object of ABI file
        actions: a list recoreds all fields of actions
        types  : a list recoreds all new types
        structs: a list recoreds all struct fields
    """
    def __init__(self, path):
        self.fpath = path
        try:
            with open(path, 'r') as f:
                print(path)
                self.abiJson = json.load(f)
        except:
            raise RuntimeError("ABI Error")
        
        self.structs = self.abiJson['structs']
        self.types   = self.abiJson['types']
        self.actions = self.abiJson['actions']
        self.actionNames = [_action['name'] for _action in self.actions]
        self.prioActNames = [item for item in self.actionNames if 'init' in item or 'set' in item]


class ArgumentFactory(object):
    """A factory parsing action and generating a test input.
    Args:
        contractName: the name of target contract
        abiData     : a abi object

    Attributes:
        contractName: the name of target contract
        abiData     : a abi object
        testArgument: a test string which can be recognized by cleos

    """
    def __init__(self, _abiData, _targetCN):
        # waiting for fuzzing
        self.fuzzingTarget = _targetCN
        self.abi = _abiData

        # cleos push action [executedContractName] [function] [argruments] -p [activeAccount]@active
        self.executedContractName = '' # directly operate
        self.functionName = ':ALL' 
        self.testArgument = ""
        self.activeAccount = '' # the activator

        self.testArgumentType = list()


        # const data
        self.forgedNotificationAgentName = setting.forgedNotificationAgentName
        self.forgedNotificationTokenFromName = setting.forgedNotificationTokenFromName# active

        self.testEOSTokenFromName = setting.testEOSTokenFromName           # An account invoke xxx.transfer

        self.fakeTransferAgentName = setting.fakeTransferAgentName # A fake eosio.token
        self.fakeTransferUserName = setting.fakeTransferUserName               # An account invoke fake.token.transfer


    def clear(self):
        """reset
        Args:
            None
        Returns:
            None
        """
        self.testArgument = ""


    def getActionType(self, actionName):
        """Return an action's type.
        Args:
            actionName: the name of action

        Returns:
            The type
        """
        for action in self.abi.actions:
            if action['name'] == actionName:
                return action['type']
        return ""
    
    def getStructDetail(self, structName):
        """Return the detail of struct.
        Args:
            structName: the name of struct

        Returns:
            The detail
        """
        # just a typedef
        for typeDetail in self.abi.types:
            if typeDetail['new_type_name'] == structName:
                return self.getStructDetail(typeDetail['type'])
            
        for structDetail in self.abi.structs:
            if structDetail['name'] == structName:
                return structDetail
        
        # if nothing found
        return {'name':'~', 'base':structName, 'fields':[]}

    def chooseFunc(self):
        return random.choice(self.abi.actionNames) # deponding on db function

    def generateNewData(self, _funcName, kind):
        """Return a data string for an action.
        Args:
            functionName: the name of the action
            kind: the kind of test
        Returns:
            The data.
        """
        self.clear()

        # choose seeds from symbolic feedback
        if kind == 0:
            # normal test
            self.executedContractName = self.fuzzingTarget
            if _funcName == ":ALL":
                self.functionName = self.chooseFunc()
            else:
                self.functionName = _funcName
            self.activeAccount = self.fuzzingTarget
            self.generateData(self.getStructDetail(self.getActionType(self.functionName)))

        elif kind == 1:
            # fake notification
            # trick here, using memo as a contractName
            # eosio.token transfer [atkforgfrom, forgAgentName, 100 EOS, xxx] -p atkforgfrom@active
            self.executedContractName = "eosio.token"
            self.functionName = "transfer"
            self.activeAccount = self.forgedNotificationTokenFromName
            self.testArgument = f'{{"from":"{self.forgedNotificationTokenFromName}", ' + \
                                f'"to":"{self.forgedNotificationAgentName}", ' + \
                                f'"quantity":{self.generateDataForSimpleType("asset")}, ' + \
                                f'"memo":{self.generateDataForSimpleType("string")}}}'
                                
        elif kind == 2:
            # fake eos@1 using fake.token
            # fake.token transfer [fakeosio, xxxx, 100 EOS, memo] fakeosio@active
            self.executedContractName = self.fakeTransferAgentName
            self.functionName = "transfer"
            self.activeAccount = self.fakeTransferUserName #fakeosio
            self.testArgument = f'{{"from":"{self.fakeTransferUserName}", ' + \
                                f'"to":"{self.fuzzingTarget}", ' + \
                                f'"quantity":{self.generateDataForSimpleType("asset")}, ' + \
                                f'"memo":{self.generateDataForSimpleType("string")}}}'
        
        elif kind == 3:
            # fake eos@2

            # xxx tansfer [testeosfrom, xxx, 100 EOS, memo] -p testeosfrom@active
            self.executedContractName = self.fuzzingTarget
            self.functionName = "transfer"
            self.activeAccount = self.testEOSTokenFromName #testEosfrom
            self.testArgument = f'{{"from":"{self.testEOSTokenFromName}", ' + \
                                f'"to":"{self.fuzzingTarget}", ' + \
                                f'"quantity":{self.generateDataForSimpleType("asset")}, ' + \
                                f'"memo":{self.generateDataForSimpleType("string")}}}'
            # self.generateData(self.getStructDetail(self.getActionType('transfer')))
        elif kind ==4 :
            # transfer Valid EOS
            # tapos test. transfer real EOS to xxx
            self.executedContractName = "eosio.token"
            self.functionName = "transfer"
            self.activeAccount = self.testEOSTokenFromName
            self.testArgument = f'{{"from":"{self.activeAccount}", ' + \
                                f'"to":"{self.fuzzingTarget}", ' + \
                                f'"quantity":{self.generateDataForSimpleType("asset")}, ' + \
                                f'"memo":{self.generateDataForSimpleType("string")}}}'
        else:
            raise RuntimeError(f"Invalid kind={kind}")

    
    def generateNewDataType(self, _funcName):
        self.testArgumentType = self.generateDataType(self.getStructDetail(self.getActionType(_funcName)))


    def generateDataType(self, structDetail):
        """Return a dict for cleos argument.
        Args:
            structName: the name of the struct
            isBase: whether the struct is a base class
        Returns:
            A dictory.
        """
        if structDetail['name'] == "~": 
            return structDetail['base']
        typeDict = list()
        for fieldDetail in structDetail['fields']:
            typeDict.append(self.generateDataType(self.getStructDetail(fieldDetail['type'])))
        return typeDict


    def generateData(self, structDetail, isBase=False):
        """Return a data string of a struct.
        Args:
            structName: the name of the struct
            isBase: whether the struct is a base class
        Returns:
            The data.
        """
        if structDetail['name'] == "~": 
            self.testArgument += self.generateDataForSimpleType(structDetail['base'])
            return

        if not isBase:
            self.testArgument += "{"
        if structDetail['base'] != "" :
            self.generateData(self.getStructDetail(structDetail['base']), True)
            self.testArgument += ", "
        fieldsSize = len(structDetail['fields'])
        for i in range(fieldsSize):
            fieldDetail = structDetail['fields'][i]
            self.testArgument += str("\"" + fieldDetail['name'] + "\": ")

            # optional arguments
            if fieldDetail['type'].endswith('?'):
                elementTypename =  fieldDetail['type'][:-1]
                if random.randint(0, 1):
                    self.generateData(self.getStructDetail(elementTypename))
                else:
                    return "null" #TODO

            # array-like arguments
            elif fieldDetail['type'].endswith('[]'):
                arrayLength = random.randint(1, 4)
                self.testArgument += "["
                elementTypename =  fieldDetail['type'][:-2]
                elementStructDetail = self.getStructDetail(elementTypename)
                for j in range(arrayLength):
                    self.generateData(elementStructDetail)
                    if j < arrayLength - 1:
                        self.testArgument += ", "
            
                self.testArgument += "]"
            else:
                self.generateData(self.getStructDetail(fieldDetail['type']))

            if i < fieldsSize - 1:
                self.testArgument += ", "
        
        if not isBase:
            self.testArgument += "}"
    
    def generateDataForSimpleType(self, structName):
        # ref: libraries/chain/abi_serializer.cpp: abi_serializer::configure_built_in_types()
        """generatinh ramdon value for simple arguments
        Args:
            structName: the name of the type

        Returns:
            The data
        """
        
        intRes = re.match('^(int|uint)(8|16|32|64|128)$', structName)
        floatRes = re.match('^float(32|64|128)$', structName)
        if intRes:
            prexType = intRes.group(1)
            bitNum = int(intRes.group(2))
            if prexType.startswith('u'):
                return f"{random.randint(0, 256)}"
            else:
                return f"{random.randint(-128,127)}"
            

        elif floatRes:
            bitNum = int(floatRes.group(1))
            return f"{random.randint(0, 100)}.{('%.4f' % random.random())[2:]}"


        elif structName in ['varint32', 'varuint32']:
            return f"{random.randint(1, 10)}"

        elif structName == 'bool':
            return 'true' if random.randint(0,1) else 'false'

        elif structName == 'string':
            randLen = random.randint(3, 8)
            return '\"'+''.join(random.sample(string.ascii_letters, randLen)) + '\"'

        elif structName == "asset":
            assetValue = random.randint(1, 1000000)
            firstString = str(int(assetValue // 10000))
            secondString =  "%04d" % (assetValue % 10000)
            return "\"" + firstString + '.' + secondString + " EOS\""

        elif structName == "extended_asset":
            assetValue = random.randint(1, 100000000)
            firstString = str(int(assetValue // 10000))
            secondString =  "%04d" % (assetValue % 10000)
            return f'{{"quantity":"{firstString}.{secondString} EOS","contract":"{self.fuzzingTarget}"}}'
        

        elif structName == "symbol": 
            return f"\"4,EOS\""
        
        elif structName == "symbol_code": 
            return f"\"EOS\""

        elif structName == "name":
            return f'\"{self.activeAccount}\"'#nameRtVal
            # std::string nameReturnValue;
            # if(dataRange == random || !pSetting || pSetting->accountList.size() == 0) nameReturnValue = activeAccount; 
            # else {
            #     int accountPosition = randomInt(0UL, pSetting->accountList.size() - 1);
            #     nameReturnValue =  pSetting->accountList[accountPosition].first;
            # }
            # if(randomInt(0, 1)) realActiveAccount = nameReturnValue;
            # return nameReturnValue;
        
        elif structName == "public_key":
            return f'\"{setting.eosioTokenPublicKey}\"'
            # if(dataRange == random || !pSetting || pSetting->accountList.size() == 0) return "EOS7jxeJjHurnzUnkhCQVk9Sr9SiuJAQC5xTZGxCbrk6u9ywsV4Bv"; 
            # else {
            #     int accountPosition = randomInt(0UL, pSetting->accountList.size() - 1);
            #     return pSetting->accountList[accountPosition].second;
            # }
        elif structName == "private_key":
            return '"PVT_R1_PtoxLPzJZURZmPS4e26pjBiAn41mkkLPrET5qHnwDvbvqFEL6"'

        elif structName == 'signature':
            return "\"SIG_K1_K3dztmFctY8QPgD6BEnxaV4s1gxyfHPZYTqHx8gH9Hiq2MLvn8Uc4ki6w7C89GVXAQ5JFM37BERe5qJSVHAqSkD8AabtKR\""
        
        elif structName == "time_point_sec":
            return '"2021-01-01T00:00:00.000"'
        elif structName == "time_point":
            return '"2021-01-01T00:00:00.000"'
        elif structName == "block_timestamp_type":
            return '"2021-01-01T00:00:00.000"'
        elif structName == "bytes":
            return '"AABBCCDDEEFF00010203040506070809"'
        elif structName == "checksum160":
            return '"123456789ABCDEF01234567890ABCDEF70123456"'
        elif structName == "checksum256":
            return '"0000000000000000000000000000000000000000000000000000000000000000"'
        elif structName == "checksum512":
            return  '"0987654321ABCDEF0987654321FFFF1234567890ABCDEF001234567890ABCDEF0987654321ABCDEF0987654321FFFF1234567890ABCDEF001234567890ABCDEF"'
        else:
            return "{}"
def test():
    contractName = 'hello'
    abi = ABIObj(f'/home/szh/contracts/{contractName}/{contractName}.abi')
    testData = ArgumentFactory(contractName, abi)
    for action in abi.actions:
        testData.generateNewData(action['name'], 3)
        print(testData.testArgument)
        