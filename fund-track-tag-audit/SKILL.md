---
name: fund-track-tag-audit
description: Audit and compare fund track/tag metadata in zmdata against fresher due-diligence evidence. Use when the user asks to verify whether one or more funds' zmdata赛道/标签/波动层级 are stale, need revision, or should be supplemented with richer multi-level track descriptions from manager due-diligence files.
---

# Fund Track Tag Audit

## Overview

This skill audits a fund's current `zmdata` track and tag metadata against evidence from:

- Due-diligence materials: workspace folder matching `投顾信息（PPT、尽调反馈表等）`

The skill now operates as a **native LLM tool-chain workflow**. It uses Trae/IDE built-in tools (Glob, LS, Read, SearchCodebase) instead of a heavy Python SMB pipeline. Evidence folders must be added to the current workspace before the audit can proceed.

Always separate:

- `display`: richer track portrait from documents, which may include L2/L3 tracks, assets, strategies, and risk-control traits
- `audit`: whether existing `zmdata` track/tag fields should be revised

## First-Time Setup (触发条件：用户明确表示首次使用本 Skill)

当用户说「首次使用 fund-track-tag-audit」「首次使用基金标签审核」「第一次用这个 skill」「怎么设置这个 skill」等类似表达时，**先不执行审计流程**，直接返回以下设置清单，并在清单末尾询问用户是否已完成设置、是否要继续审计。

### 必须
1. .trae/skills/zmdata-data-api/ 已存在
2. **安装 zmdata Python SDK**
   ```
   pip install zmdata -i http://10.168.30.14:8081/repository/flare-custom/simple --trusted-host 10.168.30.14
   ```
   或者使用zmdata-data-api这个技能安装zmdata
