# Skill 审计实施状态补充

日期：2026-09-13  
范围：`F:\Thomas\SharedSKILLS`。本文件不审计、不修改 `F:\Thomas\QuantSystem\.trae`。

这份文件承接 `skill-audit-report.md`，记录首轮改进方案落地后的验收结果。原审计报告保留为基线，不在其中覆盖历史判断。

## 已落地

| 项目 | 当前结果 | 验收证据 |
|---|---|---|
| fund-wiki 研究索引入口 | SharedSKILLS 有唯一包装入口，显式要求 `--docs-root`，可指定项目后端；兼容旧版引擎缺失配置字段 | `fund-wiki-research/scripts/build_research_index.py` 临时 docs-root 端到端运行成功，返回 `status=success` |
| ODD 证据判定 | `pass/fail/insufficient_evidence/conflict` 四态统一；缺失不再默认为通过或失败；无股权/净值来源核验记录不得按“无变更/合规”处理；一票否决缺失需政策选择 | `PE_ODD_Auditor/SKILL.md`、`shared-contracts/odd-admission.yaml` |
| 定量报告入池边界 | `score==65` 为边界待复核；证据缺失、冲突、暂定分数不自动通过；风险规则按正交字段短路并有兜底 | `quant-report-qa-interpreter/SKILL.md`、`shared-contracts/quant-report-admission.yaml` |
| Skill 命名 | ODD canonical id 为 `pe-odd-auditor`，旧名 `PE_ODD_Auditor` 保留为兼容别名；FOF canonical id 与目录一致 | `skill-registry.yaml`、`skill-map.md` |
| 复盘生命周期 | `micro-retro/project-retro/meta-retro` 分层；共享经验须先登记为 `observed/proposed`，不因复盘完成自动应用 | `project-retrospective/SKILL.md`、`project-retrospective/references/output-template.md` |
| 经验登记 | 新增 `experience-registry.yaml` 与只读校验器，限制七态转换、来源数量、正反用例、应用证据和回滚记录 | `experience-registry-validator.py --selftest`：10 个用例通过 |
| Skill 资产盘点 | 新增全量 `skill-inventory.yaml`，与仅负责主路由的 `skill-registry.yaml` 分离；体检器检查两者漂移 | `scripts/build_skill_inventory.py`，当前发现 56 个 Skill |
| 统一执行结果 | 核心入口补充 `execution.yaml`，要求返回 `status/decision/evidence/limitations/unresolved/next_action` | `shared-contracts/execution.yaml`、`skill-registry.yaml` |
| 研究到组合反馈闭环 | 将目标权重、组合约束、成本假设、实际持仓、成交、PnL、归因和暂停/退役动作拆成独立门槛；提供标准库确定性校验 | `shared-contracts/investment-feedback.yaml`、`scripts/investment_feedback.py`、`tests/test_investment_feedback.py`；测试通过 |
| 评估用例 | 40 个用例均具备结构化输入、期望行为、禁止行为和输出字段，新增 ODD 证据不足边界与组合反馈边界 | `scripts/run_skill_evals.py --validate-only`：40/40 格式有效 |
| 路由决策契约 | 主入口、辅助入口、风险级别、触发依据、排除项和升级方向可由机器校验；辅助 Skill 必须由主入口声明且默认最多两个 | `shared-contracts/route-decision.yaml`、`scripts/validate_route_decision.py`、`tests/test_route_decision.py` |
| 全库角色台账 | 56 个 Skill 均在 inventory 标注 `primary/support/reference/meta` 与 `routable`，核心 registry 保持单一主入口竞争 | `skill-inventory.yaml`、`skill-registry.yaml`、`scripts/build_skill_inventory.py` |
| 外部依赖治理 | 登记 QuantSystem 模板、MyNotes、fund-wiki/zmdata 和公开网络依赖，声明提供者、缺失策略和验证方式；可报告本机可确认的缺失路径 | `skill-dependencies.yaml`、`scripts/validate_skill_dependencies.py` |
| 版本与发布清单 | 全库 56 个 Skill 获得显式初始语义版本；发布清单记录源码 revision/state、路径和 SHA-256，并校验 registry 版本一致性 | `skill-versions.yaml`、`skill-release.yaml`、`scripts/build_skill_versions.py`、`scripts/build_skill_release.py`、`scripts/validate_skill_release.py` |
| 体检器治理接入 | `skill_doctor` 现在同时执行发布清单和依赖清单校验，并把外部依赖缺失与本地 Skill 错误分开报告 | `scripts/skill_doctor.py --strict --json` |
| 行为回归登记册 | 新增 GPT-5.4+ 行为回归套件、单条运行模板与运行记录格式，区分 pending/executed/reviewed/failed；空登记明确报告为 warning，不把格式通过冒充行为通过 | `behavior-eval-registry.yaml`、`behavior-eval-run-template.yaml`、`scripts/validate_behavior_evals.py` |
| 冻结产物交付契约 | 新增投资结论型、纯格式转换、视觉表达三类交付输入 profile，明确 artifact 不可变和退回研究层规则 | `shared-contracts/delivery-input.yaml`、`scripts/validate_artifact.py` |
| 新校验器接入体检 | `skill_doctor` 已检查行为回归登记册与交付契约引用，并把未执行行为回归作为显式 warning | `skill-registry.yaml`、`scripts/skill_doctor.py` |

