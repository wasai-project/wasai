# WASAI ![Status](https://img.shields.io/badge/Build-Fail-red)
<p align="center">
  <img src="https://github.com/ICSE2022-887/WASAI/blob/main/logo.png" width="60%" /><br/>
</p>
</p>

## ℹ️ Introductions 

WebAssembly (Wasm) smart contracts have shown growing popularity across blockchains (e.g., EOSIO) in recent years.  We propose WASAI, a concolic fuzzer for identifying vulnerabilities in Wasm smart contracts, taking EOSIO as the mainly Wasm favored blockchain. In particular, WASAI builds symbolic constraints along the execution traces of smart contracts and solves them to guide the fuzzing. 

The experimental results on code coverage demonstrate that WASAI obtains about 2x of that baselines gets. On the well-labelled benchmarks, WASAI outperforms all baselines in detecting vulnerabilities, with an F1-measure of 99.2\%. Moreover, WASAI is robust enough to remain 96.0\% F1-measure in analyzing the hard-to-detect benchmark. 

## ✳️ Features

- Concolic Fuzzer
- Effective symbolic execution
- Support Input Inference
- Parctical experiments

## 🍊 Architecture

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

## 💎 Getting Started

1.   set environment

```bash
# python3.6.9
python3 -m venv ./
activate ./venv/bin/activate
python3 -m pip install -r requirements.txt
```

2.   run

```bash
python -m bin.fuzz <wasmPath> <abiPath> <contractName> <timeout> <fuzzCnt> <saveResult>
```

3.   benchmark

     `https://drive.google.com/file/d/1z1rd3o0o6zoYVNcKXpnHWqDLn4EwdcP-/view?usp=sharing` &&
     `https://github.com/gongbell/EOSFuzzer/tree/master/dataset/binaryContracts`

## 🙆 Authors

Anonymous.

## 🌟 Contributors

Anonymous

## ©️ License

[License MIT](LICENSE)
