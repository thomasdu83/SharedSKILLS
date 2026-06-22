# Decision Rules

## Separation Principle

Always separate:

- `display portrait`: richer description derived from documents
- `audit target`: current `zmdata` track/tag metadata

Do not audit every document detail. Audit only fields that belong to maintained structured metadata.

## Recommended Information Model

- `L1`: primary track
- `L2`: secondary track
- `L3`: tertiary track
- `assets`: tradable assets, sectors, or sleeves
- `strategy`: strategy composition
- `risk`: volatility bucket or risk-control features

Typical examples:

- `L1`: CTA
- `L2`: 主观CTA
- `L3`: 趋势增强 / 主观套利 / 强弱对冲
- `assets`: 黑色 / 农产品 / 化工 / 有色
- `risk`: 中波动 / 次高波动

## What To Audit

First version should focus on:

- primary track
- volatility bucket
- core track-related tags

Use field-level conclusions:

- `strategyType`: audit only the primary strategy class.
- `raceName`: audit secondary track or cycle mismatch, but only recommend a concrete value after confirming the controlled vocabulary.
- `fundType`: audit volatility bucket only when evidence maps to an internal threshold or a clearly supported bucket.

## What To Display But Not Force Into Audit

- detailed asset coverage
- internal strategy mix ratios
- risk-control process details
- narrative manager commentary
- `labelIDs`: zmdata 系统内置多层标签树（分类层级 + 赛道 + 标尺库 + 内部标注），随基金数据自动同步，非人工维护字段。报告中在「基金记录（zmdata）」和「策略画像 → 标签映射」中展示，不纳入字段审核。

These can support a recommendation but should not become automatic tag changes unless the mapping is explicit.

## Record Handling

- keep `尽调` and `投后子基金` records separate
- if the same fund appears twice, audit each record against its own `zmdata` baseline
- do not merge a `尽调` benchmark with a `投后子基金` benchmark
- treat `匿名` manager records as candidates, not as proof of duplication. Use `疑似重复，需核验` unless fund ID/code proves identity.

## Outcome Labels

### 整体审核结论

- `一致` — 所有字段与证据吻合
- `建议补充展示` — 字段正确但文档画像更丰富，可补充展示口径
- `部分待修正` — 部分字段缺失或与证据不一致但不存在根本定性冲突
- `建议修改` — 字段值与多份高质量证据冲突
- `证据不足` — P1 弱或无
- `人工复核` — 信息不确定或存在矛盾

### 字段审核结论词

在「字段审核」表中使用的结论词：

- `一致` — 字段值与证据吻合
- `需补充` — 字段为空，文档有明确候选口径
- `需修正` — 字段非空但与证据冲突
- `需复核补充` — 字段为空，候选口径需数据侧确认后填入
- `人工复核` — 无法从文档中确定，或受控词表未覆盖

**raceName 专用约束：**
- 必须给出唯一首选建议。如证据确实无法区分两个候选标签，结论写「需复核补充」，并在「依据与说明」中说明两个候选标签的差异和取舍条件，将完整论证移至口径说明。

**fundType 专用约束：**
- 仅在目标产品有直接 P1 证据且波动层级可从材料合理推断时，才可给出具体候选值（如 `CTA_中波动`）。
- 当证据来自同系列推断或存在基准/杠杆不一致等混杂因素时，结论写「需复核补充（待人工确认）」，不给候选值。

## 证据链小结写作规则

证据链小结（关键证据章节末尾 📌 部分）必须回答两个核心问题：

1. **证据的时间线/逻辑线如何支撑或削弱审核结论**——例如："2025 年 9–10 月密集调研该系列 → 年底调研重心转向其他产品线 → 侧面印证当前缺少最新独立材料"。
2. **核心不确定性来自哪里**——缺少独立尽调材料、调研重心转移、基准体系变化、同系列产品间策略可能存在差异等。

严禁将证据链小结写成证据清单的压缩版或简单重复。仅当证据在时间/策略线上有演进关系时必写；单份证据时可省略。

## Confidence Rules

- `高`: multiple strong `P1` files aligned
- `中`: only one clear `P1` source or partial support
- `低`: weak manager-level inference only

## Same-Series Evidence Attenuation

当审核产品的证据全部来自同管理人同系列其他产品（非目标产品直接材料）时：

- 证据强度**自动降一级**：「高」→「中」，「中」→「低」。
- 字段审核结论优先使用「**需复核补充**」而非「需补充」，以表明候选口径来自间接推断，需数据侧二次确认。
- 在「口径说明」中明确标注「间接证据」，说明同系列产品名称及推断依据。
- 仅在目标产品存在至少一份 P1 直接材料时，不触发衰减规则。
- 当触发衰减规则后，`fundType` 的审核结论必须采用「**需复核补充**」，且不应给出具体候选波动层级。应在「依据与说明」中说明前置条件（如"需结合投后实际净值波动率在 CTA 波动序列中定档"），而非给出类似 `CTA_中波动` 的具体候选值。
