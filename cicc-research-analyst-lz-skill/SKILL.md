---
name: cicc-research-analyst-lz-skill
description: Use when the user explicitly asks 李昭 for an analyst perspective, or asks for a CICC perspective on 黄金贵金属与跨资产配置; not for generic explanations or weekly forecast bookkeeping.
metadata:
  openclaw:
    requires:
      env: [APP_ID, APP_SECRET]
      bins: [python3, pip3]
    query_replace: '{{query}}'
version: 1.0.1
---

# 李昭分析师接口

调用中金点睛的远程分析师服务；返回内容是 AI 生成的分析师视角，不能冒充本人发布的研报或已核验事实。

## 路由边界

- 点名 李昭 的一次性咨询由本 Skill 负责；覆盖 黄金贵金属、跨资产配置、美国利率汇率与国际货币体系。
- 未点名但明确要求中金视角时，按 `skill-registry.yaml` 的 `analyst_default_topics` 选最具体的一位。
  跨主题同等匹配则说明歧义，不默认并行调用六位；普通概念解释不自动调用远程服务。
- 周度情景概率、冻结预测快照和到期复盘仍由 `macro-strategy-learning` 主导；本 Skill 仅提供观点来源。

## 执行

1. 使用本 Skill 根目录作为命令工作目录，确认 query、时间范围、`APP_ID` 和 `APP_SECRET`。
   凭据来自中金点睛授权配置。只检查是否存在，不读取到回复、日志或命令参数中；缺失则停留在待配置状态。
2. 在完整用户问题后追加“请用李昭skill回答”，保留原问题的限制。
   在技能根目录运行 `python scripts/get_data.py "李昭, 怎么看黄金？"`；无需留回答文件时加 `--no-save`。
3. 等待同一个 SSE 请求完成，不因生成较慢重新发起调用。使用宿主工具的非阻塞运行/继续等待能力。
   不把分段内容当作最终结果；连接、鉴权或接口返回失败时给出真实失败信息，不自行生成替代结论。
4. 输出查询时间、角色、服务状态、回答、引用线索和实际返回路径；无文件时路径为空。
   区分服务提供的观点、引用事实和本地推断，无法核验的内容标明未核验。

## 运行说明

- 脚本支持 query、`--no-save` 及凭据参数；自动执行使用环境变量，避免凭据进入进程参数。
- `--no-save` 仅禁止写回答文件；当前脚本仍可能创建输出目录。
- 超时以 `scripts/get_data.py` 实现为准，不使用旧说明里的多个固定耗时作为 SLA。
- 输出文件名和路径以脚本实际返回为准，不把示例时间戳当作已存在文件。
- 业务内容会提交到中金点睛服务；遵守该服务的访问及内容限制。凭据、账号和 token 不进入输出。
- 依赖见 `skill-dependencies.yaml` 的 `cicc-research-gateway`；结构校验不代表远程鉴权或服务已实测。
- 收口遵循共享库 `shared-contracts/evidence.yaml` 和 `shared-contracts/execution.yaml`。
