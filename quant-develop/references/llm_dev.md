# QuantSystem LLM 应用开发架构规范 (Architectural & Robustness Focus)

本规范定义了 QuantSystem 中 LLM 应用的高层架构原则，旨在构建**模型无关 (Model-Agnostic)**、**高韧性 (Resilient)** 且**可评估 (Evaluable)** 的量化智能系统。

## 1. 核心设计原则 (Core Principles)

1.  **解耦 (Decoupling)**: 业务逻辑必须与具体模型供应商（OpenAI/Anthropic/Google）完全解耦。代码中严禁硬编码 `gpt-4` 或 `claude-3` 等具体版本号。
2.  **防御性 (Defensiveness)**: 始终假设 LLM 输出是不可靠的、包含幻觉的或格式错误的。必须在系统层面实施严格的校验与兜底。
3.  **可观测性 (Observability)**: 所有 LLM 交互必须包含完整的 Trace（输入/输出/耗时/Token消耗/成本），便于回溯与优化。
4.  **评估驱动 (Eval-Driven)**: 任何 Prompt 或流程的变更，必须通过自动化评估集（Golden Dataset）的测试才能上线。

## 2. 四层架构体系 (The 4-Layer Architecture)

### 2.1 控制层 (Control Layer) - 调度与韧性
*   **Capability Routing (能力路由)**: 基于任务需求配置路由策略，而非指定模型。
    *   *Example*: `profile="reasoning"` -> 路由至当前配置的 SOTA 模型；`profile="fast"` -> 路由至 Flash 类模型。
*   **Resilience Patterns (韧性模式)**:
    *   **Circuit Breaker (熔断)**: 当某供应商连续失败 N 次或延迟过高时，自动熔断并切换至备用供应商。
    *   **Fallback Strategy (降级)**: SOTA 模型不可用 -> 降级至次优模型 -> 降级至规则引擎 -> 返回安全默认值。
*   **Context Window Management**: 动态计算 Token 使用率，实施滑动窗口或智能压缩，严禁直接截断导致 JSON 结构破损。

### 2.2 数据层 (Data Layer) - 清洗与压缩
*   **Context Engineering**:
    *   **Map-Reduce**: 针对长文档，采用分块摘要（Map）+ 全局综合（Reduce）策略，保留跨段落的逻辑关联。
    *   **RAG Optimization**: 检索内容需按相关性重排序（Re-ranking），并限制 Top-K 上下文长度，避免 "Lost in the Middle" 现象。
*   **Data Contracts**: 定义严格的输入数据 Schema。脏数据（如乱码 PDF）必须在进入 Prompt 之前被拦截或标记。

### 2.3 认知层 (Cognitive Layer) - 推理与生成
*   **Prompt Management**:
    *   **Prompts as Code**: Prompt 视为代码，进行版本管理（Git）。
    *   **Template Separation**: 逻辑模板（Template）与注入数据（Context）分离，防止 Prompt Injection 攻击。
*   **Thinking Process**: 强制要求复杂任务输出 "Thinking" 步骤（CoT），将推理过程与最终结论分离，便于审计逻辑缺陷。

### 2.4 质控层 (QA Layer) - 校验与纠错
*   **Structured Enforcement**:
    *   严禁使用纯文本输出进行后续处理。必须强制 JSON/XML 结构化输出。
    *   使用 Pydantic/Zod 等库进行 Schema 校验（类型检查、范围检查、枚举检查）。
*   **Auto-Correction (自动纠错)**:
    *   **L1 (Regex Fix)**: 尝试修复常见的 JSON 格式错误（如缺少引号、尾部逗号）。
    *   **L2 (LLM Fix)**: 将错误信息反馈给轻量级模型进行重写修复。
*   **Actor-Critic Loop**: 引入独立的 Reviewer 角色，对生成结果进行事实性（Factuality）和逻辑性（Logic）检查。

## 3. 配置管理与模型抽象 (Configuration & Abstraction)

### 3.1 抽象能力配置 (Capability Profiles)
推荐使用 YAML 定义能力配置文件，而非硬编码模型参数：

```yaml
profiles:
  # 深度推理任务（如宏观归因、策略逻辑生成）
  reasoning:
    primary:
      provider: "openai"
      model: "gpt-4-turbo"  # 仅此处定义，代码引用 profile_name
      temperature: 0.7
    fallback:
      provider: "anthropic"
      model: "claude-3-opus"
      temperature: 0.5
    
  # 高频简单任务（如文本提取、格式转换）
  extraction:
    primary:
      provider: "google"
      model: "gemini-1.5-flash"
      temperature: 0.0
    fallback:
      provider: "openai"
      model: "gpt-3.5-turbo"
```

### 3.2 动态配置热加载
系统应支持在不重启服务的情况下热加载模型配置，以便在供应商宕机时快速人工介入切换流量。

## 4. 评估与测试 (Evaluation & Testing)

### 4.1 单元测试 (Unit Tests)
*   **Format Check**: 测试 Prompt 是否能生成符合 Schema 的 JSON。
*   **Regression Check**: 确保 Prompt 修改后，关键指标（如 JSON 解析成功率）不下降。

### 4.2 黄金数据集 (Golden Dataset)
维护一套包含 "输入 + 期望输出 + 评分标准" 的测试集：
*   **Semantic Similarity**: 使用 Embedding 计算生成结果与标准答案的语义相似度。
*   **LLM-as-a-Judge**: 使用 SOTA 模型作为裁判，对生成结果的准确性、完整性进行打分。

## 5. 常见反模式 (Anti-Patterns)
*   ❌ **Hardcoding Models**: 代码中出现 `if model == "gpt-4": ...`。
*   ❌ **Silent Failure**: 解析失败直接返回 `None` 而不记录 Error Log。
*   ❌ **Prompt In Code**: 将长 Prompt 字符串直接写在 Python 文件中。
*   ❌ **Blind Trust**: 直接使用 LLM 输出的内容执行 SQL 或 Shell 命令（必须经过沙箱/白名单校验）。
