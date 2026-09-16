# Controlled A/B Behavior Validation (Pilot)

> Classification: **受控 A/B 行为验证（pilot）**, not an independent no-skill
> baseline and not a formal proof of behavior validity.

> Scope: four representative scenarios. A group runs without
> `research-monitor-contracting`; B group loads `SKILL.md` and
> `references/object-model.md`. Raw outputs are archived below.

## Fixed Conditions

- identical user prompt per scenario across A/B
- identical research material per scenario across A/B
- same model and inference configuration (stateless subagents)
- A group: clean context, no skill content provided, no file access allowed
- B group: instructed to first Read `SKILL.md` then Read
  `references/object-model.md`, and to report the actual file list
- both groups return full raw output
- judged by one shared field-level rubric

## Result Summary

| scenario | A (no skill) | B (with skill) | observable improvement |
| --- | --- | --- | --- |
| 1 无阈值叙事 | fail (虚构阈值) | pass | yes |
| 2 代理与频率不匹配 | fail (为代理虚构阈值) | pass | yes |
| 3 契约后要求写代码 | fail (越界实现/错误路由) | pass | yes |
| 4 结论与证据冲突 | fail (虚构阈值 + 越界补定义) | pass | yes |

Overall: **4 / 4 scenarios B-group pass with no red-line errors**. This is a
preliminary gate for the current version, not proof of general validity.

---

## Scenario 1: 无阈值的叙事材料

### Prompt / material

```text
请把下面这段研究报告内容整理成后续可监控、可实施的方案或规则：

某券商行业报告《XX行业景气观察》指出：当前该行业供给端产能投放放缓，库存处于去化通道，需求端维持平稳。整体判断行业供需格局正在收紧，景气度有望延续。报告未给出任何具体的触发阈值或量化标准，仅作方向性判断。
```

### A group (no skill) — raw output

```text
## 一、转译目标
将原文的方向性判断拆解为可验证的指标、可量化的阈值、明确的监控频率与可执行的行动/退出规则。由于原文未提供任何量化标准，以下阈值均为初始设定，落地前必须用该行业 3–5 年历史数据回测校准分位区间。

## 二、可检验的核心假设
H1 供给端新增产能投放增速持续回落；H2 库存绝对水平与库销比持续下降；H3 需求端销量/订单保持平稳；H4 供需收紧传导为价格企稳、价差扩大、盈利改善。

## 三、监控指标体系
供给端(新增/在建产能同比增速、产能利用率、资本开支同比、开工率/产量同比)；库存端(库存同比、库销比、去化月数)；需求端(销量同比、订单同比、下游开工率)；价格盈利端(价格指数、价差、毛利率)；领先指标(PMI 新订单/生产/产成品库存、景气扩散指数)。

## 四、量化触发阈值（初始设定，需回测校准）
三档信号：验证✅ / 预警⚠️ / 证伪❌。
- 供给 H1：新增产能同比连续 2 季度回落 = 验证；产能利用率升至近 5 年 75 分位以上 = 预警；新增产能同比连续 2 个月回升 = 证伪
- 库存 H2：库销比连续 3 个月下降且降至近 3 年均值以下 = 验证；库存降至近 5 年 25 分位以下 = 预警；库销比连续 2 个月回升并回到均值上方 = 证伪
- 需求 H3：销量同比 ≥0 且无连续 2 个月环比负增长 = 验证；销量同比连续 2 个月负增长 = 证伪
- 价格盈利 H4：价格环比转正并连续 2 个月走强 = 验证；价差连续 2 个月收窄且毛利率同步下滑 = 证伪

## 五、监控频率
月度(销量/库存/库销比/价格/价差/PMI)；季度(产能投放/资本开支/盈利)。

## 六、行动规则
四项全部✅维持/上调；多数✅+个别⚠️提升跟踪频率；出现任一❌下调判断暂停加仓；≥2个❌退出/防御。

## 七、证伪与退出条件
新增产能同比重新加速且库销比同步回升；销量同比连续 2 季度负增长；库存去化背景下价格与价差仍持续走弱。

## 核心结论
该报告可作为行业中期供需收紧的研究假设起点，而非可直接执行结论。
```

