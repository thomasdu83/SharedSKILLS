---
name: finishing-a-development-branch
description: 当实现已完成、测试已通过、并且需要决定如何把工作集成到主线时使用；这是 Git/PR/合并/清理的收尾技能，不负责验证本身。
---

# 完成开发分支

## 概述

通过提供清晰的选项并执行所选工作流来引导开发工作的收尾。

**核心原则：** 验证测试 → 展示选项 → 执行选择 → 清理。

**开始时宣布：** "我正在使用 finishing-a-development-branch 技能来完成这项工作。"

## 流程

### 步骤 0：验证 Git 环境

在任何合并、拉取、推送或 PR 操作前，确认当前目录确实是 Git 仓库，并记录分支、远端和工作区状态：

```bash
git rev-parse --show-toplevel
git status --short --branch
git remote -v
```

如果不是 Git 仓库，停止 Git 收尾流程，改为报告已完成的文件、验证结果和人工后续步骤。

如果没有远端，不能执行推送或创建 PR；只展示“保持现状”或“本地后续配置 remote”的建议。

如果工作区存在与本次任务无关的未提交变更，先报告并等待用户确认，不要自动合并、拉取、推送或清理。

### 步骤 1：验证测试

**在展示选项之前，验证测试通过：**

```bash
# 运行项目的测试套件
npm test / cargo test / pytest / go test ./...
```

**如果测试失败：**
```
测试失败（<N> 个失败）。必须先修复才能继续：

[显示失败信息]

在测试通过之前无法进行合并/PR。
```

停止。不要继续到步骤 2。

**如果测试通过：** 继续步骤 2。

### 步骤 2：确定基础分支

```bash
# 尝试常见的基础分支
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

或者询问："这个分支是从 main 分出来的——对吗？"

### 步骤 3：展示选项

展示以下 4 个选项：

```
实现已完成。你想怎么做？

1. 在本地合并回 <base-branch>
2. 推送并创建 Pull Request
3. 保持分支现状（我稍后处理）
4. 丢弃这项工作

选哪个？
```

**不要添加解释** - 保持选项简洁。

### 步骤 4：执行选择

#### 选项 1：本地合并

```bash
# 切换到基础分支
git checkout <base-branch>

# 拉取最新代码前必须确认工作区干净
git status --short
git pull --ff-only

# 合并功能分支
git merge <feature-branch>

# 在合并结果上验证测试
<test command>

# 如果测试通过
git branch -d <feature-branch>
```

然后：清理工作树（步骤 5）

#### 选项 2：推送并创建 PR

```bash
# 确认远端存在
git remote -v

# 推送分支
git push -u origin <feature-branch>

# 创建 PR 前确认 GitHub CLI 已安装并已登录
gh --version
gh auth status
gh pr create --title "<title>" --body "$(cat <<'EOF'
## 摘要
<2-3 条变更要点>

## 测试计划
- [ ] <验证步骤>
EOF
)"
```

如果 `gh` 不可用或未登录，不要强行创建 PR。输出 PR 标题、摘要、测试计划和目标分支，让用户在 GitHub 网页创建。

然后：清理工作树（步骤 5）

#### 选项 3：保持现状

报告："保留分支 <name>。工作树保留在 <path>。"

**不要清理工作树。**

#### 选项 4：丢弃

**先确认：**
```
这将永久删除：
- 分支 <name>
- 所有提交：<commit-list>
- 工作树 <path>

输入 'discard' 确认。
```

等待精确的确认。

确认后：
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

然后：清理工作树（步骤 5）

### 步骤 5：清理工作树

**对于选项 1、2、4：**

检查是否在工作树中：
```bash
git worktree list | grep $(git branch --show-current)
```

Windows PowerShell 可用：
```powershell
git worktree list
git branch --show-current
```

如果是：
```bash
git worktree remove <worktree-path>
```

**对于选项 3：** 保留工作树。

## 快速参考

| 选项 | 合并 | 推送 | 保留工作树 | 清理分支 |
|------|------|------|-----------|---------|
| 1. 本地合并 | ✓ | - | - | ✓ |
| 2. 创建 PR | - | ✓ | ✓ | - |
| 3. 保持现状 | - | - | ✓ | - |
| 4. 丢弃 | - | - | - | ✓（强制） |

## 常见错误

**跳过测试验证**
- **问题：** 合并损坏的代码、创建失败的 PR
- **修复：** 在提供选项前始终验证测试

**开放式问题**
- **问题：** "接下来该做什么？" → 含糊不清
- **修复：** 准确展示 4 个结构化选项

**自动清理工作树**
- **问题：** 在可能还需要工作树时就删除了（选项 2、3）
- **修复：** 只在选项 1 和 4 时清理

**丢弃时不确认**
- **问题：** 意外删除工作成果
- **修复：** 要求输入 "discard" 确认

## 红线

**绝不：**
- 在测试失败时继续
- 合并前不验证测试结果
- 未验证 Git 仓库、分支、远端和工作区状态就执行 Git 收尾动作
- 不确认就删除工作成果
- 未经明确请求就强制推送

**始终：**
- 先运行 `git rev-parse --show-toplevel`、`git status --short --branch` 和 `git remote -v`
- 在提供选项前验证测试
- 准确展示 4 个选项
- 选项 4 要求输入确认
- 只在选项 1 和 4 时清理工作树

## 集成

**被以下技能调用：**
- **subagent-driven-development**（步骤 7）- 所有任务完成后
- **executing-plans**（步骤 5）- 所有批次完成后

**配合使用：**
- **using-git-worktrees** - 清理由该技能创建的工作树
