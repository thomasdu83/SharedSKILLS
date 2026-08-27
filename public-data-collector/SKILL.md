---
name: public-data-collector
description: 当需要从互联网公开免费源获取金融/宏观数据，且目标数据在数据库（DBSource）与 zmdata 均不可获取时使用。覆盖首次接入新源/新系列的交互式契约建立流程，以及已接入系列的日常采集执行。不用于内部数据库或 zmdata 已有的数据。
---

# 公开数据采集（public-data-collector）

## 触发边界（必须先判断）

本 skill 只在**互联网公开数据为唯一来源**时启动。任何获取动作前执行步骤 0：

1. 先在数据库（DBSource）与 zmdata 中核查目标数据是否可得（可用 zmdata-data-api 等内部能力核验）。
2. 内部可得 → 改走内部源，本流程终止，并向用户声明实际来源。
3. 内部不可得 → 才进入本 skill 流程。

## 流程 A：首次接入（新源或新系列）

1. 内部可得性检查（见上）。
2. 需求确认：指标用途、所需系列、频率、历史深度、下游消费者。
3. 源核验：对照 `references/source_vetting_checklist.md` 逐项核验候选源，记录结论。
4. 契约草案：按 `references/contract_template.yaml` 起草/更新 `config/{source}_config.yaml`。
5. 用户确认契约（免费性、字段映射、代理与密钥、vintage 取舍）。
6. 实现或扩展采集模块（QuantSystem: `platform/data/data_sources/api接口/`，含测试）。
7. 验收：全量入库 + 幂等复跑 + 空值处理日志抽查。

## 流程 B：日常获取（已接入系列）

1. 内部可得性检查（见上）。
2. 读契约确认系列已接入；未接入 → 转流程 A。
3. 执行采集：

   python platform/data/data_sources/api接口/macro_collector.py --source {source} [--series KEY ...] [--full]

4. 报告：成功/失败/跳过计数、写入行数、丢弃空值数、实际来源与代理使用情况。

## 硬性规则

- 缺失数据不补零、不补默认值；只丢弃并记 warning。
- 密钥（如 FRED_API_KEY）与代理（QUANT_HTTP_PROXY）走环境变量，不进 git、不写死进契约。
- 单系列失败不阻断其余系列；最终必须有汇总报告。
- 契约是唯一事实来源：新增系列先改契约，再（如需）改代码。