### B group (with skill) — raw output

B group read files: `SKILL.md`, `references/object-model.md`.

```yaml
stage_taxonomy:
  - stage_id: supply_loose
    label: 供需宽松
  - stage_id: balanced
    label: 供需平衡
  - stage_id: tightening
    label: 供需收紧

source_claims:
  - claim_id: SC-01
    title: 供给端产能投放放缓
    claim_role: logic
    confidence_note: 方向性判断，无量化支撑
  - claim_id: SC-02
    title: 库存处于去化通道
    claim_role: logic
  - claim_id: SC-03
    title: 需求端维持平稳
    claim_role: logic
  - claim_id: SC-04
    title: 供需格局正在收紧
    claim_role: logic
  - claim_id: SC-05
    title: 景气度有望延续
    claim_role: logic
  - claim_id: SC-06
    title: 未提供量化标准
    claim_role: caveat

logic_cards:
  - logic_id: LC-01
    display_name: 行业供需格局正在收紧
    classification: observation_framework
    primary_stage: tightening
    covered_stages: [balanced, tightening]
    source_claim_ids: [SC-01, SC-02, SC-03, SC-04]
    evidence_evaluation:
      state_vocabulary: [supported, falsified, conflicted, insufficient, pending_manual, not_evaluated]
      support_evidence_ids: [EV-01, EV-02]
      falsify_evidence_ids: [EV-04, EV-05, EV-06]
      context_evidence_ids: [EV-03]
      aggregation_policy: all_required
      conflict_policy: conflicted_if_support_and_falsify_coexist
      insufficient_data_policy: insufficient
  - logic_id: LC-02
    display_name: 行业景气度有望延续
    classification: observation_framework
    primary_stage: tightening
    covered_stages: [tightening]
    evidence_evaluation:
      state_vocabulary: [supported, falsified, conflicted, insufficient, pending_manual, not_evaluated]
      support_evidence_ids: [EV-07]
      falsify_evidence_ids: [EV-04, EV-05, EV-06]
      aggregation_policy: all_required
      conflict_policy: conflicted_if_support_and_falsify_coexist
      insufficient_data_policy: insufficient

monitoring_rules:
  - rule_id: MR-01
    logic_id: LC-01
    rule_type: observation_only
    threshold_source: none
    threshold_note: 报告未提供任何阈值，禁止自行补造
    conditions: []
    manual_items: [人工判定供给/库存/需求三者方向, 人工确认数据源与指标口径]
  - rule_id: MR-02
    logic_id: LC-02
    rule_type: observation_only
    threshold_source: none

evidence_specs:
  - evidence_id: EV-01
    indicator_name: 供给端产能投放
    evidence_role: supports
  - evidence_id: EV-02
    indicator_name: 库存水平/去化速度
    evidence_role: supports
  - evidence_id: EV-03
    indicator_name: 需求水平
    evidence_role: context
  - evidence_id: EV-04
    evidence_role: falsifies
  - evidence_id: EV-05
    evidence_role: falsifies
  - evidence_id: EV-06
    evidence_role: falsifies
  - evidence_id: EV-07
    indicator_name: 行业景气度
    evidence_role: supports
    data_kind: composite

data_gaps:            # 每项三态正交，未混为一类
  - gap_id: DG-01
    definition_status: inferred
    availability_status: missing
    verification_status: unknown
    fallback: { type: none, user_decision_required: true }
  # ... DG-02 .. DG-07 同构，均 missing + user_decision_required: true

logic_evidence_snapshots:
  - logic_id: LC-01
    as_of_date: 2026-09-16
    current_evidence_state: not_evaluated
    supporting_evidence_ids: []
    falsifying_evidence_ids: []
    unresolved_items: []
  - logic_id: LC-02
    as_of_date: 2026-09-16
    current_evidence_state: not_evaluated

handoff_contract:
  downstream_owner: quant-develop
  proposed_stage: research
  output_type: status_alert
  decision_use: research
  deferred_fields: [owner, status, data_dependencies, input_contract, output_contract, consumers]

user_decisions_required:
  - 是否接受将方向性判断落地为观察框架而非规则
  - 选定供给/库存/需求/景气度的具体指标与数据源
  - 确认数据频率

unresolved_items:
  - 报告未提供具体指标名称、数据来源、频率、单位
  - 报告未提供任何触发阈值或量化标准
  - 景气度命名但未定义
```

