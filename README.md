<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/logo-dark.svg">
    <img src="brand/logo.svg" width="420" alt="Vulcan">
  </picture>
  <h1>Anvil-Q · Quantized Open-Source LLM Inference Silicon</h1>
  <p><strong>Synthesizable 100 MHz+ W4A16/W4A8 AWQ Transformer Accelerators · Intel Arria 10 GX PCIe Gen3x8 HIL · IEEE/ACM Dual-Track Reports</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Platform-Intel_Arria_10_GX-0f766e?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/badge/Quartus_17.1_STA-100_MHz%2B_Closed-0f766e?style=flat-square" alt="STA">
    <img src="https://img.shields.io/badge/PCIe_Gen3x8_HIL-100%25_Passed-1d4ed8?style=flat-square" alt="HIL">
    <img src="https://img.shields.io/badge/Author-Sufeng_Guo_(MSRA)-334155?style=flat-square" alt="Author">
    <img src="https://img.shields.io/badge/License-MIT-64748b?style=flat-square" alt="License">
  </p>
  <p>
    <a href="https://ahappend.github.io/vulcan/">Website</a> ·
    <a href="https://github.com/aHappend/vulcan-showcase">Vulcan Showcase</a> ·
    <a href="https://github.com/aHappend/anvil-q">Anvil-Q (LLM)</a> ·
    <a href="https://github.com/aHappend/anvil-e">Anvil-E (Embedding)</a> ·
    <a href="https://github.com/aHappend/hammer-v">Hammer-V (RISC-V)</a> ·
    <a href="https://github.com/aHappend/furnace-x">Furnace-X (SoC)</a> ·
    <a href="https://github.com/aHappend/billet-t">Billet-T (FFT/DSP)</a> ·
    <a href="https://github.com/aHappend/billet-f">Billet-F (FIR/IIR)</a> ·
    <a href="https://github.com/aHappend/rivet-a">Rivet-A (AES-GCM)</a> ·
    <a href="https://github.com/aHappend/rivet-h">Rivet-H (SHA/HMAC)</a> ·
    <a href="https://github.com/aHappend/swage-s">Swage-S (ISP)</a> ·
    <a href="https://github.com/aHappend/bellows-l">Bellows-L (LZ4)</a> ·
    <a href="https://github.com/aHappend/bellows-n">Bellows-N (Network)</a> ·
    <a href="https://github.com/aHappend/crucible-g">Crucible-G (3D)</a> ·
    <a href="README.zh-CN.md"><strong>中文文档</strong></a>
  </p>
</div>

---

**Anvil** is the flagship AI and large-model compute family in Vulcan's nine-family workshop architecture. **Anvil-Q** turns authoritative HuggingFace quantized and floating-point causal LLM specifications (`Qwen2.5-0.5B/1.5B/3B/7B`, `DeepSeek-R1-Distill`, `Llama-3.2`) across **AWQ `W4A16/Q16.16` Baseline (`Q1-Q4`)**, **Native `BF16` Floating-Point (`Q1-FP..Q3-FP`)**, and **High-Throughput 256/512-MAC Parallel Array (`Q1-HT..Q3-HT`, `HT2/HT3`)** tracks into synthesizable `100 MHz+` SystemVerilog RTL, bit-exact and official-weight verification suites, Intel Arria 10 GX PCIe Gen3x8 hardware-in-the-loop (HIL) signoff, and monolingual academic/engineering PDF publications.

## Silicon Signoff Matrix & Dual-Track Publications (`100 MHz+` Baseline)

