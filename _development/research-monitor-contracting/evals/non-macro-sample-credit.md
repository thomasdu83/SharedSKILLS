# Non-Macro Schema Fixture: Credit / Operating Metric

> Purpose: prove the object model can express a credit / operating-metric scenario
> beyond macro/gold. This is a **synthetic schema fixture（领域中立结构化样例）**,
> not a real external source sample. It validates structural expressiveness only,
> not source authenticity, locator reliability, or real-world ambiguity handling.

## Fixture Source (synthetic, illustrative)

- domain: credit / corporate short-term solvency
- nature: synthetic schema fixture; not a real external source sample
- source: 某券商《制造业企业信用风险观察：现金转换压力》专题（虚构）
- date: 2026-08-20
- locator convention: page / section / paragraph

### Input fragments

| page | section | paragraph | content |
| --- | --- | --- | --- |
| 7 | 偿债压力判断 | 2 | 应收账款周转天数持续上升、且经营性现金流净额转负时，企业短期偿债能力承压。 |
| 8 | 指标观察 | 1 | DSO 上升反映销售回款放缓；经营现金流转负说明利润未转化为现金。 |
| 8 | 指标观察 | 3 | 速动比率仍高于 1 时，短期偿债压力可被部分对冲。 |
| 9 | 数据说明 | 1 | 经营性现金流为季频披露，月度监控需以现金收付差近似。 |

## Field-Level Mapping

| input structure | standard object | mapping decision | gap / note |
| --- | --- | --- | --- |
| 偿债压力判断 (p7/s2) | `logic_card` | `classification: observation_framework`；`primary_stage: assessment`；`covered_stages: [assessment]` | 无阈值，不得升级为 `rule_based` |
| DSO 指标 (p8/s1) | `evidence_spec` | `evidence_role: supports` | `definition_status: exact`（口径明确） |
| 经营性现金流净额 (p8/s1) | `evidence_spec` | `evidence_role: supports` | 季频披露，月度口径需代理 |
| 速动比率 (p8/s3) | `evidence_spec` | `evidence_role: falsifies` | 同一逻辑同时存在支持与证伪角色 |
| 现金流季频、需月度 (p9/s1) | `data_gap` | `definition_status: proxy`；`availability_status: unavailable`；`verification_status: verified` | fallback=现金收付差，需用户确认 |

## Resulting Objects (abbreviated)