3. **映射网络盘符 W:\**（尽调材料源）加入工作区
   - UNC 路径：`\\10.168.20.10\投顾信息（PPT、尽调反馈表等）\`
4. **映射网络盘符 Y:\**（共享报告库）加入工作区
   - 目标：`Y:\投顾管理人研究\fund-track-tag-audit\`

### 可选

4. `pip install pdfplumber python-docx`（仅当尽调材料含 PDF/DOCX 时需要）
5. 安装 [pandoc](https://pandoc.org)（仅当 DOCX 提取且不用 `python-docx` 备选时需要）

### 验证

```powershell
Test-Path "W:\投顾信息（PPT、尽调反馈表等）"
Test-Path "Y:\投顾管理人研究\fund-track-tag-audit"
python -c "import zmdata; print(zmdata.__version__)"
```

### 说明

- 配套 Skill（`zmdata-data-api`、`pdf`、`docx`、`pptx`、`xlsx`）已内置在 Trae IDE 中，无需额外安装。
- 最小可用配置仅需第 1–3 步（zmdata + 两个盘符）。
- 设置完成后说「继续审计」即可进入正常流程。

### 处理规则

- 用户确认已完成设置 → 继续正常审计流程（Pre-Phase → Phase 0 → …）。
- 用户表示设置遇到问题 → 协助排查。
- 用户未明确回复是否完成 → 等待用户确认，不自动继续。

## Runtime Variables (MANDATORY)

为保证该 skill 可在不同成员的本地仓库路径和 Python 环境下复用，所有 Python 命令都必须先解析以下运行时变量，禁止将某个人机器上的绝对路径写死到执行命令中。

- `$WORKSPACE_ROOT`: 当前工作区中包含 `.trae\skills\fund-track-tag-audit` 的仓库根目录
- `$SKILL_ROOT = Join-Path $WORKSPACE_ROOT ".trae\skills\fund-track-tag-audit"`
- `$REPORT_BUFFER = Join-Path $SKILL_ROOT "latest_report.md"`
- `$PYTHON_EXE`: 按以下顺序解析
  1. 用户显式提供的 Python 解释器路径
  2. `Join-Path $WORKSPACE_ROOT ".venv\Scripts\python.exe"`（若存在）
  3. 当前终端可用且已安装 `zmdata` 的 `python`

### Python Interpreter Policy

- 优先使用当前仓库自己的 `.venv`，但不得假定仓库一定位于 `F:\Thomas\QuantSystem`。
- 若未找到可用解释器，必须停止并告知用户缺少 Python 环境或依赖，而不是继续执行后续审计步骤。
- 后续所有脚本命令统一使用 `$PYTHON_EXE`；脚本内部如再调用子脚本，应继续沿用 `sys.executable`，避免跨环境漂移。

## Execution Constraints (MANDATORY)

**尽调材料目录是只读证据源，严禁改动。**

- 严禁对尽调材料所在目录执行写入、编辑、删除、移动、重命名、覆盖、格式转换覆盖、批量清理等操作。
- 只允许对证据源执行列目录、读取、搜索、抽取文本等只读操作；派生报告只能写入共享报告库或系统临时目录。
- 受保护证据源包括但不限于：
  - `W:\投顾信息（PPT、尽调反馈表等）\`
  - `Z:\投顾信息（PPT、尽调反馈表等）\`
  - 对应 UNC 路径，如 `\\10.168.20.10\投顾信息（PPT、尽调反馈表等）\`
- 即使用户要求修改、删除或整理上述证据文件，也必须拒绝，并说明该 skill 只能生成独立审核报告，不能改动原始证据。

**终端隔离（避免输出混杂）。**

- 不同性质的命令（盘符探测 / zmdata 查询 / 文件枚举 / 词汇表查询 / 报告保存）必须使用独立的 `RunCommand` 终端（每次指定 `target_terminal: "new"`），禁止所有命令复用同一终端导致输出混杂、难以定位返回值。
- 终端分类速查：

| 命令性质 | 典型命令 | 必须新终端 |
|---|---|---|
| 盘符探测 | `Test-Path`, `Get-ChildItem` 根目录 | ✅ |
| zmdata 查询 | `fund_search_quick`, `get_fund_in_label` | ✅ |
| 文件枚举 | `Get-ChildItem` 管理人文件夹 | ✅ |
| 词汇表查询 | `_vocabulary.py search/lookup` | ✅ |
| PDF 提取 | `extract_pdf_pages.py` | ✅ |
| 报告保存 | `validate_audit_report.py`, `sync_to_y.py` | ✅ |

- **注意**：由于 IDE 可能自动在 PowerShell 命令外层包裹 `trae-sandbox`，部分特殊字符（空格、管道、`$env:XXX`）的展开行为可能不一致。遇到路径或变量解析异常时，尝试调整引号嵌套方式。

**报告保存禁止使用 python -c 行内嵌入中文。**

- `python -c` 经过 `trae-sandbox` 双层引号包裹后，中文内容必然出现转义损坏（SyntaxError / 乱码），已多次证实不可靠。
- 保存报告必须使用「写入 `latest_report.md` → strict 校验 → `sync_to_y.py` 同步到 Y 盘 → 验证目标文件」的固定链路（详见 Phase 8 与 `references/save-and-sync.md`）。
- PDF 文本抽取必须使用 `scripts/extract_pdf_pages.py`，不得在终端内写一行 Python 循环或创建一次性 `.py` 脚本。

**证据分级统一为 P1/P2。**

- `P1`：尽调材料，包括尽调问卷、尽调笔记、投决会纪要、路演材料、营销材料。营销材料可在「来源」列注明「营销材料，P1 中偏弱」。
- `P2`：zmdata 当前字段
- 报告中不得出现 `P3`。如仅使用营销材料，标注为 `P1`（可在来源中说明偏弱）。

**多命中记录必须说明主审对象。**

- 如果 zmdata 命中多条同系列记录，报告必须明确写出主审记录 ID、参考记录 ID 及选择逻辑。
- 审核「匿名汇总记录」时，在「基金记录（zmdata）」中列出主审记录和参考记录，说明参考记录仅用于同系列口径校验，不等同于主记录字段值。

**报告语言约束。**

- 字段缺失只简洁告知候选口径，不写「严重不足」「可能已废弃」等判断性强但证据不足的表述。
- labelIDs 为 zmdata 系统内置多层标签树，随基金数据自动同步，非人工维护字段。不纳入字段审核结论。
- 证据强度只能写「高 / 中 / 低」。多份 P1 一致时写「高」，单份 P1 或证据偏弱时写「中」，不得写「中-高」「中偏高」等模糊等级。
- 报告采用混合格式：**基金记录（zmdata）和字段审核使用 Markdown 表格**，其余四章（结论摘要 / 策略画像 / 关键证据 / 口径说明）使用列表格式（`- `）。表格单元格内换行仅用 `<br>` 标签，严禁物理回车。

**fundType 保守原则。**

- 当审核证据来自同系列推断（已触发衰减规则），且存在基准体系不同、杠杆水平不一致、或波动特征未直接验证等混杂因素时，`fundType` 应明确标注「待人工确认」，不给予具体候选值。仅在目标产品有直接 P1 证据且波动层级可从材料中合理推断时，才可给出候选值。

**raceName 单一推荐原则。**

- 字段审核中 `raceName` 的结论必须给出**唯一的首选建议**。如果确实存在两个候选标签且证据不足以区分，应在结论中明确标注"两个候选的取舍需人工判断"，并将比较论证逻辑移至口径说明中展开，不在字段审核表中进行长篇标签辨析。

**推论边界风险前置。**

- 「口径说明」第一条必须单独开列「推论边界风险」，使用加粗强调，明确说明：①结论是否来自同系列推断；②目标产品与参考产品之间是否存在策略差异风险；③是否需要人工向管理人二次确认。不得将推论边界风险与其他口径条目混在同一行。

**证据链小结叙事要求。**

- 证据链小结必须给出因果逻辑，而非简单罗列文件清单。应回答两个核心问题：①证据的时间线/逻辑线如何支撑或削弱当前审核结论；②核心不确定性来自哪里（缺少独立材料、调研重心转移、基准体系变化等）。仅当证据在时间/策略线上有演进关系时必写；单份证据时可省略。


## Pre-Phase: Workspace Availability Check (MANDATORY — runs unconditionally)

在任何审计工作（含历史报告复用）开始前，必须先验证两个 workspace 文件夹均可达。**每次调用本 skill 均强制执行此检查，不得跳过。**

### 必检文件夹

| 文件夹 | 用途 | 测试路径 |
|---|---|---|
| `投顾信息（PPT、尽调反馈表等）` | 尽调材料（P1 证据源） | `W:\` 或 `Z:\` 根下 |
| `投顾管理人研究\fund-track-tag-audit` | 共享报告库（历史报告读写） | `Y:\` 根下 |

### 检查步骤

**Step A — 尽调材料文件夹：**

**必须使用 `RunCommand` + PowerShell，禁止使用 `LS` / `Glob`**（IDE 内置工具对 SMB 网络映射盘超时严重，即使已加入 workspace 也是如此）：

```powershell
Test-Path "W:\投顾信息（PPT、尽调反馈表等）"
Test-Path "Z:\投顾信息（PPT、尽调反馈表等）"
```

首个 `True` 的路径即为 `$DD_ROOT`。两条均 `False` 时终止。

**Step B — 共享报告库：**

```powershell
Test-Path "Y:\投顾管理人研究\fund-track-tag-audit"
```

### 终止规则

| 结果 | 动作 |
|---|---|
| 两项均可达 | → 继续 Phase 0 |
| 尽调材料文件夹不可达 | **STOP.** 告知用户："当前 workspace 中未找到尽调材料文件夹。请将 `\\10.168.20.10\投顾信息（PPT、尽调反馈表等）` 加入 workspace（如通过映射盘符 `W:\` 或 `Z:\` 加入）后再执行审计。" |
| 共享报告库不可达 | **STOP.** 告知用户："当前 workspace 中未找到共享报告库。请将 `Y:\投顾管理人研究\fund-track-tag-audit` 加入 workspace 后再执行审核；该目录用于团队共享历史审核报告。" |
| 两项均不可达 | **STOP.** 合并上述两条信息告知用户。 |

**未通过 Pre-Phase 检查时，不得继续执行任何后续步骤（包括 Phase 0 历史报告复用）。**

---

## Report Reuse and Batch Policy

### Phase 0: Historical Report Lookup

共享报告库已在 Pre-Phase 验证可用。路径约定：

```text
Y:\投顾管理人研究\fund-track-tag-audit\
  funds\
  batch\