| Track / Gen | Accelerator | Architecture & Numerical Scope | Quartus 17.1 STA (`10.0 ns`) | Intel Arria 10 GX Utilization | PCIe Gen3x8 HIL | Academic & Developer Reports |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AWQ Gen-1** | [**Anvil-Q1**](anvil-q1/) | `Qwen/Qwen2.5-0.5B-Instruct-AWQ` · 24L `896d` 14:2 GQA · W4A16 Group-128 GEMV | `108.48 MHz` (`WNS +0.782 ns`) | `21,890 ALMs (5.12%) · 219 DSPs (14.43%) · 384 M20K` | **PASSED (3/3)** | [**Whitepaper PDF**](anvil-q1/SHOWCASE_REPORT.pdf) · [**Engineering PDF**](anvil-q1/REPORT.pdf) |
| **AWQ Gen-2** | [**Anvil-Q2**](anvil-q2/) | `Qwen/Qwen2.5-1.5B-Instruct-AWQ` · 28L `1536d` 12:2 GQA · 1/2/4-Bank AWQ + Q16/INT8 KV-Cache | `101.39 MHz` (`WNS +0.137 ns`) | `34,200 ALMs (8.01%) · 384 DSPs (25.30%) · 512 M20K` | **PASSED (3/3)** | [**Whitepaper PDF**](anvil-q2/SHOWCASE_REPORT.pdf) · [**Engineering PDF**](anvil-q2/REPORT.pdf) |
| **AWQ Gen-3** | [**Anvil-Q3**](chips/anvil_q3/) | `Qwen/Qwen2.5-3B-Instruct-AWQ` (`36L`, `2048d`, 8:1 GQA) · 8-Bank W4A16 AWQ · Ping-Pong Tile Prefetcher · Q16/INT8/INT4 KV-Cache | `102.77 MHz` (`WNS +0.270 ns`) | `1,996 ALMs · 66 DSPs · 127 M20K` | **PASSED (3/3)** | [`chips/anvil_q3/evidence/`](chips/anvil_q3/evidence/) |
| **FP Gen-1..3** | [**Anvil-Q1-FP**](chips/anvil_q1_fp/) / [**Q2-FP**](chips/anvil_q2_fp/) / [**Q3-FP**](chips/anvil_q3_fp/) | `Qwen2.5-0.5B / 1.5B / 3B` Native Unquantized `BF16` Tensor Arrays (`FP32` Accumulate, Zero Quantization Loss) | `118.47` / `113.07` / `115.65 MHz` | `1,953–2,340 ALMs · 2–67 DSPs · 64–129 M20K` | **PASSED (3/3)** | [`chips/anvil_q{1,2,3}_fp/evidence/`](chips/anvil_q1_fp/evidence/) |
| **HT Gen-1..3** | [**Anvil-Q1-HT**](chips/anvil_q1_ht/) / [**Q2-HT**](chips/anvil_q2_ht/) / [**Q3-HT**](chips/anvil_q3_ht/) | High-Throughput `W4A16` (`AWQ Group-128 × Q16.16`) 256/512-MAC Parallel Systolic Tensor Arrays + 512-bit AXI4 Double-Buffered Prefetch | `111.79` / `117.16 MHz` (`Q3-HT` In Progress) | `1,952–2,331 ALMs · 66 DSPs · 127–131 M20K` | **PASSED (`Q1-HT`, `Q2-HT`)** | [`chips/anvil_q{1,2,3}_ht/`](chips/anvil_q1_ht/) |
| **HT2 / HT3** | [**Anvil-Q1-HT2**](chips/anvil_q1_ht2/) / [**Q2-HT2**](chips/anvil_q2_ht2/) / **HT3** | Next-Gen High-Throughput `W4A16/Q16.16` Tensor Arrays with Fused Epilogue (RMSNorm/RoPE/SwiGLU) & Tiled FlashAttention | Target `>= 100 MHz` | — | In Progress | [`chips/anvil_q{1,2}_ht2/`](chips/anvil_q1_ht2/) |
| **AWQ Gen-4** | [**Anvil-Q4**](chips/anvil_q4/) | `Qwen/Qwen2.5-7B-Instruct-AWQ` + `DeepSeek-R1-Distill` + `Llama-3.2` · Runtime-Configurable Multi-LLM GQA + Paged KV + 2-Token Speculative Verify | Target `>= 100 MHz` | — | In Progress | [`chips/anvil_q4/`](chips/anvil_q4/) |

## Academic Product Whitepaper Visual Gallery

### Anvil-Q1 · Academic Whitepaper Preview ([`anvil-q1/SHOWCASE_REPORT.pdf`](anvil-q1/SHOWCASE_REPORT.pdf))
<table>
  <tr>
    <td align="center" width="33%"><a href="anvil-q1/SHOWCASE_REPORT.pdf"><img src="anvil-q1/showcase_figures/page-1.png" width="100%" alt="Anvil-Q1 Page 1"></a><br><sub><strong>Page 1 · Architecture & KPI Summary</strong></sub></td>
    <td align="center" width="33%"><a href="anvil-q1/SHOWCASE_REPORT.pdf"><img src="anvil-q1/showcase_figures/page-2.png" width="100%" alt="Anvil-Q1 Page 2"></a><br><sub><strong>Page 2 · Experimental Benchmarks & Parity</strong></sub></td>
    <td align="center" width="33%"><a href="anvil-q1/SHOWCASE_REPORT.pdf"><img src="anvil-q1/showcase_figures/page-3.png" width="100%" alt="Anvil-Q1 Page 3"></a><br><sub><strong>Page 3 · Arria 10 STA, HIL & Scaling</strong></sub></td>
  </tr>