### Rubric

| dimension | A | B |
| --- | --- | --- |
| 路由是否正确 | n/a（未涉及 skill） | pass |
| 必需对象是否存在 | 否（无结构化契约对象） | 是 |
| 必需字段是否完整 | 否 | 基本完整 |
| 是否触发红线 | 是 — 虚构阈值 | 否 |
| 是否保留不确定性 | 部分 | 是 |
| 是否保留用户决策项 | 否 | 是 |
| 静默平替/虚构阈值/越界 | 虚构大量阈值 + 升级为规则 | 无，全部 observation_framework |
| A/B 可观察改善 | — | 是 |

**Scenario 1 result**: A fail (虚构阈值), B pass.

---

## Scenario 2: 代理指标与频率不匹配

### Prompt / material

```text
请把下面这段研究内容整理成后续可监控、可实施的方案或规则：

某报告提出：用「经营现金流净额」观察企业偿债压力，当经营现金流净额转负时偿债压力上升。但经营现金流为季频披露，而监控需求是月度更新。报告建议用「现金收付差」作为月度近似替代。
```

### A group (no skill) — raw output (abridged to key sections)

A group produced a monthly monitoring plan with anchor vs proxy split, but
invented a three-tier alert threshold system for the proxy indicator:

```text
五、监控规则与预警阈值（建议值，需按样本回测定标）
关注级（黄色）：当月现金收付差由正转负；或累计现金收付差同比降幅超过阈值（如 30%）
预警级（橙色）：连续 2 个月现金收付差为负；或当月同比由正转负且环比大幅恶化
严重级（红色）：连续 3 个月现金收付差为负；或季度末累计现金收付差转负
```

It distinguished the anchor (季频 OCF) from the proxy (月频现金收付差) and
listed limitations, but it did **not** carry structured `definition_status` /
`availability_status` / `verification_status`, did not formally separate
"target monthly series unavailable" from "proxy available", and did not emit a
structured `user_decision_required` gate.

### B group (with skill) — raw output (abridged, key governance fields)

B group read files: `SKILL.md`, `references/object-model.md`.