```

确定请求为单基金或多基金后，查找已保存的单基金报告。

Saved reports used for reuse are single-fund audit artifacts:

- Single-fund reports live in `Y:\投顾管理人研究\fund-track-tag-audit\funds\`
- Batch summary reports live in `Y:\投顾管理人研究\fund-track-tag-audit\batch\` only when explicitly saved
- Batch summary reports are not used as reusable fund evidence unless the user explicitly asks to find batch reports

Use:

```powershell
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\find_saved_report.py") "<基金名称或关键词>"
```

If a report is found and the user did **not** explicitly request a refresh:

1. Read the latest matching report.
2. Return the historical report content in the conversation.
3. State the audit time parsed from the filename.
4. State the saved file path.
5. Tell the user they can request "重新审核" to run a fresh audit.

Do **not** describe the historical report as the current result. Use wording such as "已找到历史审核报告".

Skip saved-report reuse and proceed to a fresh audit when the user says any of:

- 重新审核 / 重新跑 / 再查一遍
- 刷新 / 更新 / 最新 / 当前
- 不用历史报告
- 以当前 zmdata 为准
- 检查有没有变化

When the user triggers a fresh audit, the Phase 0 check must still run (to detect saved reports for informational purposes), and the agent must include a line at the start of the audit flow:

```text
本次按重新审核处理，跳过历史报告复用。
```

If multiple reports are found, default to the latest one. Use `find_saved_report.py "<query>" --all` only when the user asks to compare historical versions.

### Multi-Fund Precheck

For multiple requested funds, run the precheck helper after the target list is known and before evidence lookup:

```powershell
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\plan_multi_fund_audit.py") "<基金A>" "<基金B>" "<基金C>"
```

Behavior:

1. If the user did not request refresh, reuse saved single-fund reports by default and fresh-audit only funds without saved reports.
2. If all requested funds already have saved reports, return a compact multi-fund summary from the historical reports and state that no fresh audit was run.
3. If the user requested "全部重新审核" / "最新" / "当前" / "不用历史报告", pass `--refresh-all` and fresh-audit all funds.
4. If the user requested only specific funds to refresh, pass `--refresh "<基金名>"` for each selected fund.
5. If the user's wording is ambiguous and the choice materially affects runtime, ask once whether to reuse saved reports, refresh all, or refresh specified funds.

Never generate placeholder single-fund reports. The precheck helper only plans reuse vs fresh-audit work.

## Prerequisites

### 1. Evidence Root Resolution

尽调材料文件夹已在 Pre-Phase 验证可达。此处仅确定当前可用的盘符作为 `$DD_ROOT`（再次 LS 测试 W:\ 和 Z:\，取首个返回内容的路径）。后续 `Glob` 搜索均以 `$DD_ROOT` 为根。

### 2. zmdata Lookup (MANDATORY)

Invoke the `zmdata-data-api` skill, then query the target fund.

**Do NOT use `zmdata_cli.py call --params` in PowerShell** — JSON quoting in PowerShell is unreliable and will break. Use `python -c` directly:

```powershell
& $PYTHON_EXE -c "import zmdata as api; df = api.fund_search_quick('基金名称'); print(df[['fundID','fundCode','fundName','typeName','strategyType','fundType','raceName']].to_string())"
```

If the result is wide, add `, pageSize=30` as the second argument. To dump all fields as dict:

```powershell
& $PYTHON_EXE -c "import zmdata as api; df = api.fund_search_quick('基金名称'); import json; [print(json.dumps(r, ensure_ascii=False, default=str)) for r in df.to_dict('records')]"
```

Extract from zmdata for each matched fund:

- `fund_name` / `fund_code` / `fund_id`
- `manager_name`
- `strategyType` (主赛道)
- `raceName` (细分赛道/标签)
- `fundType` (波动层级)
- `type_name` (记录类型: `尽调` / `投后子基金`)

> **常见问题**：`fundID` 在 zmdata 返回的 DataFrame 中为 **字符串类型**（如 `"1518296"`），筛选时须用 `r['fundID'] == '1518296'`，不能用整数比较。使用 `df.iloc[0]` 按位置取行时，`fundID` 列可能因索引重置而变化，建议始终用 `df.to_dict('records')` 后按字段筛选。

### 3. Fund Resolution & Scoring

For a multi-fund request, resolve each input fund independently. If the user supplies a manager name, a pasted list, or a keyword that returns several strong fund candidates, keep the candidates separated by product and make the candidate table explicit.

Score each zmdata record against each user query using these heuristics (do NOT run external Python; apply inline):

```
fund_code exact match        → +1000
fund_name exact match        → +900
short name exact match       → +850
query in full name           → +600 (substring)
query in short name          → +650 (substring)
fund_code in query           → +300
manager name in query        → +120
type == "尽调"               → +30
manager is NOT anonymous     → +10
```

- `MIN_STRONG_MATCH_SCORE = 600`
- Keep only records with score ≥ threshold (or threshold = max_score − 150 if max_score is very high)
- Never silently discard `匿名` manager records if they score above threshold
- If multiple funds resolve, audit all of them

Present a candidate table when matching is unexpected, ambiguous, or expands the user's input into multiple products:

```
| 保留 | 分数 | 基金 | 代码 | 管理人 | 记录类型 | 当前赛道 |
|---|---:|---|---|---|---|---|
```

## Audit Workflow

### Phase 4: Evidence Discovery

For each confirmed fund, locate evidence files inside `$DD_ROOT`.

**Step 3a — Find manager folder in due-diligence share**

```
LS $DD_ROOT/
Glob pattern: $DD_ROOT/*<manager_id_or_keyword>*/
```

The folder name typically follows the pattern `{机构ID}_{管理人简称}`, e.g., `359818_杭州博衍私募`.

**Step 3b — List files inside the manager folder**

```
LS <manager_folder_path>/
```

**Step 3c — Priority-rank the files**

Use the priority order from `references/source-priority.md`:

- `P1` (尽调材料, highest weight for track): 尽调摘要 > 投决会纪要 > 尽调笔记 > 路演材料 > 营销材料

Files with keyword matches to the fund name or code get higher priority internally.

**Binary file handling**:

- `.md` / `.txt`: read directly with `Read` tool
- `.pdf`: use `scripts/extract_pdf_pages.py` — never write a one-off Python script or use `python -c` with inline loops

```powershell
# Extract first N pages
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\extract_pdf_pages.py") "<pdf路径>" --first 10

