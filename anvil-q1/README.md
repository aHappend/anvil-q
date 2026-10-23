# Anvil-Q1 · W4A16 Quantized LLM Inference Accelerator

[中文文档 (`README.zh-CN.md`)](README.zh-CN.md) · [Product Whitepaper PDF (`SHOWCASE_REPORT.pdf`)](SHOWCASE_REPORT.pdf) · [Developer Engineering Report PDF (`REPORT.pdf`)](REPORT.pdf)

## Overview

**Anvil-Q1** is a dedicated hardware accelerator autonomously architected, implemented, and verified by **Vulcan** for **Qwen/Qwen2.5-0.5B-Instruct-AWQ (24 Layers, 896D, 14Q:2KV GQA, 151,936 Vocab)** on the **Intel Arria 10 GX (10AX115N3F40E2SG) PCIe Gen3x8** platform.

| Metric | Measured Result | Summary |
| :--- | :--- | :--- |
| **Output Fidelity** | **100% Top-1 Match (382/382 Tokens)** | 24-layer 30-prompt multi-domain autoregressive parity (41,280 layer evals) |
| **Numerical Cosine Similarity** | **0.999992** | Mean 151,936-vocab logit cosine similarity vs. FP32 |
| **Quartus 17.1 STA Timing** | **Fmax = 108.48 MHz** | WNS = +0.782 ns at 100.0 MHz (10.0 ns) baseline, 0 failing endpoints |
| **Intel Arria 10 GX Utilization** | **5.12% ALMs / 14.43% DSPs** | 21,890 ALMs, 384 M20K BRAMs, 219 DSPs |
| **Physical PCIe Gen3x8 HIL** | **PASSED (3/3 runs)** | Deterministic hardware execution on Intel Arria 10 GX (`10AX115N3F40E2SG`) |

## Documentation Suite

| Document | Format | Description |
| :--- | :--- | :--- |
| **[Product Whitepaper (`SHOWCASE_REPORT.pdf`)](SHOWCASE_REPORT.pdf)** | PDF / [Markdown](SHOWCASE_REPORT.md) | Executive KPI summary, autonomous AI-to-Silicon pipeline, official-weight benchmark parity, and 7B–8B scaling roadmap |
| **[Developer Engineering Report (`REPORT.pdf`)](REPORT.pdf)** | PDF / [Markdown](REPORT.md) | Complete SystemVerilog RTL microarchitecture, interface contracts, fixed-point bounds, Quartus STA, and PCIe BAR0 HIL register ledger |
| **[Engineering Journey (`.vulcan/engineering/JOURNEY.md`)](.vulcan/engineering/JOURNEY.md)** | Markdown | Full autonomous design, verification, and hardware signoff log |
