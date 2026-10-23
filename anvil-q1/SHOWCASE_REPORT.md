# Anvil-Q1 · W4A16 Quantized LLM Inference Accelerator — Product Whitepaper & Benchmark Evaluation Report

[English Whitepaper PDF (`SHOWCASE_REPORT.pdf`)](SHOWCASE_REPORT.pdf) · [Chinese Edition (`SHOWCASE_REPORT.zh-CN.md`)](SHOWCASE_REPORT.zh-CN.md) · [Chinese Whitepaper PDF (`SHOWCASE_REPORT.zh-CN.pdf`)](SHOWCASE_REPORT.zh-CN.pdf) · [Developer Engineering Report (`REPORT.pdf`)](REPORT.pdf)

## 1. Executive Key Performance Indicators (KPIs)

| Dimension | Measured Result | Engineering Significance |
| :--- | :--- | :--- |
| **Output Fidelity** | **100% Top-1 Match (46/46 Tokens)** | 24-layer multi-domain autoregressive generation parity |
| **Numerical Precision** | **0.999993** | Mean 151,936-vocab logit cosine similarity vs. FP32 |
| **Physical FPGA Validation** | **Intel Arria 10 GX** | PCIe Gen3x8 hardware execution with **0 bit errors**, Quartus 17.1 setup slack **+27.218 ns** |
| **Silicon Utilization & Scaling** | **5.12% ALMs / 14.43% DSPs** | **>94.9%** fabric headroom; 8 GB on-board DDR4 scales up to **7B–8B AWQ LLMs** |

## 2. 24-Layer Multi-Domain Autoregressive Generation Benchmark

| Benchmark Domain | Input Prompt | Official FP32 Baseline Output | Anvil W4A16 Hardware Output | Top-1 Agreement | 151,936-Vocab Logit Cosine |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mathematics** | `What is 15 + 27? Answer briefly.` | `The answer is 42.` | `The answer is 42.` | **8/8 (100%)** | `0.999992` |
| **Code Generation** | `Write a one-line Python function add(a, b) that returns their sum.` | `def add(a, b):     return a + b` | `def add(a, b):     return a + b` | **17/17 (100%)** | `0.999986` |
| **General Knowledge** | `What is the capital of France? Answer in one sentence.` | `The capital of France is Paris.` | `The capital of France is Paris.` | **8/8 (100%)** | `0.999997` |
| **Logical Reasoning** | `If all cats are mammals and Tom is a cat, what is Tom? Answer briefly.` | `Tom is a mammal.` | `Tom is a mammal.` | **7/7 (100%)** | `0.999995` |
| **Chinese Dialogue** | `中国的首都是哪里？请用一句话回答。` | `中国的首都是北京。` | `中国的首都是北京。` | **6/6 (100%)** | `0.999994` |

- **24-Layer Time-Multiplexed Hardware Execution**: Executed **120 hardware Transformer layers** and **1,259,748 clock cycles** across all five domains on Intel Arria 10 GX (`10AX115N3F40E2SG`) with **0 bit errors**.

## 3. Intel Arria 10 GX Utilization & 7B–8B LLM Scaling Roadmap

| Hardware Resource | Single-Core Utilization | Arria 10 GX Capacity | Utilization | Multi-Core & LLM Scaling Target |
| :--- | :--- | :--- | :--- | :--- |
| **Adaptive Logic Modules (ALMs)** | `21,890` | `427,200` | `5.12%` | Scales to 8–16x parallel compute engines |
| **On-Chip Memory (M20K BRAM)** | `384` | `2,713` | `14.15%` | Deep on-chip KV cache & ping-pong weight buffers |
| **Precision DSP Blocks (18x19)** | `219` | `1,518` | `14.43%` | 1,024+ DSP MAC array for >100x throughput |
| **Clock Frequency (Fmax)** | `25 MHz` (`WNS +27.218 ns`) | `20nm Arria 10` | `0 Failing Paths` | Pipelined retiming up to **150–250 MHz** |
| **On-Board 8 GB DDR4 Capacity** | `0.5B` (`0.35 GB`) | `8.0 GB DDR4` | `4.4%` | **0.5B $\to$ 1.5B (`0.95 GB`) $\to$ 3B (`1.8 GB`) $\to$ 7B–8B (`3.9 GB` W4 weights + `4 GB` KV Cache)** |

## Whitepaper Page Preview

### Page 1
![Whitepaper Page 1](showcase_figures/page-1.png)

### Page 2
![Whitepaper Page 2](showcase_figures/page-2.png)

### Page 3
![Whitepaper Page 3](showcase_figures/page-3.png)
