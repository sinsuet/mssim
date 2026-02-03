
# ---

**卫星总体构型演化系统 (Satellite Design Evolution Engine)**

## **工程阶段总结报告 (DV1.4 Engineering MVP)**

**日期**: 2026-02-04

**版本**: DV1.4 (Neuro-Symbolic Engineering Loop)

**状态**: ✅ 核心闭环跑通 / ✅ 工程化重构完成

## ---

**1\. 核心成果摘要 (Executive Summary)**

本项目旨在构建下一代生成式工程设计引擎，通过 **“神经符号协同 (Neuro-Symbolic Collaboration)”** 解决卫星布局设计中多学科耦合与局部最优的难题。

截至目前，我们已成功完成了 **DV1.4 工程版** 的代码构建与验证。系统实现了从物理状态感知、大模型语义决策、到数值求解器微观落地的全自动闭环。特别是核心的 **LLM 语义层 (Semantic Layer)**，已完全满足架构设计中关于“上下文压缩”、“网关控制”及“规格校验”的定义要求。

## ---

**2\. 深度对标：LLM 语义层实现情况 (Semantic Layer)**

本节重点对比 **架构要求** (参考上传图片 image\_b55504.jpg, image\_d2c6a0.png) 与 **当前代码实现**。

### **2.1 模块一：上下文 (Context Ctx)**

**目标**：把当前设计状态压缩成 LLM 可用的上下文包，包含热点、违规、历史失败模式及可用动作。

| 架构要求 (Requirements) | 当前代码实现 (Implementation) | 对应文件/代码 | 状态 |
| :---- | :---- | :---- | :---- |
| **热点与违规提取** | 物理引擎计算 dist\_to\_rib 和 max\_temp，生成结构化的 ViolationItem 列表。 | run\_pro.py 中的 physics\_update() 方法 | ✅ |
| **可读摘要生成** | 将数值矩阵转化为自然语言描述 ("Battery at X=8 clash with Rib")。 | protocol.py 中的 to\_markdown\_prompt() | ✅ |
| **历史失败模式** | 记录 Solver 的尝试结果（如“Iter 2 移动失败”），防止 LLM 反复横跳。 | ContextPack.history\_trace 字段 | ✅ |
| **可用动作约束** | **\[关键升级\]** 显式告知 LLM 当前场景下允许使用的算子（如仅 MOVE）。 | ContextPack.allowed\_ops 字段 | ✅ |

### **2.2 模块二：LLM 网关 (LLM Gateway)**

**目标**：负责模型调用、提示模板、工具路由与费用/时延控制。

| 架构要求 (Requirements) | 当前代码实现 (Implementation) | 对应文件/代码 | 状态 |
| :---- | :---- | :---- | :---- |
| **模型调用** | 集成阿里云 DashScope SDK，调用 qwen-plus 模型。 | app.py 中的 call\_qwen\_brain() | ✅ |
| **提示模板 (Prompt)** | System Prompt 注入，强制规定“AI 专家人设”与“JSON 输出格式”。 | app.py 中的 system\_prompt 变量 | ✅ |
| **工具路由** | 目前支持单一优化路由 (/optimize)，架构已预留扩展接口。 | Flask Route @app.route('/optimize') | ✅ |
| **费用/时延控制** | 实现了基础的超时处理与 Token 消耗记录（通过 Log 统计），尚未实现熔断机制。 | logger.py 记录 ai\_reasoning\_len | 🔄 (部分) |

### **2.3 模块三：规格检 (Spec Check)**

**目标**：负责 SearchSpec 的 Schema/规则一致性校验，不合格则拒绝入链。

| 架构要求 (Requirements) | 当前代码实现 (Implementation) | 对应文件/代码 | 状态 |
| :---- | :---- | :---- | :---- |
| **Schema 校验** | 使用 Pydantic 严格定义 SearchSpec 数据结构，类型错误直接抛异常。 | protocol.py 中的 SearchSpec 类 | ✅ |
| **规则一致性** | 校验 bounds 是否为 \[min, max\]，校验 op\_id 是否在枚举中。 | protocol.py 中的 @field\_validator | ✅ |
| **拒绝入链** | 如果 LLM 输出格式错误或产生幻觉算子，HTTP 返回 400，保护下游 Solver。 | app.py 中的 try...except ValidationError | ✅ |