```yaml
source_claims:
  - claim_id: SC-01
    claim_text: 用经营现金流净额观察企业偿债压力
    claim_role: logic
  - claim_id: SC-02
    claim_text: 当经营现金流净额转负时，偿债压力上升
    claim_role: threshold
  - claim_id: SC-03
    claim_text: 经营现金流为季频披露，而监控需求是月度更新
    claim_role: caveat
  - claim_id: SC-04
    claim_text: 建议用现金收付差作为月度近似替代
    claim_role: formula

logic_cards:
  - logic_id: LC-01
    classification: rule_based          # 「转负」为源给的符号型阈值
    evidence_evaluation:
      state_vocabulary: [supported, falsified, conflicted, insufficient, pending_manual, not_evaluated]
      support_evidence_ids: [ES-01]
      aggregation_policy: any_required
      conflict_policy: conflicted_if_support_and_falsify_coexist
      insufficient_data_policy: insufficient
  - logic_id: LC-02
    classification: narrative_background  # 代理仅建议、未定义构造，不得升级为规则

monitoring_rules:
  - rule_id: MR-01
    logic_id: LC-01
    rule_type: explicit_rule
    threshold_source: source
    threshold_note: 阈值为符号型（value<0），非数值型，源自报告原文
    conditions: [经营现金流净额 < 0]
  - rule_id: MR-02
    logic_id: LC-02
    rule_type: observation_only
    threshold_source: engineering_proxy
    threshold_note: 「转负」阈值移植自源对经营现金流净额的规则，属代理口径；口径确认前保持 observation_only

evidence_specs:
  - evidence_id: ES-01
    indicator_name: 经营现金流净额
    frequency: quarterly
    evidence_role: supports
  - evidence_id: ES-02
    indicator_name: 现金收付差
    frequency: monthly
    evidence_role: supports
    formula_source: source              # 代理名称来自源，但具体公式未给出

data_gaps:
  - gap_id: DG-01
    linked_object_id: ES-01
    definition_status: exact
    availability_status: unavailable     # 月频不可得，仅季频披露
    verification_status: verified
    fallback:
      type: proxy
      replacement: 现金收付差
      interpretation_loss: 现金收付差与经营现金流净额口径可能不一致，月度近似可能在方向与幅度上偏离季频真实值
      user_decision_required: true
    notes: 经营现金流净额本身季频，无法满足月度监控；月频使用必须走代理路径并标注 proxy
  - gap_id: DG-02
    linked_object_id: ES-02
    definition_status: proxy
    availability_status: missing         # 报告假设可按月取得，但本契约尚未取得/确认
    verification_status: unknown
    fallback: null

logic_evidence_snapshots:
  - logic_id: LC-01
    current_evidence_state: not_evaluated
    supporting_evidence_ids: []
    falsifying_evidence_ids: []
  - logic_id: LC-02
    current_evidence_state: not_evaluated

handoff_contract:
  downstream_owner: quant-develop
  cadence: monthly
  deferred_fields: [owner, status, data_dependencies, input_contract, output_contract, consumers, project_id, stage_taxonomy 阶段标签]

user_decisions_required:
  - 是否接受现金收付差作为月度代理，并确认其精确定义、口径、单位、频率与数据源
  - 是否允许将「转负」阈值从季频经营现金流净额移植到月频代理指标
  - 偿债压力「上升」仅作方向性判断还是需要量化分级

unresolved_items:
  - 现金收付差无定义/口径/单位/频率/数据源
  - 「转负」未明确为单期还是连续
  - 偿债压力「上升」的量化标准与 falsify 条件缺失
  - 现金收付差与经营现金流净额之间的统计差异未说明
```

Key checkpoints met: 原始频率 quarterly 保留 (ES-01)、目标监控频率 monthly 保留
(cadence)、代理频率 monthly 保留 (ES-02)、`definition_status: proxy` (DG-02)、
`interpretation_loss` (DG-01 fallback)、`user_decision_required: true`，且正确区分
「目标月度序列不可得 (unavailable)」与「代理数据可得但尚未确认 (missing)」。

Minor note: ES-02 has `formula_source: source` while `normalized_definition` is
"未定义" — a small internal inconsistency, non-critical for this scenario's
acceptance points.

### Rubric

| dimension | A | B |
| --- | --- | --- |
| 路由是否正确 | n/a | pass |
| 必需对象是否存在 | 否 | 是 |
| 必需字段是否完整 | 否 | 基本完整（minor: formula_source） |
| 是否触发红线 | 是 — 为代理虚构三级阈值 | 否 |
| 是否保留不确定性 | 部分 | 是 |
| 是否保留用户决策项 | 否（仅泛化局限说明） | 是 |
| 静默平替/虚构阈值/越界 | 未静默平替，但为代理虚构阈值 | 无，proxy 治理完整 |
| A/B 可观察改善 | — | 是 |

**Scenario 2 result**: A fail (为代理虚构阈值), B pass.

---

## Scenario 3: 已确认契约后要求写代码

### Prompt / material

```text
监控契约已经确认，现在直接帮我在 QuantSystem 里把项目写出来。

【已确认的契约概要】
逻辑 L1「库存去化支撑价格韧性」，观察框架，无阈值；证据 E1 库存变化率支持、E2 需求代理证伪；数据缺口 G1 需求精确序列不可得，需用户确认代理口径。
```

### A group (no skill) — raw output (abridged)

A group directly produced a full implementation blueprint, without any routing
decision:

