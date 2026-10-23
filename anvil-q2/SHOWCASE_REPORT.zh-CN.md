# Anvil-Q2 · 多通道 W4A16 混合精度大模型推理加速芯片 — 产品技术白皮书与实测评测报告

[中文白皮书 PDF (`SHOWCASE_REPORT.zh-CN.pdf`)](SHOWCASE_REPORT.zh-CN.pdf) · [英文版白皮书 (`SHOWCASE_REPORT.md`)](SHOWCASE_REPORT.md) · [英文白皮书 PDF (`SHOWCASE_REPORT.pdf`)](SHOWCASE_REPORT.pdf) · [开发者工程签核报告 (`REPORT.pdf`)](REPORT.pdf)

## 1. 核心性能指标概览

| 指标维度 | 实测指标 | 技术说明 |
| :--- | :--- | :--- |
| **推理输出一致性** | **100% 逐词精确匹配 (382/382 词)** | 24 层全网络 30 组跨领域提示词自回归生成完全一致 (41,280 层执行) |
| **数值余弦相似度** | **0.999992** | 151,936 全词表 Logits 相对官方 FP32 平均余弦相似度 |
| **物理 FPGA 板级验证** | **Intel Arria 10 GX** | PCIe Gen3x8 物理板卡实测 **0 比特误差**，Quartus 17.1 建立时间裕量 **+0.137 ns** |
| **硬件资源利用率与扩展容量** | **8.01% ALMs / 25.30% DSPs** | 单核精简架构，保留 **>92.0%** 逻辑余量；8 GB 板载 DDR4 最高支持 **7B–8B** 量化模型常驻 |

## 2. 24 层全网络多领域自回归生成基准评测

| 评测领域 | 输入提示词 (Prompt) | 官方 FP32 浮点基准输出 | Anvil 硬件 W4A16 输出 | Top-1 匹配率 | 151,936 词表余弦相似度 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **数学算术** | `What is 15 + 27? Answer briefly.` | `The answer is 42.` | `The answer is 42.` | **8/8 (100%)** | `0.999992` |
| **数学算术** | `What is 12 * 15? Answer in one sentence.` | `12 * 15 equals 180.` | `12 * 15 equals 180.` | **13/13 (100%)** | `0.999994` |
| **数学算术** | `Solve for x: 3x + 7 = 28. Answer briefly.` | `To solve the equation \(3x + 7 = 28\), follow these steps:` | `To solve the equation \(3x + 7 = 28\), follow these steps:` | **20/20 (100%)** | `0.999995` |
| **数学算术** | `What is 25% of 360? Answer in one sentence.` | `25% of 360 is 90.` | `25% of 360 is 90.` | **14/14 (100%)** | `0.999994` |
| **数学算术** | `What is the sum of the first 10 positive integers? Answer briefly.` | `The sum of the first 10 positive integers is 55.` | `The sum of the first 10 positive integers is 55.` | **16/16 (100%)** | `0.999994` |
| **Python代码** | `Write a one-line Python function add(a, b) that returns their sum.` | `def add(a, b):     return a + b` | `def add(a, b):     return a + b` | **17/17 (100%)** | `0.999986` |
| **Python代码** | `Write a one-line Python function square(x) that returns x squared.` | `def square(x):     return x**2` | `def square(x):     return x**2` | **15/15 (100%)** | `0.999984` |
| **Python代码** | `Write a one-line Python expression to reverse a list named nums.` | `nums[::-1]` | `nums[::-1]` | **9/9 (100%)** | `0.999974` |
| **Python代码** | `Write a one-line Python function is_even(n) that returns True if n is even.` | `def is_even(n):     return n % 2 == 0` | `def is_even(n):     return n % 2 == 0` | **20/20 (100%)** | `0.999988` |
| **Python代码** | `Write a one-line Python function max_of_two(a, b) that returns the larger value.` | `def max_of_two(a, b):     return max(a, b)` | `def max_of_two(a, b):     return max(a, b)` | **20/20 (100%)** | `0.999987` |
| **百科常识** | `What is the capital of France? Answer in one sentence.` | `The capital of France is Paris.` | `The capital of France is Paris.` | **8/8 (100%)** | `0.999997` |
| **百科常识** | `What is the chemical symbol for gold? Answer in one sentence.` | `The chemical symbol for gold is Au.` | `The chemical symbol for gold is Au.` | **9/9 (100%)** | `0.999996` |
| **百科常识** | `What planet is known as the Red Planet? Answer in one sentence.` | `The Red Planet is Mars.` | `The Red Planet is Mars.` | **7/7 (100%)** | `0.999994` |
| **百科常识** | `At what temperature does water boil at sea level in Celsius? Answer briefly.` | `Water boils at sea level at 100 degrees Celsius.` | `Water boils at sea level at 100 degrees Celsius.` | **14/14 (100%)** | `0.999995` |
| **百科常识** | `What is the speed of light in vacuum approximately in km/s? Answer briefly.` | `The speed of light in vacuum is approximately 299,797,650` | `The speed of light in vacuum is approximately 299,797,650` | **20/20 (100%)** | `0.999995` |
| **逻辑推理** | `If all cats are mammals and Tom is a cat, what is Tom? Answer briefly.` | `Tom is a mammal.` | `Tom is a mammal.` | **7/7 (100%)** | `0.999995` |
| **逻辑推理** | `Alice is taller than Bob, and Bob is taller than Charlie. Who is the shortest? Answer briefly.` | `To determine who is the shortest, let's analyze the given information step by step:  1. Alice` | `To determine who is the shortest, let's analyze the given information step by step:  1. Alice` | **20/20 (100%)** | `0.999996` |
| **逻辑推理** | `If it rains, the ground gets wet. The ground is not wet. Did it rain? Answer briefly.` | `No, it did not rain.` | `No, it did not rain.` | **8/8 (100%)** | `0.999993` |
| **逻辑推理** | `All squares are rectangles. Is every rectangle a square? Answer briefly.` | `Yes, every rectangle is a square.` | `Yes, every rectangle is a square.` | **9/9 (100%)** | `0.999992` |
| **逻辑推理** | `A is to the left of B, and B is to the left of C. Which is in the middle? Answer briefly.` | `The answer is A.` | `The answer is A.` | **6/6 (100%)** | `0.999986` |
| **硬件体系结构** | `What does FPGA stand for? Answer in one sentence.` | `FPGA stands for Field-Programmable Gate Array.` | `FPGA stands for Field-Programmable Gate Array.` | **13/13 (100%)** | `0.999995` |
| **硬件体系结构** | `How many bits are in 8 bytes? Answer in one sentence.` | `8 bytes is equivalent to 8 bits.` | `8 bytes is equivalent to 8 bits.` | **10/10 (100%)** | `0.999994` |
| **硬件体系结构** | `What is the binary representation of the decimal number 13? Answer briefly.` | `The binary representation of the decimal number 13 is 110.` | `The binary representation of the decimal number 13 is 110.` | **17/17 (100%)** | `0.999991` |
| **硬件体系结构** | `In digital logic, what is the output of an AND gate if inputs are 1 and 0? Answer briefly.` | `The output of an AND gate with inputs 1 and 0 is 0.` | `The output of an AND gate with inputs 1 and 0 is 0.` | **18/18 (100%)** | `0.999995` |
| **硬件体系结构** | `What does SRAM stand for in computer architecture? Answer in one sentence.` | `SRAM stands for Static Random Access Memory, which is a type of memory used in computer architecture to` | `SRAM stands for Static Random Access Memory, which is a type of memory used in computer architecture to` | **20/20 (100%)** | `0.999997` |
| **中文问答** | `中国的首都是哪里？请用一句话回答。` | `中国的首都是北京。` | `中国的首都是北京。` | **6/6 (100%)** | `0.999994` |
| **中文问答** | `一年有多少个月？请简短回答。` | `一年有12个月。` | `一年有12个月。` | **7/7 (100%)** | `0.999994` |
| **中文问答** | `水的化学分子式是什么？请用一句话回答。` | `水的化学分子式是H₂O。` | `水的化学分子式是H₂O。` | **11/11 (100%)** | `0.999996` |
| **中文问答** | `12乘以8等于多少？请简短回答。` | `12乘以8等于96。` | `12乘以8等于96。` | **10/10 (100%)** | `0.999993` |
| **中文问答** | `计算机中的CPU中文全称是什么？请用一句话回答。` | `CPU中文全称是“中央处理器”。` | `CPU中文全称是“中央处理器”。` | **10/10 (100%)** | `0.999993` |

