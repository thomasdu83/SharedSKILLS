---
name: using-git-worktrees
description: 当需要开始与当前工作区隔离的功能开发、执行实现计划、创建功能分支或使用 git worktree 时使用；先验证当前目录是 Git 仓库，再创建具有目录选择和安全验证的隔离工作树
---

# 使用 Git 工作树

## 概述

Git 工作树创建共享同一仓库的隔离工作区，允许同时在多个分支上工作而无需切换当前目录。

**核心原则：** 先验证 Git 仓库和工作区状态，再选择目录，最后创建隔离工作树。

**开始时宣布：** "我正在使用 using-git-worktrees 技能来建立一个隔离的工作区。"

## Git 前置检查

创建工作树前先运行：

```powershell
git rev-parse --show-toplevel
git status --short --branch
git remote -v
```

如果 `git rev-parse --show-toplevel` 失败，停止并报告：当前目录不是 Git 仓库，不能创建 worktree。

如果工作区存在未提交变更，先说明变更范围，并询问用户是否继续；不要自动 stash、commit 或丢弃变更。

## 目录选择流程

按以下优先顺序执行。

### 1. 检查现有目录

Windows / PowerShell：

```powershell
Test-Path .worktrees
Test-Path worktrees
```

Git Bash / Linux：

```bash
test -d .worktrees
test -d worktrees
```

如果两者都存在，优先使用 `.worktrees`。

### 2. 检查项目约定文件

Windows / PowerShell：

```powershell
$files = @("CLAUDE.md", "AGENTS.md", ".codex.md") | Where-Object { Test-Path $_ }
if ($files) {
  Select-String -Path $files -Pattern "worktree.*director|worktree.*directory" -CaseSensitive:$false
}
```

Git Bash / Linux：

```bash
grep -i "worktree.*director\|worktree.*directory" CLAUDE.md AGENTS.md .codex.md 2>/dev/null
```

如果指定了偏好，直接使用，无需询问。

### 3. 询问用户

如果没有现有目录且项目约定文件中无偏好设置：

```text
未找到工作树目录。我应该在哪里创建工作树？

1. .worktrees/（项目本地，隐藏目录）
2. %USERPROFILE%\.codex\worktrees\<project-name>（用户级全局位置）

你倾向哪个？
```

## 安全验证

### 项目本地目录

创建 `.worktrees` 或 `worktrees` 前必须验证目录已被 Git 忽略：

```powershell
git check-ignore .worktrees
git check-ignore worktrees
```

如果未被忽略：

1. 在 `.gitignore` 中添加相应条目。
2. 记录此变更。
3. 只有用户明确要求提交时，才执行 `git add` / `git commit`。
4. 继续创建工作树。

### 用户级全局目录

`%USERPROFILE%\.codex\worktrees\<project-name>` 在项目之外，无需 `.gitignore` 验证。

## 创建步骤

### 1. 检测项目名称

```powershell
$repoRoot = git rev-parse --show-toplevel
$project = Split-Path -Leaf $repoRoot
```

### 2. 创建工作树

项目本地目录：

```powershell
$path = Join-Path ".worktrees" $BRANCH_NAME
git worktree add $path -b $BRANCH_NAME
Set-Location $path
```

用户级全局目录：

```powershell
$path = Join-Path $env:USERPROFILE ".codex\worktrees\$project\$BRANCH_NAME"
git worktree add $path -b $BRANCH_NAME
Set-Location $path
```

### 3. 运行项目设置

按项目文件自动检测：

```powershell
if (Test-Path package.json) { npm install }
if (Test-Path Cargo.toml) { cargo build }
if (Test-Path requirements.txt) {
  if (Test-Path "F:\Thomas\QuantSystem\.venv\Scripts\python.exe") {
    & "F:\Thomas\QuantSystem\.venv\Scripts\python.exe" -m pip install -r requirements.txt
  } else {
    python -m pip install -r requirements.txt
  }
}
if (Test-Path pyproject.toml) { poetry install }
if (Test-Path go.mod) { go mod download }
```

### 4. 验证基线正常

运行项目对应的最小基线检查：

```powershell
npm test
cargo test
& "F:\Thomas\QuantSystem\.venv\Scripts\python.exe" -m pytest
go test ./...
```

如果基线失败，报告失败情况并询问是否继续或先排查。

## 快速参考

| 情况 | 操作 |
|---|---|
| `.worktrees/` 存在 | 使用它，并验证已忽略 |
| `worktrees/` 存在 | 使用它，并验证已忽略 |
| 两者都存在 | 使用 `.worktrees/` |
| 都不存在 | 检查项目约定文件，再询问用户 |
| 本地目录未被忽略 | 添加到 `.gitignore`，记录检查点，用户要求时再提交 |
| 当前目录不是 Git 仓库 | 停止，报告无法创建 worktree |
| 基线测试失败 | 报告失败，等待用户确认 |

## 红线

**绝不：**
- 未验证 `git rev-parse --show-toplevel` 就创建 worktree
- 创建项目本地工作树时不验证是否已忽略
- 自动 stash、commit、丢弃用户变更
- 跳过基线测试验证
- 在有歧义时假设目录位置

**始终：**
- 先查看 `git status --short --branch`
- 遵循目录优先级：现有目录 > 项目约定文件 > 询问
- 对项目本地目录验证是否已忽略
- 使用项目自己的测试或检查命令验证基线

## 集成

**被以下技能调用：**
- **brainstorming**（阶段 4）- 设计通过且需要隔离实现时使用
- **subagent-driven-development** - 执行需要隔离工作区的任务前使用
- **executing-plans** - 执行需要隔离工作区的计划前使用

**配合使用：**
- **finishing-a-development-branch** - 工作完成后清理时使用
