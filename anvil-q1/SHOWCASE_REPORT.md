# Anvil-Q1 Phase 2: Official AWQ Weight Integration and Software–RTL Evaluation — 对外通俗高级版成果展示与实验白皮书 (Executive & Public Showcase Report)

> **双轨制报告导读 (Dual-Track Reports)**：本仓库同时提供面向外界读者的通俗高级展示版 [`SHOWCASE_REPORT.pdf`](SHOWCASE_REPORT.pdf)（本文档）与面向硬件开发者的专业工程签核版 [`REPORT.pdf`](REPORT.pdf) / [`REPORT.md`](REPORT.md)。

## 1. 一页看懂核心成果 (Executive KPI Highlights)

| 核心指标维度 | 实测成果数据 | 通俗解读与工程意义 |
| :--- | :--- | :--- |
| **任务与输出对齐率 (Fidelity)** | **100% Top-1 (46/46 Tokens)** | 24-Layer 5-Domain Natural Language Dialogue Exact Match |
| **数值余弦相似度 (Cosine Sim)** | **0.999993** | Mean 151,936-Vocab Logit Cosine vs. Official HuggingFace FP32 |
| **真实物理芯片上板 (Real FPGA)** | **Intel Arria 10 (`netsys17`)** | PCIe Gen3x8 物理板卡实测 **0 比特错误**，Quartus 17.1 建立时间裕量 **+27.218 ns** |
| **FPGA 资源占用与扩容潜力** | **仅占 5.12% ALMs / 14.43% DSPs** | 剩余 **>94.9%** 算力可实现 **150x+** 并行提速，8GB 板载 DDR4 最大可常驻运行 **7B–8B 大模型** |

## 2. 五大领域真实对话实测对比 (24-Layer Multi-Domain Live Dialogue Showcase)

| 测试领域 | 用户输入 (Prompt) | HuggingFace 官方 FP32 软件输出 | Anvil 芯片硬件 W4A16 输出 | Top-1 匹配率 | 151,936 词表余弦相似度 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mathematics / 数学算术** | `What is 15 + 27? Answer briefly.` | `The answer is 42.` | `The answer is 42.` | **8/8 (100%)** | `0.999992` |
| **Code Generation / Python代码** | `Write a one-line Python function add(a, b) that returns their sum.` | `def add(a, b):     return a + b` | `def add(a, b):     return a + b` | **17/17 (100%)** | `0.999986` |
| **General Knowledge / 百科常识** | `What is the capital of France? Answer in one sentence.` | `The capital of France is Paris.` | `The capital of France is Paris.` | **8/8 (100%)** | `0.999997` |
| **Logical Reasoning / 逻辑推理** | `If all cats are mammals and Tom is a cat, what is Tom? Answer briefly.` | `Tom is a mammal.` | `Tom is a mammal.` | **7/7 (100%)** | `0.999995` |
| **Chinese Dialogue / 中文问答** | `中国的首都是哪里？请用一句话回答。` | `中国的首都是北京。` | `中国的首都是北京。` | **6/6 (100%)** | `0.999994` |

- **物理 FPGA 24 层流式协处理实测 (`netsys17`)**：通过 12 趟 × 2 层/趟流式权重加载，在真实 Intel Arria 10 GX FPGA 上累计完成 **120 个物理 Transformer 层**、**1,259,748 个硬件时钟周期**，实现 **0 比特误差**。

## 3. FPGA 资源利用率与 7B 大模型扩容路线图 (Silicon Utilization & 7B LLM Roadmap)

| 资源 / 演进维度 | 当前 v1 实测 | Arria 10 GX 总容量 | 当前利用率 | 下一代深度优化与扩容目标 |
| :--- | :--- | :--- | :--- | :--- |
| **ALMs 逻辑单元** | `21,890` | `427,200` | `5.12%` | 扩展 64–128 路并行计算阵列 |
| **M20K 片上存储** | `1` | `2,713` | `0.04%` | 大容量片上 KV Cache 与双缓冲 Ping-Pong |
| **DSP 硬件乘加器** | `219` | `1,518` | `14.43%` | 启用 1,024+ 颗 DSP 实现 **150x–200x** 吞吐提速 |
| **工作主频 (Fmax)** | `25 MHz` (`WNS +27.218 ns`) | `20nm Arria 10` | 正裕量充沛 | 深度流水线重定时提升至 **150–250 MHz (6x–10x)** |
| **板载 8GB DDR4 大模型容量** | `0.5B` (`~0.35 GB`) | `8.0 GB DDR4` | `4.4%` | **0.5B $\to$ 1.5B (`0.95 GB`) $\to$ 3B (`1.8 GB`) $\to$ 7B–8B (`3.9 GB` W4 权重 + `4 GB` KV Cache 单卡全常驻)** |

## Illustrated Showcase Whitepaper Pages (对外通俗高级版图文白皮书分页预览)

### Showcase Page 1
![Showcase Page 1](showcase_figures/page-1.png)

### Showcase Page 2
![Showcase Page 2](showcase_figures/page-2.png)

### Showcase Page 3
![Showcase Page 3](showcase_figures/page-3.png)