```yaml
source_claims:
  - claim_id: claim_001
    source_type: report
    source_title: 制造业企业信用风险观察：现金转换压力
    source_author_or_org: 某券商
    source_date: "2026-08-20"
    locator: { page: 7, section: 偿债压力判断, paragraph: 2 }
    claim_text: 应收账款周转天数持续上升、且经营性现金流净额转负时，企业短期偿债能力承压。
    claim_role: logic
    confidence_note: 单一来源，方向性描述，未给出统计检验。

  - claim_id: claim_004
    source_type: report
    source_title: 制造业企业信用风险观察：现金转换压力
    source_author_or_org: 某券商
    source_date: "2026-08-20"
    locator: { page: 9, section: 数据说明, paragraph: 1 }
    claim_text: 经营性现金流为季频披露，月度监控需以现金收付差近似。
    claim_role: caveat
    confidence_note: 数据口径限制，明确披露。

logic_cards:
  - logic_id: receivable_cash_stress
    display_name: 现金转换压力下的短期偿债能力
    proposition: 当应收账款周转天数持续上升且经营性现金流净额转负时，企业短期偿债能力承压。
    mechanism: DSO 上升意味着销售回款放缓、营运资金占用增加；经营现金流转负说明账面利润未转化为现金流入，短期偿债资金来源被削弱。
    implication: 若两者同时恶化则下调偿债能力判断；若速动比率健康或现金流改善则压力缓解。
    applicability_boundary: 适用于应收账款与经营现金流均可观察的制造业企业。
    failure_mode: 若行业结算模式变化或现金流受一次性项目干扰，逻辑解释力下降。
    classification: observation_framework
    primary_stage: assessment
    covered_stages: [assessment]
    source_claim_ids: [claim_001, claim_004]
    evidence_evaluation:
      state_vocabulary: [supported, falsified, conflicted, insufficient, pending_manual, not_evaluated]
      support_evidence_ids: [dso, operating_cash_flow]
      falsify_evidence_ids: [quick_ratio]
      context_evidence_ids: []
      aggregation_policy: all_required
      conflict_policy: conflicted_if_support_and_falsify_coexist
      insufficient_data_policy: insufficient

monitoring_rules:
  - rule_id: rule_receivable_cash_stress
    logic_id: receivable_cash_stress
    rule_type: observation_only
    decision_direction: stress_when_dso_rising_and_ocf_negative
    aggregation_method: analyst_judgment
    threshold_source: none
    threshold_note: 研报只描述方向性组合信号，未给出 DSO 或现金流的具体触发阈值。
    conditions: []
    falsifiers: [quick_ratio_healthy]
    manual_items:
      - DSO 上升幅度与现金流负值程度是否已构成实质压力需人工判断
    state_mapping:
      triggered: 观察支持
      not_triggered: 观察未支持
      pending_manual: 待人工确认
      insufficient: 证据不足

evidence_specs:
  - evidence_id: dso
    logic_id: receivable_cash_stress
    linked_rule_ids: [rule_receivable_cash_stress]
    indicator_name: 应收账款周转天数
    evidence_role: supports
    data_kind: derived_series
    source_label: 应收账款周转天数
    normalized_definition: 应收账款周转天数（DSO）
    transform: level
    unit: days
    frequency: quarterly
    required_date_semantics: 截至季度末
    formula_source: source
    implemented_formula_note: 需确认统计口径与披露滞后。
    threshold_reference: 无明确阈值
    automation_status: automated

  - evidence_id: operating_cash_flow
    logic_id: receivable_cash_stress
    linked_rule_ids: [rule_receivable_cash_stress]
    indicator_name: 经营性现金流净额
    evidence_role: supports
    data_kind: series
    source_label: 经营性现金流净额
    normalized_definition: 经营活动产生的现金流量净额
    transform: level
    unit: currency
    frequency: quarterly
    required_date_semantics: 截至季度末
    formula_source: source
    implemented_formula_note: 季频披露，月度监控需代理口径。
    threshold_reference: 无明确阈值
    automation_status: semi_automated

  - evidence_id: quick_ratio
    logic_id: receivable_cash_stress
    linked_rule_ids: [rule_receivable_cash_stress]
    indicator_name: 速动比率
    evidence_role: falsifies
    data_kind: series
    source_label: 速动比率
    normalized_definition: 速动资产 / 流动负债
    transform: ratio
    unit: ratio
    frequency: quarterly
    required_date_semantics: 截至季度末
    formula_source: source
    implemented_formula_note: 需确认速动资产口径。
    threshold_reference: 研报以 1 为参考
    automation_status: automated

data_gaps:
  - gap_id: gap_ocf_monthly
    linked_object_type: evidence_spec
    linked_object_id: operating_cash_flow
    definition_status: proxy
    availability_status: unavailable
    verification_status: verified
    source_attempts:
      - source: quarterly_ocf
        result: available
        reason: 季频披露，频率不满足月度监控
      - source: monthly_ocf
        result: unavailable
        reason: 原始月频经营现金流序列不存在
    fallback:
      type: proxy
      replacement: 月度现金收付差
      interpretation_loss: 现金收付差无法完整区分经营、投资、筹资活动，只能近似反映经营现金变动方向。
      user_decision_required: true
    notes: 若用户不接受月度代理口径，则该证据只能降级为季频观察。

logic_evidence_snapshots:
  - logic_id: receivable_cash_stress
    as_of_date: "2026-09-16"
    current_evidence_state: conflicted
    supporting_evidence_ids: [dso, operating_cash_flow]
    falsifying_evidence_ids: [quick_ratio]
    unresolved_items:
      - 速动比率改善与现金流恶化方向冲突

handoff_contract:
  downstream_owner: quant-develop
  target_scope:
    domain: credit
    project_id: receivable-cash-stress-monitor
  proposed_stage: monitor_only
  output_type: status_alert
  decision_use: internal_decision
  cadence: monthly
  required_entrypoints:
    research: false
    publish: false
    monitor: true
  deliverables:
    - logic_card implementation scaffold
    - evidence pipeline placeholders
    - manual-review field support
  implementation_constraints:
    - 不得将月度现金收付差标记为原始经营现金流
    - 不得为观察框架强行补阈值
    - 阶段名称必须可配置
  acceptance_checks:
    - 逻辑对象可显示 proposition、mechanism、implication
    - evidence role 支持 supports 与 falsifies 区分
    - proxy 状态在页面或接口中可见
    - unresolved items 不得丢失
  deferred_fields:
    - owner
    - status
    - data_dependencies
    - input_contract
    - output_contract
    - consumers

user_decisions_required:
  - 是否接受月度现金收付差作为经营现金流的代理口径

unresolved_items:
  - DSO 与经营现金流的组合触发阈值缺失，当前仅能形成观察框架
  - 原始月频经营现金流序列尚未确认
```

## Time-Semantics Note (for pressure validation)

The fixture exposes a frequency mismatch that the current object model does not
split into explicit fields:

```yaml
source_frequency: quarterly                # 研究资料中的经营现金流频率
requested_monitoring_frequency: monthly    # 目标监控频率
fallback_frequency: monthly                # 现金收付差代理的频率
```

This is intentionally **not** added as a new object-model field yet. It is a
pressure-validation checkpoint: the formal skill must prevent a downstream reader
from believing `evidence_spec.frequency: quarterly` already satisfies the monthly
monitoring cadence. The monthly proxy（现金收付差）is a separate fallback whose
frequency must not be confused with the source frequency. `availability_status:
unavailable` describes the target monthly series being unobtainable, not that all
related data（例如现金收付差代理）is absent.

## Handoff Allowance

- allowed: yes — single-stage logic, observation framework, and proxy/missing data
  are all expressible with the current objects.
- required `deferred_fields`: `owner`, `status`, `data_dependencies`, `input_contract`,
  `output_contract`, `consumers`.
- `user_decisions_required`: whether to accept the monthly cash-receipt proxy.

## Generality Judgement

| feature under test | result |
| --- | --- |
| single-stage logic | expressible via `primary_stage` / `covered_stages` |
| observation framework | expressible via `classification: observation_framework` |
| proxy / missing data | expressible via `definition_status` / `availability_status` |
| support + falsify roles | expressible via `evidence_role` |
| source traceability | expressible via `locator` (page / section / paragraph) |