# Extract specific page range
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\extract_pdf_pages.py") "<pdf路径>" --pages 29-31

# Search by keyword with context
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\extract_pdf_pages.py") "<pdf路径>" --keyword "量化CTA" --context-pages 1

# Truncate output per page
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\extract_pdf_pages.py") "<pdf路径>" --first 10 --max-chars 3000
```

**`.docx` handling** — try pandoc first, fall back to `python-docx`:

```powershell
# Primary: pandoc (if installed)
pandoc "<docx路径>" -t markdown --wrap=none

# Fallback: python-docx
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\extract_docx.py") "<docx路径>"
```

> pandoc 和 `extract_docx.py` 均失败时（如 `ModuleNotFoundError: docx`），告知用户 `.docx` 无法读取，询问是否需要执行 `pip install python-docx`。不要静默安装。

- `.docx`: invoke `docx` skill, or use `scripts/extract_docx.py` as fallback
- `.pptx`: invoke `pptx` skill
- `.xlsx`: invoke `xlsx` skill

Always read `.md` files first (尽调笔记, 尽调摘要, 投决会) — they contain the densest track/strategy information.

### Phase 5: Evidence Extraction & Portrait Building

Read each high-priority file and extract:

**Track / strategy information:**

- What strategy type does the document describe for this fund/series? (e.g., 量化CTA, 主观股票多头, 市场中性)
- What sub-strategies are mentioned? (e.g., 趋势跟踪, 强弱对冲, 基本面多因子)
- What assets/品种 are covered?
- What is the portfolio construction logic?
- What is the risk-control framework?

**Build a display portrait:**

```
- 一级赛道:
- 细分赛道:
- 策略属性:
- 收益来源:
- 投资范围:
- 风险画像:
- 标签映射:
```

Cross-reference multiple files. If 3+ documents agree on a classification, treat it as strong P1 evidence.

### Phase 6: Audit Execution

Compare the document-derived portrait against the current `zmdata` fields.

For each auditable field, apply `references/decision-rules.md`:

| Field | Audit Rule |
|---|---|
| `strategyType` | Does the document's primary strategy match zmdata? Check against controlled vocabulary via `_vocabulary.py search` |
| `raceName` | Does the document's L2/L3 track description match? Only recommend a concrete value after confirming it exists in the controlled vocabulary |
| `fundType` | Does the document's risk/volatility description align with the current bucket? Map document descriptions (e.g., "标准波动产品 1.5-2x 杠杆") to vocabulary terms |

**Vocabulary check** — when you need to validate terms or resolve label IDs:

```powershell
# Search: find labels whose name contains <keyword> (e.g., search "期货" matches "期货主观")
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\_vocabulary.py") search "<keyword>"