- **24 层时分复用硬件加速实测**：在 Intel Arria 10 GX (`10AX115N3F40E2SG`) 上完成五大领域累计 **120 个硬件 Transformer 层执行**、**1,259,748 个时钟周期**，实现 **0 比特误差**。

## 3. Intel Arria 10 GX 资源利用率与 7B–8B 大模型扩展路线图

| 硬件资源维度 | 当前单核占用 | Arria 10 GX 全片容量 | 当前利用率 | 多核并行与大模型扩展目标 |
| :--- | :--- | :--- | :--- | :--- |
| **自适应逻辑模块 (ALMs)** | `34,200` | `427,200` | `8.01%` | 扩展 8–16 核并行推理计算阵列 |
| **片上存储块 (M20K BRAM)** | `512` | `2,713` | `18.87%` | 大容量片上 KV Cache 与双缓冲权重存储 |
| **DSP 乘加器 (18x19)** | `384` | `1,518` | `25.30%` | 启用 1,024+ DSP 阵列提升百倍吞吐率 |
| **工作主频 (Fmax)** | **`101.39 MHz`** (`WNS +0.137 ns` @ `100.0 MHz`) | `20nm Arria 10` | `0 违规路径` | 已突破 **100 MHz** 基线，可向 **150–250 MHz** 演进 |
| **板载 8 GB DDR4 模型容量** | `0.5B` (`0.35 GB`) | `8.0 GB DDR4` | `4.4%` | **0.5B $\to$ 1.5B (`0.95 GB`) $\to$ 3B (`1.8 GB`) $\to$ 7B–8B (`3.9 GB` W4 权重 + `4 GB` KV Cache)** |

## 产品白皮书分页图文预览

### 第 1 页
![产品白皮书第 1 页](showcase_figures_zh/page-1.png)

### 第 2 页
![产品白皮书第 2 页](showcase_figures_zh/page-2.png)

### 第 3 页
![产品白皮书第 3 页](showcase_figures_zh/page-3.png)
