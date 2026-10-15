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
  · <a href="anvil-q1/">Anvil-Q1 package</a>
  · <a href="brand/">Brand assets</a>
</p>

**Anvil** is our AI accelerator silicon family developed with **Vulcan 0.8**. **Anvil-Q**
is the dedicated **quantized causal LLM inference series** within the family, turning authoritative
HuggingFace AWQ mixed-precision model specifications into synthesizable SystemVerilog RTL,
self-checking verification suites and reproducible delivery packages.

## Series roadmap

| Generation | Design | Target model & precision contract | Delivered RTL | Status |
| --- | --- | --- | --- | --- |
| **Gen-1** | **[Anvil-Q1](anvil-q1/)** | [Alibaba `Qwen/Qwen2.5-0.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-AWQ) · **W4A16 AWQ G128 Mixed-Precision** (24 layers, `896d` hidden, 14Q:2KV 7:1 GQA with QKV bias, `4864d` SwiGLU MLP, `rope_theta = 1e6`, 168 AWQ INT4 group-128 linear projections) | `13` modules / `1223` lines | In Progress — Step 45 (planning) by Vulcan 0.8 |
| **Gen-2** | **Anvil-Q2** | `Qwen/Qwen2.5-1.5B-Instruct-AWQ` · Multi-bank W4A16 AWQ + KV-cache compression engine | — | Planned |

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

- **Current engineering status**: `In Progress — Step 45 (planning) by Vulcan 0.8` (updated `2026-10-15 21:12:48 UTC+8`)
- **Authoritative HuggingFace configs & Layer-0 AWQ slice**: [`anvil-q1/hf_qwen25_05b_awq_spec/`](anvil-q1/hf_qwen25_05b_awq_spec/)
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