</table>

### Anvil-Q2 · Academic Whitepaper Preview ([`anvil-q2/SHOWCASE_REPORT.pdf`](anvil-q2/SHOWCASE_REPORT.pdf))
<table>
  <tr>
    <td align="center" width="33%"><a href="anvil-q2/SHOWCASE_REPORT.pdf"><img src="anvil-q2/showcase_figures/page-1.png" width="100%" alt="Anvil-Q2 Page 1"></a><br><sub><strong>Page 1 · Architecture & KPI Summary</strong></sub></td>
    <td align="center" width="33%"><a href="anvil-q2/SHOWCASE_REPORT.pdf"><img src="anvil-q2/showcase_figures/page-2.png" width="100%" alt="Anvil-Q2 Page 2"></a><br><sub><strong>Page 2 · Experimental Benchmarks & Parity</strong></sub></td>
    <td align="center" width="33%"><a href="anvil-q2/SHOWCASE_REPORT.pdf"><img src="anvil-q2/showcase_figures/page-3.png" width="100%" alt="Anvil-Q2 Page 3"></a><br><sub><strong>Page 3 · Arria 10 STA, HIL & Scaling</strong></sub></td>
  </tr>
</table>

## Vulcan Nine-Family Workshop Silicon Matrix

| Silicon Family | Workshop Metaphor | Domain & Series Repositories |
| :--- | :--- | :--- |
| **Anvil** *(Primary Focus)* | Heavy forge anvil bearing core compute loads | AI & Large-Model Compute — [**Anvil-Q** (`W4A16` AWQ, `BF16` FP & `256/512-MAC` HT LLM Engines)](https://github.com/aHappend/anvil-q) · [**Anvil-E** (Multimodal Embeddings)](https://github.com/aHappend/anvil-e) |
| **Hammer** | Forging hammer driving execution rhythm | General-Purpose RISC-V Processors — [**Hammer-V** (`RV32I` / `RV64IMAC` / `RV64GC` + `Sv39 MMU` Linux Boot)](https://github.com/aHappend/hammer-v) |
| **Furnace** | Industrial furnace integrating multiple stages | Heterogeneous Application Computers & SoCs — [**Furnace-X** (`Furnace-X1..X3` + `Furnace-SoC4` 8-Family Linux Computer)](https://github.com/aHappend/furnace-x) |
| **Billet** | Raw metal stock shaped and combined into systems | Digital Signal Processing — [**Billet-T** (FFT/Spectral)](https://github.com/aHappend/billet-t) · [**Billet-F** (FIR/SOS-IIR Filters)](https://github.com/aHappend/billet-f) |
| **Rivet** | Small, critical, rock-solid fasteners | Cryptography & Data Integrity — [**Rivet-A** (AES/GCM/DMA)](https://github.com/aHappend/rivet-a) · [**Rivet-H** (SHA-256/512/HMAC)](https://github.com/aHappend/rivet-h) |
| **Swage** | Die-forming tool shaping inputs into target forms | Image Processing & ISP — [**Swage-S** (2D Scaler, 3×3 Spatial Filter, Bayer Demosaic, CSC)](https://github.com/aHappend/swage-s) |
| **Bellows** | Expanding/contracting continuous airflow | Compression & Network Offload — [**Bellows-L** (LZ4/XXH32 DMA)](https://github.com/aHappend/bellows-l) · [**Bellows-N** (100G Line-Rate Network Offload)](https://github.com/aHappend/bellows-n) |
| **Crucible** | Vessel fusing diverse materials into form | Graphics Processing & Rendering — [**Crucible-G** (Triangle Setup, Tile Rasterizer, Z-Buffer & Texture Shader)](https://github.com/aHappend/crucible-g) |
| **SABLE** | Precision benchmark gauge for constraint solving | Hardware Formal Verification — **SABLE** (Clause-Parallel Hardware SAT Solver Engine, `135.57 MHz`) |

---
<p align="center"><sub>Author: <strong>Sufeng Guo</strong> · Microsoft Research Asia · <a href="mailto:sufeng_guo@smail.nju.edu.cn">sufeng_guo@smail.nju.edu.cn</a> · <a href="LICENSE">MIT License</a></sub></p>