# Single lookup
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\_vocabulary.py") lookup <label_id>

# Batch lookup (comma-separated) — resolve many IDs in one call
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\_vocabulary.py") lookup <id1,id2,id3,...>

# List all known values by category
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\_vocabulary.py") strategy-types
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\_vocabulary.py") race-names
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\_vocabulary.py") risk-labels
```

Always batch all label IDs from one fund into a single `lookup` call instead of one call per ID.

### Phase 7: Output (MANDATORY TEMPLATE READ)

**CRITICAL**: Before writing any report Markdown, you MUST read `references/output-templates.md` in full. Do NOT generate a report from memory. The output uses hybrid format: table for 基金记录 and 字段审核; list for 结论摘要 / 策略画像 / 关键证据 / 口径说明. Follow six-section structure and all key content rules.

Single-fund output has exactly six sections:

1. **结论摘要** — 一致项先写，再写异常项（缺失/冲突），最后证据强度
2. **基金记录（zmdata）** — Markdown 表格，字段为空时写「空」
3. **字段审核** — 四列：字段 / 当前值 / 结论 / 说明。结论词：一致 / 需补充 / 需修正 / 需复核补充 / 人工复核
4. **策略画像** — 七行：一级赛道 / 细分赛道 / 策略属性 / 收益来源 / 投资范围 / 风险画像 / 标签映射
5. **关键证据** — 列表格式，3–6 条，按 P1/P2 优先级排列
6. **口径说明** — 同系列证据、字段缺失 vs 定性冲突等口径

**Multiple funds** → summary table first, expand only abnormal funds.

### Phase 8: Save Markdown Reports

**Document-first rule:** the saved Markdown file is the source of truth; the conversation is only a display surface. Generate each report once, save and validate it first, then show the same validated content or a compact summary in the conversation. Do not present a report as final if validation or sync fails.

Before saving, read `references/save-and-sync.md` and follow it exactly.

Single-fund reports are always saved before the full report is shown in the conversation or generated as part of a multi-fund audit.

```text
Y:\投顾管理人研究\fund-track-tag-audit\funds\
```

Use a timestamped filename:

```text
YYYYMMDD-HHMMSS_<基金简称>_策略标签审核.md
```

**保存流程（固定缓冲区 `latest_report.md` + strict 校验 + `sync_to_y.py`）:**

此流程彻底规避 `python -c` 行内嵌入中文导致的 `trae-sandbox` 转义损坏。Agent 每次操作的都是同一个固定文件，无需动态管理临时文件生命周期。

**Step 1 — 写入固定缓冲区：**

使用 `Write` 工具，**总是**写入以下固定路径。如文件已存在则直接覆盖。

```text
$REPORT_BUFFER
```

> `Write` 是 IDE 原生工具，在沙盒内直接写文件，不受 PowerShell / trae-sandbox 引号嵌套影响。中文、表格、特殊符号均可原样写入。

**Step 2 — strict 校验（强制）：**

```powershell
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\validate_audit_report.py") $REPORT_BUFFER --strict
```

**Step 3 — 同步到 Y 盘（强制）：**

```powershell
& $PYTHON_EXE (Join-Path $SKILL_ROOT "scripts\sync_to_y.py") "Y:\投顾管理人研究\fund-track-tag-audit\funds\<YYYYMMDD-HHMMSS_基金简称_策略标签审核>.md"
```

> `sync_to_y.py` 只接收一个参数——目标文件完整路径。源路径固定为脚本父目录下的 `latest_report.md`，无需任何字符串拼接。`shutil.copy2` 二进制安全拷贝。自动创建目标目录。

**Step 4 — 验证归档（强制）：**

- 使用只读命令确认目标文件存在且可读。
- 成功后，会话中先展示 5–8 行摘要和保存路径；完整六段报告仅在用户需要或报告较短时展示。
- 失败时，告知用户「报告草稿已生成但未归档成功」，并给出本地 `latest_report.md` 路径，不得称为正式审核结果。

**禁止的方式（重申）：**

| 方式 | 原因 |
|---|---|
| `python -c "import os; report = '''...中文...'''"` | trae-sandbox 双层引号必然损坏中文，已多次证实不可靠 |
| `@'...'@` heredoc + pipe | PowerShell 管道在 sandbox 中文编码损耗 |
| `Out-File "$env:TEMP\..."` | sandbox 拦截，退出码 -1073741510 |
| 直接用 `Write` 工具写入 Y:\ 路径 | Write 工具被沙盒限制在工作区内，无法跨盘写入 |

For multi-fund audits:

- Save each single-fund report by writing to `latest_report.md` and running `sync_to_y.py` once per fund.
- Show one compact综合报告 in the conversation.
- Do not save the综合报告 unless the user explicitly asks to save it.
- If the user asks to save the综合报告, use `--kind batch` and title it `<批次名>_多基金策略标签审核`.

### Evidence Priority Rules

Follow `references/source-priority.md`:

- Multiple `P1` aligned ≠ `P2`: **建议修改**
- Single `P1` agrees: **可建议修改**（confidence: 中）
- Only weak `P1`: **不修改**（confidence: 低）

## Scope

Audit only these zmdata fields:

- `strategyType` — primary strategy class
- `raceName` — secondary track / cycle
- `fundType` — volatility bucket
- `labelIDs` — displayed in 基金记录（zmdata） and 策略画像 → 标签映射 for reference; not audited (zmdata system-internal labels, auto-synced)

Display may include richer detail (L1/L2/L3, assets, strategy mix) beyond what zmdata tracks.

## Operational Notes

- **管理人更名**：尽调材料中的管理人名称为注册地机构名称，可能与 zmdata 当前管理人不一致（如「扬州远和」→「杭州远和」）。此类更名不影响策略标签审核，应在报告口径说明中注明。
- **SMB 路径空格**：`W:\投顾信息（PPT、尽调反馈表等）` 等 SMB 路径含中文括号和空格，PowerShell 命令中必须用英文双引号包裹完整路径，IDE sandbox 的 `trae-sandbox` 包裹层可能改变引号嵌套行为，优先使用 `python -c` 内联代替复杂 PowerShell 管道。

## References

- `references/source-priority.md` — evidence priority and conflict rules
- `references/decision-rules.md` — field-level audit rules and outcome labels
- `references/output-templates.md` — output format specifications
- `references/save-and-sync.md` — document-first save/sync workflow and failure handling

## Scripts

- `scripts/_vocabulary.py` — controlled vocabulary lookup CLI. Commands:
  - `search <keyword>` — find labels where keyword appears in the label name
  - `lookup <id>` or `lookup <id1,id2,id3>` — resolve one or many label IDs
  - `strategy-types` / `race-names` / `risk-labels` — list all known values per category
  Lightweight, reads a markdown file, no network I/O.
- `scripts/extract_pdf_pages.py` — the only authorised PDF text extractor. Supports `--pages`, `--first`, `--keyword` with `--context-pages`, and `--max-chars`. Outputs to stdout only, never writes files. Parser errors are reported as concise stderr messages.
- `scripts/extract_docx.py` — docx text extractor using `python-docx`. Fallback when pandoc is unavailable. Usage: `extract_docx.py "<docx路径>"`. Extracts paragraphs and table text, auto-truncates at 12000 chars.
- `scripts/validate_audit_report.py` — validate single-fund audit report Markdown before saving. Two modes:
  - **normal**（默认）：仅报告结构性错误（缺章节 / 画像维度严重缺失 / 无效值 / 表格使用）；内容质量问题（画像缺维 / 推测性表述）降级为警告，不阻断。
  - **`--strict`**（Phase 8 强制使用）：所有警告升级为错误，追加完整 7 维画像检查、加粗格式检查、推论边界风险、字段建议等内容规则。
  - 独立调试时直接运行 `validate_audit_report.py <path> --strict` 预览保存前的校验结果，无需走完整保存流程。
- `scripts/save_audit_report.py` — backup/debug helper only. The normal skill workflow uses `latest_report.md` + `validate_audit_report.py --strict` + `sync_to_y.py`.
- `scripts/sync_to_y.py` — 将固定缓冲区 `latest_report.md` 同步到 Y 盘。仅接收目标文件路径一个参数，源路径固定。零字符串拼接，Agent 认知负担最低。
- `scripts/find_saved_report.py` — search saved single-fund reports in the shared report store. Use before every fresh audit unless the user explicitly requested refresh/re-audit.
- `scripts/plan_multi_fund_audit.py` — precheck a list of funds and mark each as reuse historical report or fresh audit. It does not create reports.

## Legacy

- `scripts/_legacy/` — contains the old SMB-based Python pipeline (`audit_fund_tracks.py`, `collect_manager_files.py`, `smb_file_utils.py`, `_extractors.py`, `check_prereqs.py`). These are no longer used by the native workflow and are kept for reference only.
