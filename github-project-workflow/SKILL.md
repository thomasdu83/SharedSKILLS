---
name: github-project-workflow
description: 当需要把本地项目连接到 GitHub、初始化仓库、配置 origin、首次 push、日常同步、处理 GitHub 远端错误、编写 GitHub PR 草稿或检查 QuantSystem 的 .gitignore / 数据排除策略时使用
---

# GitHub 项目工作流

## 概述

用于 Windows / PowerShell 环境下的 GitHub 仓库初始化、远端配置、首次推送和日常同步。默认保守执行：先验证仓库状态，再建议或执行 Git 命令。

**开始时宣布：** "我正在使用 github-project-workflow 技能处理 GitHub 仓库流程。"

## 基本原则

- 先运行 `git rev-parse --show-toplevel` 判断当前目录是否已在 Git 仓库中。
- 先运行 `git status --short --branch` 查看分支和变更范围。
- 先运行 `git remote -v` 查看远端。
- 未经用户明确要求或批准，不执行 `commit`、`pull`、`push`、`merge`、`rebase`、删除分支或覆盖远端。
- 对 QuantSystem，默认不提交 `data/`、`database/`、`.venv/`、`node_modules/`、`*.db`、`*.pkl`、日志和临时输出。

## 新项目首次上传

用户已在 GitHub 网页创建空仓库时，按此流程：

```powershell
cd F:\Thomas\QuantSystem

git init
git branch -M main

git status --short --branch
git add -A
git status --short

git commit -m "chore: initialize QuantSystem repository"
git remote add origin https://github.com/<user-or-org>/<repo>.git
git remote -v
git push -u origin main
```

如果 `git push -u origin main` 报 `src refspec main does not match any`，说明还没有第一次 commit。先执行 `git add -A` 和 `git commit`。

## 首次上传前检查

在 `git add -A` 前检查 `.gitignore` 和嵌套仓库：

```powershell
git status --short --branch
$repoRoot = git rev-parse --show-toplevel
Get-ChildItem -Path $repoRoot -Force -Recurse -Directory -Filter .git |
  Where-Object { $_.FullName -ne (Join-Path $repoRoot ".git") } |
  Select-Object FullName
```

如果发现子目录里有独立 `.git`，先问用户：

- 独立项目：加入根 `.gitignore`，例如 `/ChronoSalon/`。
- 并入主仓库：删除子目录内部 `.git`，再重新 `git add -A`。

不要在未确认前删除任何 `.git` 目录。

## 日常更新

单人本地开发的常用流程：

```powershell
git status --short --branch
git add -A
git status --short
git commit -m "fix(scope): describe the change"
git push origin main
```

只有在多设备、多人协作、GitHub 网页改过文件，或 `push` 被拒绝时，再使用：

```powershell
git pull --rebase origin main
git push origin main
```

## 常见远端问题

远端已存在：

```powershell
git remote -v
git remote set-url origin https://github.com/<user-or-org>/<repo>.git
```

查看提交历史：

```powershell
git log --oneline --decorate -n 10
```

撤销暂存：

```powershell
git restore --staged .
```

## PR 草稿

如果用户要求创建 PR，先检查 GitHub CLI：

```powershell
gh --version
gh auth status
```

如果 `gh` 不可用或未登录，只输出 PR 草稿：

```markdown
## 摘要
- <变更要点 1>
- <变更要点 2>

## 测试
- <运行过的验证命令和结果>

## 注意事项
- <数据、配置、迁移或兼容性风险>
```
