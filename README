

# ---

**Satellite Design Evolution Engine (MSSIM)**

**Next-Gen Generative Engineering Design Engine | DV1.4 Engineering MVP** \> *Neuro-Symbolic Collaboration for Satellite Layout Optimization*

## ---

**📖 项目简介 (Introduction)**

**Satellite Design Evolution Engine** 是一个基于 **“神经符号协同 (Neuro-Symbolic Collaboration)”** 架构的智能卫星布局设计系统 。

\+1

传统卫星设计面临多学科强耦合、专家经验依赖度高、迭代周期长等痛点 。本项目通过解耦 **“宏观语义决策 (Macro-Semantic)”** 与 **“微观数值寻优 (Micro-Optimization)”** ，实现了从模糊设计意图到精确物理落地的全自动闭环。

\+3

**核心价值：**

* **语义驱动**：利用 LLM (Qwen-Plus) 处理复杂的拓扑逻辑与冲突消解 。

* **物理落地**：利用 Scipy 数值求解器在 AI 划定的子空间内进行高精度寻优 。  
  \+1

* **工程合规**：通过严格的 Data Protocol (Pydantic) 防止 AI 幻觉，确保输出可执行 。  
  \+1

## ---

**🏗️ 系统架构 (Architecture)**

本系统遵循 **DV1.4 工程版** 架构，包含五大核心模块 ：

1. **Semantic (语义层)**:  
   * **ContextPack**: 将物理状态（热点、违规）压缩为 LLM 可读摘要 。

   * **Gateway**: 集成 Qwen 大模型，负责策略生成。  
   * **Spec Check**: 强类型校验 SearchSpec，拦截非法指令 。

2. **Orchestrator (主控)**:  
   * 负责状态机流转、文件管理与全链路追溯 (Traceability) 。

3. **SimEval (仿真评估)**:  
   * 内置轻量级物理引擎（几何干涉 \+ 热辐射模型）。

4. **SearchOpt (搜索优化)**:  
   * **Macro**: LLM 决定优化方向（拓扑跳转）。

   * **Micro**: 梯度下降算法（Minimize Scalar）在 Bounds 内寻找最优解 。

5. **Visualization (可视化)**:  
   * 自动化生成工程仪表盘与演化轨迹图。

## ---

**📂 目录结构 (Directory Structure)**

Plaintext

mssim/  
├── app.py              \# \[Service\] 语义层微服务 (Flask \+ LLM Gateway)  
├── protocol.py         \# \[Data\] 数据协议定义 (ContextPack/SearchSpec Schema)  
├── run\_pro.py          \# \[Core\] 工程主控脚本 (Physics \+ Orchestrator \+ Solver)  
├── logger.py           \# \[Util\] 日志与文件管理 (Traceability System)  
├── analyzer.py         \# \[Util\] 数据分析与可视化绘图 (Dashboard Generator)  
├── requirements.txt    \# \[Env\] 项目依赖清单  
└── experiments/        \# \[Output\] 实验结果产出目录 (Auto-generated)  
    └── run\_2026xxxx\_xxxxxx/  
        ├── design\_dashboard.png  \# 演化轨迹可视化图表  
        ├── evolution\_trace.csv   \# 过程数据记录  
        ├── report.md             \# 总结报告  
        └── llm\_interactions/     \# LLM 交互全纪录 (Req/Resp JSON)

## ---

**🚀 快速开始 (Getting Started)**

### **1\. 环境准备**

确保已安装 Python 3.8+。

Bash

\# 安装依赖  
pip install \-r requirements.txt

### **2\. 配置 API Key**

本项目使用阿里云 DashScope (Qwen) 作为推理核心。

在项目根目录创建 .env 文件，或直接在终端设置环境变量：

Bash

\# Linux/Mac  
export DASHSCOPE\_API\_KEY="sk-your-api-key"

\# Windows PowerShell  
$env:DASHSCOPE\_API\_KEY="sk-your-api-key"

### **3\. 运行系统**

本系统采用 **微服务架构**，需分别启动“大脑”与“躯干”。

**步骤 A: 启动语义引擎 (The Brain)**

在一个终端窗口中运行：

Bash

python app.py  
\# 输出: 🚀 Satellite Semantic Engine running on port 5000...

**步骤 B: 启动工程闭环 (The Loop)**

在另一个终端窗口中运行：

Bash

python run\_pro.py  
\# 输出: 🚀 Starting Engineering Run...

## ---

**📊 结果产出 (Outputs)**

运行结束后，系统会自动在 experiments/ 目录下生成带有时间戳的文件夹。包含以下核心资产 ：

1. **Dashboard (design\_dashboard.png)**:  
   * **Trajectory**: 展示组件如何绕过障碍物（Rib）并避开热源。  
   * **Convergence**: 温度与干涉距离的收敛曲线。  
2. **Trace Data (evolution\_trace.csv)**:  
   * 包含每一步的坐标、温度、Cost、AI 推理耗时等结构化数据。  
3. **Audit Logs (llm\_interactions/)**:  
   * 完整保存每一轮的 ContextPack (输入) 和 SearchSpec (输出)，用于工程审计与 Prompt 优化。

## ---

**📅 演进路线 (Roadmap)**

当前版本为 **DV1.4**，对标蓝图中的“工程版原型”阶段 。

\+1

* \[x\] **DV1.0 Simplified**: 跑通 Context \-\> LLM \-\> JSON 流程 。

* \[x\] **DV1.2 Minimal Loop**: 引入 Scipy 数值求解器，实现 Neuro-Symbolic 闭环。  
* \[x\] **DV1.4 Engineering MVP**: 增加全链路日志、可视化分析、工程级代码重构。  
* \[ \] **DV2.0 Basic**:  
  * 接入真实物理场仿真 (High-Fi FEA) 。

  * 扩展算子库 (Swap, Add Surface) 。

  * 支持历史回滚 (History Rollback) 。

* \[ \] **DV3.0 Engineering**:  
  * 自动布线 (Auto-Routing) 。

  * 自愈与鲁棒性增强 (Self-Healing) 。

## ---
