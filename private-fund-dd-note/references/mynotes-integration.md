# MyNotes 融合说明

本文件用于说明本技能如何继承 `mynotes-knowledge-manager` 的规则源，而不是重复定义一套新的 MyNotes 规范。

## 继承方式

采用“引用规则源 + 任务级桥接说明”的方式：

- `path-policy.md` 负责决定落盘路径与原始材料处理边界
- `note-schema.md` 负责决定 frontmatter 字段形状与默认值
- `human-review-gate.md` 负责决定是否可以标记为 `validated` 以及是否允许移动原始材料

本技能不摘录这些文件的全文，也不覆盖其通用规则。

## 本技能对 MyNotes 的桥接约束

当用户要求把尽调纪要落在 `F:\Thomas\MyNotes` 时：

1. 用户指定目录优先，不重路由。
2. 若用户未指定输出目录，且核心材料已在同一个 MyNotes 目录中，Markdown 默认放在该目录。
3. 若核心材料位于 `000 Inbox`，可以同目录生成草稿，但应保持 review 状态并建议后续稳定归档位置。
4. 使用 Obsidian 兼容 Markdown 与 YAML frontmatter。
5. 默认采用稳定知识笔记形态，而不是 intake note。
6. `source_files` 至少列出电话转录和路演材料。
7. 原始材料只引用，不移动、不重命名、不去重。
8. 未经过用户显式 review gate，不得写成：
   - `stage: validated`
   - `human_review_required: false`

## 推荐默认值

对本类私募尽调纪要，若用户未另行指定，采用以下默认值：

```yaml
type: knowledge-note
status: filed
stage: synthesized
confidence: medium
ai_owned: true
human_review_required: true
stale: false
```

建议补充：

```yaml
review_after: <当前日期后 3 个月>
```

## 文件命名建议

默认命名格式：

```text
<管理人简称>_私募基金电话尽调纪要_<电话日期>.md
```

如果用户已有既定命名习惯，以用户习惯优先。

## 何时停下来问用户

出现以下情况时，应停下来确认，而不是自行决定：

- 目标目录不明确
- 一个目录中有多个 `txt` 或多个核心 `pdf`
- 用户希望移动或归档原始材料
- 用户要求直接标记为 `validated`
- 产物是否应成为普通知识笔记还是项目文档存在明显歧义
- 源材料在多个目录中，且用户没有说明 Markdown 应与哪一组原始材料同目录