## 当前验证

- `python scripts/skill_doctor.py --strict --json`：`errors=[]`，`unresolved_paths=[]`，状态为 `warning`。
- `python scripts/validate_skill_release.py --json`：56/56 Skill 路径、SHA-256、版本源和核心 registry 版本一致。
- `python scripts/validate_skill_dependencies.py --json`：4 项依赖声明结构和 registry 反向引用通过；QuantSystem `docs/retrospectives` 与 MyNotes 目录在当前机器缺失，按各自 policy 报告，不伪装为可用。
- `python scripts/run_skill_evals.py --validate-only`：40 个用例格式全部通过。
- `python scripts/validate_behavior_evals.py --json`：4 个行为套件结构有效；真实运行数 0，按设计返回 warning。
- `python scripts/validate_artifact.py tests/fixtures/artifact-research.yaml --json`：冻结 research artifact 通过；非法 portfolio artifact fixture 被正确拒绝。
- `python -m pytest -q`：根目录治理测试 26 个全部通过；`pytest.ini` 已隔离各 Skill 内嵌的独立 engine/examples 测试环境。
- `python experience-registry-validator.py --selftest`：10 个语义自测全部通过。
- `python -S experience-registry-validator.py --registry experience-registry.yaml`：零第三方依赖模式下通过。
- Python 入口脚本 `py_compile` 通过，`git diff --check` 无空白错误。

## 尚未完成且不能伪装成已完成

1. **LLM 行为回归尚未执行。** 当前 40 个用例只证明格式和契约完整，`cases_behavior_executed=0`、`cases_human_reviewed=0`。仍需用实际目标模型执行路由、强推结论、材料冲突、PIT 缺失、复盘回写和组合反馈等压力场景，并保存评分结果。
2. **投资政策边界仍需人工确认。** ODD 一票否决项的 `insufficient_evidence` 采用保守风控、形式满足还是证据加权；定量报告 `score==65` 在风险等级上采用哪一种制度解释，不能由 Skill 自行决定。
3. **完整主路由覆盖仍不完整。** `skill-registry.yaml` 当前是 `core_router`，只登记核心入口；所有 56 个资产在 `skill-inventory.yaml`，但未登记 Skill 不参与自动主入口竞争。若希望事实查询、材料入库和公开数据采集也由机器路由，下一轮应增加这些入口及其优先级和 excludes。
4. **缓存与历史产物仍在源码目录。** 体检器只报告，不删除。`fof-risk-report-generator`、`fund-track-tag-audit` 等目录中的缓存/预览/历史 HTML 是否迁移或删除，需要资产保留决策后单独处理。
5. **组合与实盘反馈闭环已建立最小契约，但尚未接入 QuantSystem 运行数据。** SharedSKILLS 现在能校验目标权重、实际持仓、成交、成本、PnL、归因和暂停/退役门槛；真实组合数据、预测校准和模型退役流程仍需在 QuantSystem 中接入，不能把契约校验当成投资结果证明。
6. **SharedSKILLS 与 QuantSystem 副本尚无锁定文件。** 仍建议在 QuantSystem 内建立 `skill-lock.yaml`，记录源版本、hash、项目覆盖和同步时间；本轮按用户范围不修改 `.trae`。
7. **发布清单当前对应 dirty working tree。** `skill-release.yaml` 的 `source_state` 会明确标记为 `dirty`；它可用于内部验收和审计，不能被当作已签署的生产发布版本。

## 下一轮建议顺序

1. 用真实历史任务完成五条主线各 5 个行为压力用例，并人工评分误路由、漏门槛、伪验证和错误回写。
2. 由投资政策负责人确认 ODD 与定量报告的边界状态，形成不可歧义的制度参数。
3. 建立目标权重/实际持仓/成交/PnL/归因的统一 artifact 与 model card，再把监控结果连接到配置、暂停和退役动作。
4. 清理或迁移缓存、预览图、历史 HTML，并在 QuantSystem 侧建立版本锁定和同步检查。
5. 根据行为回归结果压缩高频入口 Skill 的第一屏，而不是继续扩充长篇自然语言规则。

本轮新增的治理脚本先作为 SharedSKILLS 内部门禁使用；尚未把任何外部依赖强行改成可用，也没有删除缓存、预览图或历史产物。

当前状态应表述为：**首轮结构和高风险规则改进已完成并通过静态/入口验证；行为有效性、投资政策确认、资产清理和组合实盘闭环仍在后续阶段。**