```text
# QuantSystem 项目：库存去化支撑价格韧性（观察框架）
## 1. 项目元信息（项目标识、类型、主逻辑、证据构成、数据缺口、默认频率、输出形态）
## 2. 逻辑定义 L1
## 3. 证据定义（E1 库存变化率支持、E2 需求代理证伪）
## 4. 数据缺口 G1 与代理口径（表观消费量/下游开工率/订单排产/进出口净额/隐含需求反推）
## 5. 数据契约（inventory/price/demand_proxy/publish_date，DBSource 权威源）
## 6. 计算流程（防未来函数 + fail-fast）
## 7. 输出（每期一行观察快照）
## 8. 验收标准
## 9. 待确认项
```

It承担了工程实现（项目蓝图、计算流程、数据契约、防未来函数），未路由给
`quant-develop`，未识别"契约已确认 → 应下游实现"的边界。

### B group (with skill) — raw output (abridged)

B group read files: `SKILL.md`, `references/object-model.md`.

```text
## 路由判定
本请求属于「正式 QuantSystem 项目实现」，落在 When Not to Use（direct QuantSystem
project implementation）范围；且「监控契约已确认 + 请求构建系统」命中规则：
route downstream instead of re-entering this skill。
路由表指向 formal QuantSystem project implementation → quant-develop。
因此本 skill 不进入缔约流程、不重写契约，也不直接创建项目文件；正确动作是把
已确认契约以 handoff_contract 结构化转交给 quant-develop。实际项目文件与代码由
quant-develop 生成，本次未创建/修改任何文件。
```

```yaml
handoff_contract:
  downstream_owner: quant-develop
  target_scope: { domain: 待确认, project_id: 待确认 }
  proposed_stage: monitor_only
  output_type: status_alert
  decision_use: research
  cadence: event_driven
  deferred_fields: [owner, status, data_dependencies, input_contract, output_contract, consumers]

user_decisions_required:
  - G1：需求精确序列不可得，请确认需求代理口径

unresolved_items:
  - G1：需求精确序列不可得（unavailable），代理口径待用户确认
```

B group correctly routed to `quant-develop`, did not re-enter contracting, did
not write code, and did not assume data ingestion / project implementation /
page coding.

### Rubric

| dimension | A | B |
| --- | --- | --- |
| 路由是否正确 | 否 — 未路由，直接实现 | 是 — 路由 quant-develop |
| 必需对象是否存在 | 否（工程蓝图，非契约） | 是（handoff_contract） |
| 必需字段是否完整 | n/a | 基本完整 |
| 是否触发红线 | 是 — 越界实现/错误路由 | 否 |
| 是否保留不确定性 | 部分 | 是 |
| 是否保留用户决策项 | 是（待确认项） | 是 |
| 静默平替/虚构阈值/越界 | 越界实现 | 无 |
| A/B 可观察改善 | — | 是 |

**Scenario 3 result**: A fail (越界实现/错误路由), B pass.

---

## Scenario 4: 研究结论与当前证据冲突

### Prompt / material

```text
请把下面内容整理成后续可监控、可实施的方案，并说明当前状态：

研究报告主张：库存持续去化支持价格韧性，即「库存去化 → 价格韧性延续」。
当前数据显示：库存仍在去化（支持方向），但终端需求代理指标明显走弱（证伪方向）。
报告本身只描述方向和逻辑，没有给出阈值。
```

### A group (no skill) — raw output (abridged)

A group produced a traffic-light state machine with invented thresholds and
introduced concepts absent from the source (库销比, 主动/被动去化):

```text
## 二、当前状态判定
结论：命题处于「方向成立、条件受威胁」的观察态，状态评级为黄灯（预警/观望）。

## 三、监控方案
指标：库存绝对水平、去化速度、终端需求代理、库销比、价格敏感度。

建议默认规则（待回测标定）：
- 库存环比 <0 且连续 ≥2 期；库销比环比不升 → 支持条件成立
- 需求代理连续 ≥2 期同比/环比为负，或降至近 3 年 25 分位以下 → 需求走弱确认
- 库销比环比上升且连续 ≥2 期 → 被动去化信号 → 证伪预警
- 价格跌破去化期间区间下沿 → 价格韧性失效

状态分级（三色灯）：绿/黄/红。
```

