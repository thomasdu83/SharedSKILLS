# 代码审查 (Code Review)

当用户提及 "review", "审查", "检查代码" 时，自动进入审查模式。

## 1. 审查模式

- **快速审查 (Quick Scan)**: 5分钟内，检查 `print`, 类型注解, 硬编码路径。
- **深度审查 (Deep Review)**: 模块级检查，覆盖架构、设计模式、数据层规范。

## 2. 检查清单 (Checklist)

### 2.1 Critical (必须修复)
- [ ] **Hardcoding**: 是否存在硬编码路径或配置？
- [ ] **Dependency Injection**: 核心类是否通过构造函数注入依赖？
- [ ] **Fail Fast**: 是否在入口处校验参数？
- [ ] **Silent Failure**: 是否存在空的 `except:` 块？
- [ ] **Logging**: 是否使用 `print()` 而非 `logger`？
- [ ] **Data Format**: 大批量数据是否使用 Parquet 而非 CSV/Excel/SQLite？

### 2.2 Warning (强烈建议)
- [ ] **Type Hints**: 公开方法是否有类型注解？
- [ ] **Docstrings**: 是否包含 `Args/Returns/Raises`？
- [ ] **Complexity**: 单文件是否超过 1000 行？

## 3. 输出格式

```markdown
# 代码审查报告

**审查对象**: `[文件/模块]`
**审查模式**: [快速/深度]

---

## ⛔ Critical
1. **[位置]**: 问题描述
   - *修复建议*: ...

## ⚠️ Warning
1. **[位置]**: 问题描述

## ✅ 合规项
- ...

## 📋 改进计划
1. 立即修复: ...
2. 后续优化: ...
```
