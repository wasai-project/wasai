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
# python3.6.9
python3 -m venv ./
activate ./venv/bin/activate
python3 -m pip install -r requirements.txt
```

2.   run example

```bash
python -m bin.fuzz <wasmPath> <abiPath> <contractName> <timeout> <fuzzCnt> <saveResult>
```

The result should be like:

```

```

# Benchmark

`https://drive.google.com/file/d/1z1rd3o0o6zoYVNcKXpnHWqDLn4EwdcP-/view?usp=sharing` &&
`https://github.com/gongbell/EOSFuzzer/tree/master/dataset/binaryContracts`

# Authors

[Zihan Sun](https://github.com/Al0ha0e), [Weimin Chen](https://github.com/Kenun99)

# License

[License MIT](LICENSE)
