---
name: private-fund-dd-note
description: Use when 用户要求把私募基金/私募管理人电话尽调、录音转写稿、访谈纪要、路演 PDF/PPT/DOCX 或公开核验材料整理成定性尽调 Markdown，尤其是要求与原始材料同目录落盘、沉淀到 MyNotes，或补充中基协/官网/工商/处罚等公开核验时。
---

# 私募基金尽调纪要整理

用于将电话尽调转录、路演材料与公开可核验信息整合为标准化的私募基金定性尽调纪要。默认把 Markdown 草稿放在用户指定目录；若用户未指定且核心材料位于同一目录，则放在原始材料同目录。

## 何时使用

在以下情形使用本技能：

- 用户要求根据电话转录 `txt`、路演材料 `pdf` 整理私募基金尽调纪要
- 用户要求把录音转写稿、访谈纪要、路演 `pdf` / `pptx` / `docx` 汇总成定性尽调 Markdown
- 用户要求补充中基协、官网、工商、第三方公开信息核验
- 用户要求按标准私募基金尽调格式输出 Markdown
- 用户要求生成的 `.md` 与原始尽调材料放在同一路径
- 用户要求将产物落在 `F:\Thomas\MyNotes` 的基金尽调目录中

不要在以下情形使用本技能：

- 只做 MyNotes 归档、改路径、改 frontmatter、改标签时，使用 `mynotes-knowledge-manager`
- 需要正式 ODD 评分、按扣分表打分时，使用 `PE_ODD_Auditor`
- 需要将内容入库到 fund-wiki 或做基金池研究时，使用 `fund-wiki` 或 `fund-wiki-research`

## 必读引用

### MyNotes 规则源

当产物需要写入 `F:\Thomas\MyNotes` 时，先读取以下文件，再执行本技能：

- `../mynotes-knowledge-manager/references/path-policy.md`
- `../mynotes-knowledge-manager/references/note-schema.md`
- `../mynotes-knowledge-manager/references/human-review-gate.md`
- `references/mynotes-integration.md`

### 本技能参考文件

- `references/dd-outline.md`
- `references/verification-checklist.md`
- `references/source-layering-rules.md`
- `references/risk-patterns.md`
- `references/pressure-scenarios.md`

## 核心原则

1. 公开可核验事实、管理人口径、待核实事项必须分层书写。
2. 不把电话口径、路演口径或第三方平台展示口径直接写成既成事实。
3. 关键缺失信息可以留空并列入“待核实事项”，不要为凑完整度而补写。
4. 用户指定落盘目录时，不擅自重路由；未指定且核心材料同目录时，Markdown 默认放在该目录。
5. 不移动、删除、重命名原始 `txt` / `pdf` / `pptx` / `docx` 材料。
6. 默认输出为草稿，而不是最终验证结论。
7. 公开核验必须记录核验状态；未检索、检索失败、网络不可用都不能写成“无异常”。
8. 对客户名称、个人联系方式、账号、身份证件等敏感信息只做必要概括，不扩散到无关章节。

## 先确认或停下的情形

出现以下情况时，先向用户确认，不自行决定：

- 没有明确输出目录，且核心材料不在同一目录
- 一个目录中有多个可能的电话转录、路演材料或已有纪要，无法判断主材料
- 用户要求移动、归档、重命名、删除或去重原始材料
- 用户要求直接标记为 `validated` 或 `human_review_required: false`
- 用户明确要求跳过公开核验，但又希望得到正式尽调判断

## 标准流程

1. 识别核心材料：电话转录、路演材料、已有纪要、公开核验材料。必要时按文件类型使用 `pdf`、`docx` 或 `pptx` 读取内容。
2. 确定输出路径：用户指定目录优先；否则核心材料同目录时，Markdown 落在该目录。
3. 从电话转录提取团队、策略、产品、规模、风控、客户、回撤、容量、费率等口径。
4. 从路演材料提取公司介绍、团队背景、产品要素、业绩展示、风控框架。
5. 按 `references/verification-checklist.md` 执行最小必要公开核验；若无法核验，记录为“未完成核验”或“无法访问”。
6. 按 `references/source-layering-rules.md` 将内容切分为：
   - 公开可核验事实
   - 管理人口径
   - 差异与冲突
   - 待核实事项
7. 按 `references/dd-outline.md` 组织正文结构。
8. 如果目标路径在 `F:\Thomas\MyNotes`，按 `references/mynotes-integration.md` 生成 frontmatter、文件名和 review 状态。
9. 输出 Markdown，并在 `Sources` 中保留本地材料与公开核验来源。

## 输出要求

- 文件格式：Obsidian 兼容 Markdown
- 产物类型：`knowledge-note`
- 证据粒度：默认使用文档级 `source_files`
- 状态默认值：
  - `status: filed`
  - `stage: synthesized`
  - `confidence: medium`
  - `human_review_required: true`
- 标题应直接体现管理人名称与文档性质
- `source_files` 至少列出本次使用的原始转录和路演材料
- 公开核验来源应列出来源名称、URL 或检索位置、访问日期、核验状态
- 若未完成公开核验，`confidence` 默认降为 `low`，并在正文说明原因

## 关键检查

- `.md` 是否落在用户指定路径，或在未指定路径时与核心材料同目录
- 是否明确区分“公开事实”和“电话/路演口径”
- 是否把冲突信息放入“风险提示”或“待核实事项”
- 是否遗漏中基协基础信息
- 是否记录公开核验来源、访问日期和核验状态
- 是否把第三方平台描述误写成正式结论
- 是否遵守 MyNotes review gate
- 是否避免扩散敏感客户、个人身份或联系方式信息

## 常见错误

- 用户未指定输出路径时，把 Markdown 放到当前工作目录而不是材料所在目录
- 直接把电话中的规模、费率、股权安排写成事实
- 因为用户指定了 MyNotes 目录，就跳过 MyNotes frontmatter 规范
- 因为有官网或第三方页面，就省略中基协核验
- 网络不可用或未执行公开检索时，用记忆补写核验结论
- 把“未查到处罚”写成“确认无处罚”
- 产物已落盘却擅自标为 `validated`
