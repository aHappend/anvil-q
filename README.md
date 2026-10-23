<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/logo-dark.svg">
    <img src="brand/logo.svg" width="480" alt="Vulcan">
  </picture>
</p>

<h1 align="center">Anvil-Q · Quantized LLM silicon, forged anew.</h1>

<p align="center">
  Open W4A16 AWQ quantized language model accelerator RTL. Real engineering results.
  <br>
  <a href="https://ahappend.github.io/vulcan/">Visit the website</a>
  · <a href="https://github.com/aHappend/vulcan-showcase">Vulcan Showcase</a>
  · <a href="README.zh-CN.md">中文</a>
  · <a href="anvil-q1/">Anvil-Q1 package</a> · <a href="anvil-q1/SHOWCASE_REPORT.pdf">Anvil-Q1 Whitepaper (PDF)</a> · <a href="anvil-q1/REPORT.pdf">Anvil-Q1 Engineering Report (PDF)</a>
  · <a href="anvil-q2/">Anvil-Q2 package</a> · <a href="anvil-q2/SHOWCASE_REPORT.pdf">Anvil-Q2 Whitepaper (PDF)</a> · <a href="anvil-q2/REPORT.pdf">Anvil-Q2 Engineering Report (PDF)</a>
  · <a href="brand/">Brand assets</a>
</p>

**Anvil** is our flagship AI and large-model compute silicon family developed with **Vulcan 0.8**. **Anvil-Q**
is the dedicated **quantized causal LLM inference series** within the family, turning authoritative
HuggingFace AWQ mixed-precision model specifications into synthesizable `100 MHz+` SystemVerilog RTL,
self-checking verification suites, physical Intel Arria 10 GX PCIe Gen3x8 hardware-in-the-loop (HIL) validation, and IEEE/ACM-grade dual-track publication packages.

## Product Whitepapers & Developer Engineering Reports

For every verified accelerator in the series, **Vulcan** publishes a strictly monolingual, academic-paper-grade dual-track documentation suite:

| Accelerator | Academic Product Whitepaper | Developer Engineering Signoff Report | Intel Arria 10 GX (`10AX115N3F40E2SG`) Silicon Signoff |
| --- | --- | --- | --- |
| **Anvil-Q1** (`Qwen2.5-0.5B-AWQ`) | [**`SHOWCASE_REPORT.pdf`**](anvil-q1/SHOWCASE_REPORT.pdf) · [`SHOWCASE_REPORT.md`](anvil-q1/SHOWCASE_REPORT.md) | [**`REPORT.pdf`**](anvil-q1/REPORT.pdf) · [`REPORT.md`](anvil-q1/REPORT.md) | **PASSED** (`Fmax 108.48 MHz`, `WNS +0.782 ns`, `21,890 ALMs / 5.12%`, `219 DSPs / 14.43%`, `30-Prompt 24L + 46/46 Top-1 Token Parity`) |
| **Anvil-Q2** (`Qwen2.5-1.5B-AWQ`) | [**`SHOWCASE_REPORT.pdf`**](anvil-q2/SHOWCASE_REPORT.pdf) · [`SHOWCASE_REPORT.md`](anvil-q2/SHOWCASE_REPORT.md) | [**`REPORT.pdf`**](anvil-q2/REPORT.pdf) · [`REPORT.md`](anvil-q2/REPORT.md) | **PASSED** (`Fmax 101.39 MHz`, `WNS +0.137 ns`, `34,200 ALMs / 8.01%`, `384 DSPs / 25.30%`, `1/2/4-Bank AWQ + INT8 KV Cache`, `Cosine 0.999999953`) |

### Whitepaper Page Preview · Anvil-Q1 & Anvil-Q2

<p align="center">
  <img src="anvil-q1/showcase_figures/page-1.png" width="32%" alt="Anvil-Q1 Product Whitepaper Page 1">
  <img src="anvil-q1/showcase_figures/page-2.png" width="32%" alt="Anvil-Q1 Product Whitepaper Page 2">
  <img src="anvil-q1/showcase_figures/page-3.png" width="32%" alt="Anvil-Q1 Product Whitepaper Page 3">
</p>
<p align="center">
  <img src="anvil-q2/showcase_figures/page-1.png" width="32%" alt="Anvil-Q2 Product Whitepaper Page 1">
  <img src="anvil-q2/showcase_figures/page-2.png" width="32%" alt="Anvil-Q2 Product Whitepaper Page 2">
  <img src="anvil-q2/showcase_figures/page-3.png" width="32%" alt="Anvil-Q2 Product Whitepaper Page 3">
</p>

## Series roadmap (`100 MHz+` Baseline Policy)

All accelerators in the **Anvil-Q** series enforce a **`100.0 MHz` (`10.0 ns`)** post-fit static timing signoff baseline (with Coordinator-arbitrated timing waiver when bounded by physical architecture limits) and physical FPGA PCIe Gen3x8 HIL verification:

| Generation | Design | Target model & precision contract | Delivered RTL | Status & Signoff |
| --- | --- | --- | --- | --- |
| **Gen-1** | **[Anvil-Q1](anvil-q1/)** | [Alibaba `Qwen/Qwen2.5-0.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-AWQ) · **W4A16 AWQ G128 Mixed-Precision** (24 layers, `896d` hidden, 14Q:2KV 7:1 GQA with QKV bias, `4864d` SwiGLU MLP, `rope_theta = 1e6`, 168 AWQ INT4 group-128 linear projections) | `16` modules / `1,451` lines | **Completed & Verified (`108.48 MHz`, `WNS +0.782 ns`, Physical Arria 10 HIL)** — [Whitepaper (`SHOWCASE_REPORT.pdf`)](anvil-q1/SHOWCASE_REPORT.pdf) · [Developer (`REPORT.pdf`)](anvil-q1/REPORT.pdf) |
| **Gen-2** | **[Anvil-Q2](anvil-q2/)** | [Alibaba `Qwen/Qwen2.5-1.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-AWQ) · **1/2/4-Bank Parallel W4A16 AWQ + Lossless Q16 / Symmetric Group-32 INT8 KV-Cache Compression Engine** (28 layers, `1536d` hidden, 12Q:2KV 6:1 GQA, `8960d` SwiGLU MLP, `Anvil-Q1` compatibility mode) | `21` modules / `2,407` lines | **Completed & Verified (`101.39 MHz`, `WNS +0.137 ns`, Physical Arria 10 HIL)** — [Whitepaper (`SHOWCASE_REPORT.pdf`)](anvil-q2/SHOWCASE_REPORT.pdf) · [Developer (`REPORT.pdf`)](anvil-q2/REPORT.pdf) |
| **Gen-3+** | **Anvil-Q3+** (Planned) | Larger open-source quantized LLMs (`3B–7B+` AWQ/GPTQ with external DDR4 weight streaming & multi-bank tensor engines) | Planned | Next milestone under the `100 MHz+` Vulcan timing baseline |

## Vulcan Seven-Family Silicon Matrix

**Anvil** is the centerpiece of Vulcan's seven-family workshop silicon architecture:

| Silicon Family | Workshop Metaphor | Domain & Representative Cores |
| --- | --- | --- |
| **Anvil** *(Primary Focus)* | Heavy forge anvil bearing core compute loads | AI & Large Model Compute (`Anvil-Q` quantized causal LLM series, `Anvil-E` multimodal embedding series, matrix/tensor engines) |
| **Rivet** | Small, critical, rock-solid fasteners | Cryptography, Checksum & Data Integrity (`AES`, `SHA`, `CRC` cores) |
| **Billet** | Raw metal stock shaped and combined into systems | Digital Signal Processing (`FIR`, `FFT`, `CORDIC` cores) |
| **Swage** | Die-forming tool shaping inputs into target forms | Image Processing & ISP (scaling, filtering, pixel-format conversion) |
| **Bellows** | Expanding/contracting continuous airflow | Compression, Decompression & Streaming Data (`LZ4` accelerators) |
| **Crucible** | Vessel fusing diverse materials into form | Graphics Processing & Rendering (geometry, texture, lighting fusion) |
| **Furnace** | Industrial system integrating multiple stages | Large-Scale Heterogeneous SoCs & Complete Compute Systems |

## Anvil-Q2 · Generation 2 (`Qwen/Qwen2.5-1.5B-Instruct-AWQ` Multi-Bank + INT8 KV Edition)

`Anvil-Q2` scales the `Anvil-Q` architecture to the 28-layer [`Qwen/Qwen2.5-1.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-AWQ) checkpoint (`hidden_size = 1536`, `intermediate_size = 8960`, 12Q:2KV 6:1 GQA) while maintaining pin-and-register backward compatibility with `Anvil-Q1`:

- **1/2/4-Bank Parallel W4A16 AWQ Engine**: Achieves `1.97×` (2-bank) and `3.82×` (4-bank) end-to-end token throughput scaling with `0` bit-level deviation across banking modes.
- **Dual-Mode KV Cache Codec**: Supports bit-exact lossless Q16 (`KV_MODE=0`, cosine `1.000000000`) and symmetric group-32 INT8 (`KV_MODE=1`, `46.88%` M20K reduction, min cosine `0.999999953`).
- **101.39 MHz Timing Signoff**: Pipelined scalar arbiter, multi-bank scheduler, and AWQ GEMV lanes close Intel Arria 10 GX STA at **`101.39 MHz`** (`WNS = +0.137 ns` at `10.0 ns` clock constraint).
- **Product Whitepaper**: [`anvil-q2/SHOWCASE_REPORT.pdf`](anvil-q2/SHOWCASE_REPORT.pdf) · **Developer Report**: [`anvil-q2/REPORT.pdf`](anvil-q2/REPORT.pdf)

## Anvil-Q1 · Generation 1 (`Qwen/Qwen2.5-0.5B-Instruct-AWQ` W4A16 Edition)

`Anvil-Q1` targets the authoritative HuggingFace [`Qwen/Qwen2.5-0.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-AWQ)
checkpoint (`quant_method = "awq"`, `version = "gemm"`, `bits = 4`, `group_size = 128`, `zero_point = true`),
autonomously engineered with **Vulcan 0.8**:

| Stage / Subsystem | Authoritative Specification (`Qwen/Qwen2.5-0.5B-Instruct-AWQ`) | Hardware Engineering Focus |
| --- | --- | --- |
| **AWQ GEMM W4A16 Dequantizer & GEMV** | `bits = 4`, `group_size = 128`, `zero_point = true`, `I32 qweight` & `qzeros` nibble order `[0, 4, 1, 5, 2, 6, 3, 7]`, `F16 scales` (`w = (q - z) * s`) | On-the-fly 32-bit AWQ nibble unpacker, group-128 zero-point subtraction, scale multiplication, and wide-accumulator W4A16 dot-product engine |
| **Pre-Norm & Rotary Position (`RMSNorm` + `RoPE`)** | `rms_norm_eps = 1e-6` (`[896]`), `rope_theta = 1000000.0`, `head_dim = 64`, `max_position_embeddings = 32768` | Reciprocal-sqrt RMS normalization and rotary position embedding across 14 query heads and 2 key heads |
| **7:1 Grouped-Query Attention (`self_attn`)** | `num_attention_heads = 14`, `num_key_value_heads = 2` (`7:1` GQA), `q_proj [896->896]` + bias, `k_proj [896->128]` + bias, `v_proj [896->128]` + bias, `o_proj [896->896]` (no bias) | QKV biased AWQ projections, 2-head KV cache storage with 7× head broadcast, causal scaled dot-product attention |
| **SwiGLU Feed-Forward (`mlp`)** | `intermediate_size = 4864` (`[896, 608]` packed `I32`), `gate_proj`, `up_proj`, `silu(gate) * up`, `down_proj [4864->896]` (no bias) | 38-group (`4864 / 128`) AWQ W4A16 dual-projection SwiGLU datapath and residual accumulation |

- **Current engineering status**: `Completed & Verified — Full W4A16 AWQ RTL Delivery Package & Dual-Track Reports Published`
- **Product Whitepaper**: [`anvil-q1/SHOWCASE_REPORT.pdf`](anvil-q1/SHOWCASE_REPORT.pdf)
- **Developer Engineering Report**: [`anvil-q1/REPORT.pdf`](anvil-q1/REPORT.pdf)
- **Authoritative HuggingFace configuration**: [`anvil-q1/hf_qwen25_05b_awq_spec/`](anvil-q1/hf_qwen25_05b_awq_spec/)
- **Deliverable directory**: [`anvil-q1/`](anvil-q1/) (`rtl/`, `design/`, `tests/`)

## Delivered RTL Inventory (`Anvil-Q1`)

| Module File | Size | Role |
| --- | --- | --- |
| [`anvil-q1/rtl/anvil_q1_00_pkg.sv`](anvil-q1/rtl/anvil_q1_00_pkg.sv) | `106` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_awq_dequant.sv`](anvil-q1/rtl/anvil_q1_awq_dequant.sv) | `38` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_bus_mux.sv`](anvil-q1/rtl/anvil_q1_bus_mux.sv) | `35` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_decoder_layer.sv`](anvil-q1/rtl/anvil_q1_decoder_layer.sv) | `107` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_elementwise.sv`](anvil-q1/rtl/anvil_q1_elementwise.sv) | `91` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_gqa_attention.sv`](anvil-q1/rtl/anvil_q1_gqa_attention.sv) | `151` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_mem_port.sv`](anvil-q1/rtl/anvil_q1_mem_port.sv) | `49` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_parameters.sv`](anvil-q1/rtl/anvil_q1_parameters.sv) | `27` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_rmsnorm.sv`](anvil-q1/rtl/anvil_q1_rmsnorm.sv) | `113` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_rope.sv`](anvil-q1/rtl/anvil_q1_rope.sv) | `97` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_swiglu_mlp.sv`](anvil-q1/rtl/anvil_q1_swiglu_mlp.sv) | `75` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_top.sv`](anvil-q1/rtl/anvil_q1_top.sv) | `151` lines | Synthesizable SystemVerilog RTL module |
| [`anvil-q1/rtl/anvil_q1_w4a16_gemv.sv`](anvil-q1/rtl/anvil_q1_w4a16_gemv.sv) | `183` lines | Synthesizable SystemVerilog RTL module |

## License

Published code, documentation and artwork are provided under the [MIT License](LICENSE).