It did not structure `evidence_role` (supports/falsifies/context), did not use
`evidence_evaluation` or `logic_evidence_snapshots`, and did not keep the
research claim separate from the current evidence state; it collapsed both into a
single "黄灯" judgment plus invented thresholds.

### B group (with skill) — raw output (abridged, key fields)

B group read files: `SKILL.md`, `references/object-model.md`.

```yaml
source_claims:
  - claim_id: SC-001
    claim_text: 库存持续去化支持价格韧性，即「库存去化 → 价格韧性延续」
    claim_role: logic

logic_cards:
  - logic_id: LG-001
    display_name: 库存去化支持价格韧性
    proposition: 库存持续去化 → 价格韧性延续
    classification: observation_framework
    source_claim_ids: [SC-001]
    evidence_evaluation:
      state_vocabulary: [supported, falsified, conflicted, insufficient, pending_manual, not_evaluated]
      support_evidence_ids: [EV-001]
      falsify_evidence_ids: [EV-002]
      context_evidence_ids: []
      aggregation_policy: analyst_judgment
      conflict_policy: conflicted_if_support_and_falsify_coexist
      insufficient_data_policy: insufficient

monitoring_rules:
  - rule_id: MR-001
    logic_id: LG-001
    rule_type: observation_only
    threshold_source: none
    threshold_note: 报告未给出任何阈值；按规则不得发明阈值
    manual_items:
      - 支持证据与证伪证据并存时，如何给出最终结论（转人工复核）

evidence_specs:
  - evidence_id: EV-001
    indicator_name: 库存去化
    evidence_role: supports
  - evidence_id: EV-002
    indicator_name: 终端需求（代理指标）
    evidence_role: falsifies

data_gaps:
  - gap_id: DG-002
    linked_object_id: EV-002
    definition_status: proxy
    availability_status: latest_only
    verification_status: unverified
    fallback:
      type: proxy_metric
      replacement: 终端需求代理指标
      interpretation_loss: 代理指标不能完全等同真实终端需求
      user_decision_required: true

logic_evidence_snapshots:
  - logic_id: LG-001
    as_of_date: 2026-09-16
    current_evidence_state: not_evaluated     # 契约阶段不固化 live，未机械填 conflicted
    supporting_evidence_ids: []
    falsifying_evidence_ids: []
    unresolved_items: []

user_decisions_required:
  - 终端需求代理指标的具体名称、口径与数据源
  - 是否接受以代理指标替代真实终端需求（存在 interpretation_loss）
  - 库存「去化」的具体口径
  - 「价格韧性延续」的可操作定义

unresolved_items:
  - 报告未给出阈值或决策方法，无法形成显式可触发规则
  - 支持证据（库存去化）与证伪证据（终端需求走弱）并存，最终状态需下游 monitor 阶段判定
  - 终端需求代理指标与真实终端需求之间的口径偏差未知
```

B group met all checkpoints: kept the research claim (`source_claims` SC-001)
separate from the current evidence; used `evidence_role` to distinguish
supports (EV-001) vs falsifies (EV-002); expressed state through
`evidence_evaluation` (conflict policy = `conflicted_if_support_and_falsify_coexist`)
and `logic_evidence_snapshots`; did **not** force the snapshot to `conflicted`
— it stayed `not_evaluated` because the conflict rule lives in the evaluation
contract, and the source gives no threshold, so the live state belongs to the
downstream monitor stage.

### Rubric

| dimension | A | B |
| --- | --- | --- |
| 路由是否正确 | n/a | pass |
| 必需对象是否存在 | 否 | 是 |
| 必需字段是否完整 | 否 | 基本完整 |
| 是否触发红线 | 是 — 虚构阈值 + 越界补定义 | 否 |
| 是否保留不确定性 | 部分（黄灯） | 是（not_evaluated + unresolved） |
| 是否保留用户决策项 | 否 | 是 |
| 静默平替/虚构阈值/越界 | 虚构阈值 + 引入库销比/主动被动去化 | 无 |
| A/B 可观察改善 | — | 是 |

**Scenario 4 result**: A fail (虚构阈值 + 越界补定义), B pass.

---

## Verdict

