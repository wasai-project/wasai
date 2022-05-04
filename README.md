# WASAI

## Introduction

WebAssembly (Wasm) smart contracts have shown growing popularity across blockchains (e.g., EOSIO) in recent years.  We propose WASAI, a concolic fuzzer for identifying vulnerabilities in Wasm smart contracts, taking EOSIO as the mainly Wasm favored blockchain. In particular, WASAI builds symbolic constraints along the execution traces of smart contracts and solves them to guide the fuzzing.

## Architecture

```
|-- fuzz_benchmark.py               large scale analysis 
|—— bin                          
| |—— fuzz.py                       entry file
| |—— complicatedVerification.py    RQ3-1
| |—— reduceCov.py                  RQ3-2
|—— symzzer         
| |—— fuzzActions.py                main entry
| |—— argumentFactory.py            generate seeds
| |—— logAnalyzer.py                feedback
| |-- tainter
| | |-- analysis.py                 constratins generation
| | |-- wasabiHooker.py             engine hooks
| | |-- emulator.py                 symbolic execution engine
| | |-- memory.py                   memory model
| | |-- opcodes.py                  opcode table
| | |-- utils.py          
| |-- setting.py
| |-- utils.py
```
## Getting Started

1.   set environment

```bash
git clone https://github.com/wasai-project/wasai.git && cd wasai # download the code
sudo docker build -t localhost/client-eos:wasai .
sudo docker run --rm -ti  localhost/client-eos:wasai # run a docker container
```

2. run example

   Execute bin/fuzz.py to the result. `python -m bin.fuzz <wasmPath> <abiPath> <contractName> <timeout> <fuzzCnt> <saveResult>`

```bash
# in the docker container 
python3 -m bin.fuzz ./examples/batdappboomx/batdappboomx.wasm ./examples/batdappboomx/batdappboomx.abi batdappboomx 300 300  ./rt/ --detect_vuls 020000
```

WASAI should report a Fake EOS vulnerablity.

```
[+] Executed EOSPONSER# 68
- Checking Fakeos
[+] final report: {
    "name": "batdappboomx",
    "time": "5.45s",
    "bugs": [
        2
    ],
    "lava_eos": [],
    "lava_notif": [],
    "logLifes": []
}
```
# More Benchmark

```
https://drive.google.com/file/d/1z1rd3o0o6zoYVNcKXpnHWqDLn4EwdcP-/view?usp=sharing` &&
`https://github.com/gongbell/EOSFuzzer/tree/master/dataset/binaryContracts
```

# Authors

[Zihan Sun](https://github.com/Al0ha0e), [Weimin Chen](https://github.com/Kenun99)

# License

[License MIT](LICENSE)

