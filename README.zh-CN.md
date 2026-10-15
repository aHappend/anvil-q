<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/logo-dark.svg">
    <img src="brand/logo.svg" width="480" alt="Vulcan">
  </picture>
</p>

<h1 align="center">Anvil-Q · 把量化大模型，锻造成芯片。</h1>

<p align="center">
  开源 W4A16 AWQ 混合精度大模型推理加速 RTL 设计，展示真实工程成果。
  <br>
  <a href="https://ahappend.github.io/vulcan/">访问官网</a>
  · <a href="https://github.com/aHappend/vulcan-showcase">Vulcan 作品集</a>
  · <a href="README.md">English</a>
  · <a href="anvil-q1/">Anvil-Q1 交付包</a>
  · <a href="brand/">品牌素材</a>
</p>

**Anvil** 是基于 **Vulcan 0.8** 研发的 AI 加速芯片家族。**Anvil-Q** 是家族中的**量化大语言模型（Quantized LLM）专用推理芯片系列**，将 HuggingFace 权威 AWQ 混合精度模型规范转化为可综合 SystemVerilog RTL、自检验证套件与可复现的工程交付包。

## 系列路线图

| 代际 | 芯片型号 | 目标模型与混合精度规范 | 已交付 RTL | 当前状态 |
| --- | --- | --- | --- | --- |
| **第一代** | **[Anvil-Q1](anvil-q1/)** | [Alibaba `Qwen/Qwen2.5-0.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-AWQ) · **W4A16 AWQ G128 混合精度**（24 层、`896d` 隐藏维、14Q:2KV 7:1 GQA 含 QKV 偏置、`4864d` SwiGLU MLP、`rope_theta = 1e6`、全模型 168 个 AWQ 4-bit 在线反量化线性层） | `13` 个模块 / `1146` 行 | In Progress — Step 4 (designer) by Vulcan 0.8 |
| **第二代** | **Anvil-Q2** | `Qwen/Qwen2.5-1.5B-Instruct-AWQ` · 多 Bank W4A16 AWQ 与 KV-Cache 压缩加速引擎 | — | 规划中 |

## Anvil-Q1 · 第一代（`Qwen/Qwen2.5-0.5B-Instruct-AWQ` W4A16 混合精度版）

`Anvil-Q1` 严格依据 HuggingFace 官方 [`Qwen/Qwen2.5-0.5B-Instruct-AWQ`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-AWQ)
权重与量化配置（`quant_method = "awq"`、`version = "gemm"`、`bits = 4`、`group_size = 128`、`zero_point = true`），由 **Vulcan 0.8** 全自主完成架构设计、模块化 RTL 实现与黑盒独立验证：

| 计算阶段 / 硬件子系统 | 模型权威配置（`Qwen/Qwen2.5-0.5B-Instruct-AWQ`） | 硬件工程重点 |
| --- | --- | --- |
| **AWQ GEMM W4A16 在线反量化与矩阵乘（`awq_dequant` + `w4a16_gemv`）** | `bits = 4`，`group_size = 128`，`zero_point = true`，`I32 qweight` 与 `qzeros` 按 `[0, 4, 1, 5, 2, 6, 3, 7]` 交织打包，`F16 scales`（`w = (q - z) * s`） | 32 位 AWQ 4-bit 交织解包器、G128 分组零点偏置相减与缩放恢复、宽累加器 W4A16 混合精度乘加阵列 |
| **RMSNorm 与百万基底旋转位置编码（`RMSNorm` + `RoPE`）** | `rms_norm_eps = 1e-6`（`[896]`），`rope_theta = 1000000.0`，`head_dim = 64`，`max_position_embeddings = 32768` | 倒数平方根 RMS 归一化与 14 个查询头 / 2 个键头的旋转位置编码 |
| **7:1 分组查询注意力（`self_attn` GQA）** | `num_attention_heads = 14`，`num_key_value_heads = 2`（`7:1` GQA），`q_proj [896->896]`、`k/v_proj [896->128]` 含 `F16` 偏置，`o_proj [896->896]` 无偏置 | 带偏置 QKV AWQ 投影、2 头 KV Cache 存储与 7 倍分组广播、因果掩码缩放点积注意力 |
| **SwiGLU 前馈网络（`mlp`）** | `intermediate_size = 4864`（打包维度 `[896, 608]`），`gate_proj`、`up_proj`、`silu(gate) * up`、`down_proj [4864->896]`（无偏置） | 38 分组（`4864 / 128`）AWQ W4A16 双路门控投影、SiLU 激活与残差归约 |

- **当前工程状态**：`In Progress — Step 4 (designer) by Vulcan 0.8`（最近更新：`2026-10-15 18:49:03 UTC+8`）
- **官方配置与第 0 层真实 AWQ 切片快照**：[`anvil-q1/hf_qwen25_05b_awq_spec/`](anvil-q1/hf_qwen25_05b_awq_spec/)
- **交付包目录**：[`anvil-q1/`](anvil-q1/)（`rtl/`、`design/`、`tests/`）

## 已交付 RTL 模块清单（`Anvil-Q1`）

| 模块文件 | 代码规模 | 功能说明 |
| --- | --- | --- |
| [`anvil-q1/rtl/anvil_q1_00_pkg.sv`](anvil-q1/rtl/anvil_q1_00_pkg.sv) | `116` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_awq_dequant.sv`](anvil-q1/rtl/anvil_q1_awq_dequant.sv) | `38` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_bus_mux.sv`](anvil-q1/rtl/anvil_q1_bus_mux.sv) | `34` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_decoder_layer.sv`](anvil-q1/rtl/anvil_q1_decoder_layer.sv) | `107` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_elementwise.sv`](anvil-q1/rtl/anvil_q1_elementwise.sv) | `87` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_gqa_attention.sv`](anvil-q1/rtl/anvil_q1_gqa_attention.sv) | `141` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_mem_port.sv`](anvil-q1/rtl/anvil_q1_mem_port.sv) | `49` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_parameters.sv`](anvil-q1/rtl/anvil_q1_parameters.sv) | `26` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_rmsnorm.sv`](anvil-q1/rtl/anvil_q1_rmsnorm.sv) | `109` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_rope.sv`](anvil-q1/rtl/anvil_q1_rope.sv) | `92` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_swiglu_mlp.sv`](anvil-q1/rtl/anvil_q1_swiglu_mlp.sv) | `75` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_top.sv`](anvil-q1/rtl/anvil_q1_top.sv) | `144` 行 | 可综合 SystemVerilog RTL 模块 |
| [`anvil-q1/rtl/anvil_q1_w4a16_gemv.sv`](anvil-q1/rtl/anvil_q1_w4a16_gemv.sv) | `128` 行 | 可综合 SystemVerilog RTL 模块 |

## 许可

公开的代码、文档与视觉素材采用 [MIT License](LICENSE)。