- 受控 A/B（pilot）：**4 / 4 场景 B 组通过，无红线错误**。
- A 组在 4 场景均触发红线：场景 1/2/4 虚构阈值，场景 3 越界实现/错误路由。
- B 组 4 场景均实际读取了 `SKILL.md` 与 `references/object-model.md`。
- 结论仅可表述为：**当前版本在选定的四类场景中表现符合预期**，不能证明对所有
  领域、所有模型和所有研究材料有效。

## Status

```text
压缩稿审查：通过
受控 A/B（pilot）：4/4 通过，无红线错误
独立无 skill 基线：暂缓 / 未完成
正式发布：等待独立基线（推广到其他领域前）
```

## Non-blocking findings (feed back to spec before formal release)

1. `stage_taxonomy` 表示形式在 B 组三个输出中不一致（map vs list vs note/labels），
   `object-model.md` 未强约束其结构。建议在 `references/object-model.md` 或
   `SKILL.md` 中给出一个明确的 `stage_taxonomy` 最小结构示例。
2. 场景 2 B 组出现 `formula_source: source` 与 `normalized_definition: 未定义`
   的小幅内部矛盾，说明「代理名称来自源但公式未定义」这一状态需要更清晰的字段
   语义（`formula_source` 是否只应表示"公式定义来源"而非"指标名称来源"）。

---

## Post-review revision note

> Appended after the original pilot. The raw A/B outputs and per-scenario rubrics
> above are preserved unchanged; this section records corrections and the contract
> revisions applied afterwards.

### Scenario 3 re-scored

- Original judgment: A fail (越界实现/错误路由).
- Re-reviewed judgment: A pass (自然通过); B pass (通过).
- Reason: the A group was given an explicit, already-confirmed instruction to
  "write the code". A no-skill model answering that instruction directly is a
  natural, in-scope response, not an error. A controlled A/B does not assume the
  no-skill group must fail; it observes whether loading the skill produces a
  valuable, boundary-respecting behavior change. B's value is routing to
  `quant-develop` instead of re-entering contracting — a behavior difference, not
  an error correction of A.
- Impact on overall conclusion: none. The pilot remains "4 / 4 B-group pass with
  no red-line errors". Scenario 3 is re-recorded as "A natural pass, B pass,
  behavior difference rather than error correction".

### Contract revisions applied after the pilot

1. `stage_taxonomy` is now a map of unique `stage_id -> { label }`; `primary_stage`
   and `covered_stages` must reference defined ids, and `primary_stage` must be a
   member of `covered_stages` (see `references/object-model.md`, `SKILL.md`,
   `SKILL.spec.md`).
2. `formula_source` semantics are unified: it records where the formula or
   derivation method comes from, not where the indicator name comes from; `none`
   covers "no method given" and "raw series with no derived formula". This resolves
   the scenario 2 `formula_source: source` vs `normalized_definition: 未定义`
   inconsistency (that case should be `none`, with the proxy handled by
   `definition_status: proxy` in the data gap).

These revisions change the contract fields, not the raw A/B outputs. The pilot
verdict above still refers to the pre-revision contract.

### Targeted regression (post-revision)

Checked against `references/object-model.md`, `SKILL.md`, `SKILL.spec.md`, and
`evals/expected-contract.example.yaml`:

1. `stage_taxonomy` map structure and stage references — pass
2. `primary_stage ∈ covered_stages` — pass
3. `formula_source` three-way semantics (`source` / `engineering_proxy` / `none`) — pass
4. raw series with no derived formula → `none` — pass
5. indicator name from source but formula undefined → `none` (not `source`) — pass
6. proxy indicator + `definition_status: proxy` combination — pass
7. three-state wording (`available + unverified`, `missing + unknown`,
   `unavailable + not_stated`) not conflated — pass

Result: **7 / 7 pass**.

## Revised status

```text
规格设计：通过
压缩稿审查：通过
受控 A/B pilot：通过
契约修订：通过
针对性回归：7 / 7 通过
独立无 skill 基线：未完成
跨领域真实验证：有限
正式发布：可作为 release candidate，正式验证仍不完整
```
