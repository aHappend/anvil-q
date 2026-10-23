# Anvil-Q1 · W4A16 混合精度大语言模型推理加速芯片 — 产品技术白皮书与实测评测报告

[中文白皮书 PDF (`SHOWCASE_REPORT.zh-CN.pdf`)](SHOWCASE_REPORT.zh-CN.pdf) · [英文版白皮书 (`SHOWCASE_REPORT.md`)](SHOWCASE_REPORT.md) · [英文白皮书 PDF (`SHOWCASE_REPORT.pdf`)](SHOWCASE_REPORT.pdf) · [开发者工程签核报告 (`REPORT.pdf`)](REPORT.pdf)

## 1. 核心性能指标概览

| 指标维度 | 实测指标 | 技术说明 |
| :--- | :--- | :--- |
| **推理输出一致性** | **100% 逐词精确匹配 (46/46 词)** | 24 层全网络五大领域自回归对话生成完全一致 |
| **数值余弦相似度** | **0.999993** | 151,936 全词表 Logits 相对官方 FP32 平均余弦相似度 |
| **物理 FPGA 板级验证** | **Intel Arria 10 GX** | PCIe Gen3x8 物理板卡实测 **0 比特误差**，Quartus 17.1 建立时间裕量 **+27.218 ns** |
| **硬件资源利用率与扩展容量** | **5.12% ALMs / 14.43% DSPs** | 单核精简架构，保留 **>94.9%** 逻辑余量；8 GB 板载 DDR4 最高支持 **7B–8B** 量化模型常驻 |

## 2. 24 层全网络多领域自回归生成基准评测

| 评测领域 | 输入提示词 (Prompt) | 官方 FP32 浮点基准输出 | Anvil 硬件 W4A16 输出 | Top-1 匹配率 | 151,936 词表余弦相似度 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **数学算术** | `What is 15 + 27? Answer briefly.` | `The answer is 42.` | `The answer is 42.` | **8/8 (100%)** | `0.999992` |
| **Python代码** | `Write a one-line Python function add(a, b) that returns their sum.` | `def add(a, b):     return a + b` | `def add(a, b):     return a + b` | **17/17 (100%)** | `0.999986` |
| **百科常识** | `What is the capital of France? Answer in one sentence.` | `The capital of France is Paris.` | `The capital of France is Paris.` | **8/8 (100%)** | `0.999997` |
| **逻辑推理** | `If all cats are mammals and Tom is a cat, what is Tom? Answer briefly.` | `Tom is a mammal.` | `Tom is a mammal.` | **7/7 (100%)** | `0.999995` |
| **中文问答** | `中国的首都是哪里？请用一句话回答。` | `中国的首都是北京。` | `中国的首都是北京。` | **6/6 (100%)** | `0.999994` |

- **24 层时分复用硬件加速实测**：在 Intel Arria 10 GX (`10AX115N3F40E2SG`) 上完成五大领域累计 **120 个硬件 Transformer 层执行**、**1,259,748 个时钟周期**，实现 **0 比特误差**。

## 3. Intel Arria 10 GX 资源利用率与 7B–8B 大模型扩展路线图

| 硬件资源维度 | 当前单核占用 | Arria 10 GX 全片容量 | 当前利用率 | 多核并行与大模型扩展目标 |
| :--- | :--- | :--- | :--- | :--- |
| **自适应逻辑模块 (ALMs)** | `21,890` | `427,200` | `5.12%` | 扩展 8–16 核并行推理计算阵列 |
| **片上存储块 (M20K BRAM)** | `384` | `2,713` | `14.15%` | 大容量片上 KV Cache 与双缓冲权重存储 |
| **DSP 乘加器 (18x19)** | `219` | `1,518` | `14.43%` | 启用 1,024+ DSP 阵列提升百倍吞吐率 |
| **工作主频 (Fmax)** | `25 MHz` (`WNS +27.218 ns`) | `20nm Arria 10` | `0 违规路径` | 深度流水线重定时提升至 **150–250 MHz** |
| **板载 8 GB DDR4 模型容量** | `0.5B` (`0.35 GB`) | `8.0 GB DDR4` | `4.4%` | **0.5B $\to$ 1.5B (`0.95 GB`) $\to$ 3B (`1.8 GB`) $\to$ 7B–8B (`3.9 GB` W4 权重 + `4 GB` KV Cache)** |

## 产品白皮书分页图文预览

### 第 1 页
![产品白皮书第 1 页](showcase_figures_zh/page-1.png)

### 第 2 页
![产品白皮书第 2 页](showcase_figures_zh/page-2.png)

### 第 3 页
![产品白皮书第 3 页](showcase_figures_zh/page-3.png)