## ---

**3\. 系统架构实现详解 (System Architecture)**

我们构建了一个典型的 **“主控-微服务”** 架构，实现了物理与语义的解耦。

### **3.1 神经符号双层闭环 (Macro-Micro Loop)**

这是系统的核心引擎，解决了“大模型不懂数学，求解器不懂逻辑”的矛盾。

* **外层 (Macro \- The Brain):**  
  * **角色**: Qwen 大模型。  
  * **职责**: 负责**拓扑跳转**与**策略制定**。  
  * **逻辑**: "检测到 X 轴有墙，且温度不高，因此策略是向 \-X 轴移动以换取空间。" \-\> 输出 Bounds: \[-5, 0\]。  
* **内层 (Micro \- The Solver):**  
  * **角色**: Scipy (minimize\_scalar).  
  * **职责**: 负责**连续参数寻优**。  
  * **逻辑**: 在 AI 给定的 \[-5, 0\] 区间内，利用梯度下降找到代价值最小的精确点（如 \-2.34mm）。  
  * **亮点**: 引入了 **"安全裕度 (Safety Margin)"** 代价函数，让设计不仅“不违规”，而且“有余量”。

### **3.2 全链路可追溯性 (Traceability)**

为了满足工程审计需求，我们实现了 logger.py 模块：

* **独立实验目录**: 每次运行生成 experiments/run\_YYYYMMDD\_HHMMSS/。  
* **证据链 (Chain of Evidence)**: llm\_interactions/ 文件夹完整保存了每一轮发给 LLM 的 Prompt (Req) 和 LLM 返回的原始 JSON (Resp)。  
* **数据演化表**: evolution\_trace.csv 记录了每一次迭代的物理指标变化。

### **3.3 可视化分析 (Visual Analysis)**

analyzer.py 模块实现了自动化报表生成：

* **轨迹图**: 直观展示组件如何在“热源”与“障碍物”之间寻找安全路径。  
* **收敛曲线**: 展示温度和干涉距离随迭代次数的下降趋势。

## ---

**4\. 文件结构说明 (Project Structure)**

项目已按照工程化标准进行了模块拆分：

Plaintext

mssim/  
├── app.py           \# \[Service\] 语义层微服务 (Flask \+ LLM Gateway)  
├── protocol.py      \# \[Data\] 数据协议定义 (ContextPack/SearchSpec)  
├── run\_pro.py       \# \[Core\] 工程主控脚本 (Physics \+ Orchestrator \+ Solver)  
├── logger.py        \# \[Util\] 日志与文件管理  
├── analyzer.py      \# \[Util\] 数据分析与可视化绘图  
├── requirements.txt \# \[Env\] 项目依赖清单  
└── experiments/     \# \[Output\] 实验结果产出目录  
    └── run\_20260204\_011022/  
        ├── design\_dashboard.png  \# 自动生成的可视化仪表盘  
        ├── evolution\_trace.csv   \# 过程数据  
        ├── report.md             \# 总结报告  
        └── llm\_interactions/     \# LLM 交互全纪录

## ---

**5\. 下一步计划 (Next Steps)**

虽然 DV1.4 已达到 MVP 标准，但距离 DV2.0 (Run Stable) 仍需在以下方面进行增强：

1. **多保真仿真接口 (SimEval Upgrade)**:  
   * 目前使用简易物理公式。下一步需接入轻量级 FEA (有限元) 库或查表法，以支持更复杂的物理场。  
2. **更复杂的算子库 (OpsGeo Extension)**:  
   * 目前仅支持 MOVE。需实现 SWAP (交换组件) 和 ADD\_SURFACE (增加散热面) 的几何逻辑。  
3. **熔断与重试机制**:  
   * 在 app.py 中增加对 LLM API 异常的自动重试（Exponential Backoff）。

---

**结论**:

目前的系统已完美复现了设计图中的 **"语义驱动与物理反馈闭环"** 核心逻辑。数据流清晰、接口规范、具备完全的可解释性和可追溯性，为后续的复杂场景扩展打下了坚实基础。