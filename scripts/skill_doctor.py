#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""skill_doctor.py — SharedSKILLS 只读体检工具。

本工具只读取文件、报告问题，不修改、不删除、不重命名、不自动修复任何内容。

设计约束：
- 只使用 Python 标准库（os / sys / argparse / json / re / datetime / pathlib）。
- 不依赖 PyYAML；内置一个最小 YAML 子集解析器，专门解析本项目已知结构的
  skill-registry.yaml 与 tests/*.yaml。
- 不自动同步到 QuantSystem，不写入任何缓存。

用法：
    python scripts\\skill_doctor.py --root . --json
    python scripts\\skill_doctor.py --root . --strict
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _configure_stdout() -> None:
    """Keep machine-readable output usable on Windows legacy consoles."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, OSError):
        pass

# 本地资源前缀：正文中以这些前缀开头的相对路径被判定为 Skill 自身必需资源。
_LOCAL_PREFIXES = ("references/", "scripts/", "engine/", "assets/", "agents/")
# 目标输出前缀：属于 QuantSystem 模板或仓库产出目标，缺失只警告，不判为 Skill 内部缺失。
_TARGET_PREFIXES = ("docs/", "docs/templates/")
# 缓存 / 临时 / 编译产物模式：只报告，不删除。
_CACHE_PATTERNS = (
    "__pycache__",
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".cache",
    ".DS_Store",
    "~$",
    ".light-skill-update-cache.json",
    "__html_preview",
)

# 这些目录中的路径通常出现在示例代码或模板说明中，不是运行该 Skill
# 所必需的本地依赖。它们仍会被报告，但不会在 --strict 下阻断验收。
_ILLUSTRATIVE_SKILL_DIRS = {
    "skill-creator",
    "writing-skills",
    "dispatching-parallel-agents",
    "chinese-git-workflow",
}


# ---------------------------------------------------------------------------
# 最小 YAML 子集解析器（仅处理本项目已知结构）
# ---------------------------------------------------------------------------

def _preprocess(text: str):
    """把 YAML 文本转成 (缩进, 内容) 列表，去掉空行与纯注释行。"""
    items = []
    for raw in text.splitlines():
        stripped = raw.rstrip("\n")
        if not stripped.strip():
            continue
        if stripped.lstrip().startswith("#"):
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        content = stripped.strip()
        # 去掉行尾注释（简单处理：引号内不处理，本项目注释少且不内含冒号内容）
        items.append((indent, content))
    return items


def _parse_scalar(s: str):
    """解析标量：支持引号字符串、单行方括号列表 []、空列表。"""
    s = s.strip()
    if s == "[]":
        return []
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if inner == "":
            return []
        return [x.strip().strip("\"'") for x in inner.split(",")]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("\"", "'"):
        return s[1:-1]
    return s


def _looks_like_mapping(rest: str) -> bool:
    """判断序列项 '- ...' 的剩余部分是否形如 'key: value'。"""
    if ":" not in rest:
        return False
    key = rest.split(":", 1)[0].strip()
    return key != "" and " " not in key


def _parse_block(items, i: int, indent: int):
    """递归解析一个块（mapping 或 sequence），返回 (值, 下一个索引)。"""
    if i >= len(items):
        return None, i
    if items[i][1].startswith("- "):
        return _parse_sequence(items, i, indent)
    return _parse_mapping(items, i, indent)


def _parse_mapping(items, i: int, indent: int):
    result = {}
    while i < len(items):
        ind, content = items[i]
        if ind < indent:
            break
        if ind > indent:
            raise ValueError(f"意外的缩进：{content!r}")
        if content.startswith("- "):
            break
        if ":" not in content:
            raise ValueError(f"mapping 行缺少冒号：{content!r}")
        key, rest = content.split(":", 1)
        key = key.strip().strip("\"'")
        rest = rest.strip()
        if rest == "":
            # 空值：下一行缩进更深则解析子块，否则置 None。
            if i + 1 < len(items) and items[i + 1][0] > indent:
                val, i = _parse_block(items, i + 1, items[i + 1][0])
                result[key] = val
            else:
                result[key] = None
                i += 1
        else:
            result[key] = _parse_scalar(rest)
            i += 1
    return result, i


def _parse_sequence(items, i: int, indent: int):
    result = []
    while i < len(items):
        ind, content = items[i]
        if ind < indent:
            break
        if ind > indent:
            raise ValueError(f"sequence 中意外的缩进：{content!r}")
        if not content.startswith("- "):
            break
        rest = content[2:].strip()
        if rest == "":
            # '- ' 后为空，下一行缩进更深则解析子块。
            if i + 1 < len(items) and items[i + 1][0] > indent:
                val, i = _parse_block(items, i + 1, items[i + 1][0])
                result.append(val)
            else:
                result.append(None)
                i += 1
        elif _looks_like_mapping(rest):
            m, i = _parse_inline_mapping(items, i, indent, rest)
            result.append(m)
        else:
            result.append(_parse_scalar(rest))
            i += 1
    return result, i


def _parse_inline_mapping(items, i: int, seq_indent: int, first_rest: str):
    """解析 '- key: value' 开头的 mapping，后续键对齐在 seq_indent + 2。"""
    key_indent = seq_indent + 2
    m = {}
    key, rest = first_rest.split(":", 1)
    key = key.strip().strip("\"'")
    rest = rest.strip()
    if rest == "":
        if i + 1 < len(items) and items[i + 1][0] > key_indent:
            val, i = _parse_block(items, i + 1, items[i + 1][0])
            m[key] = val
        else:
            m[key] = None
        i += 1
    else:
        m[key] = _parse_scalar(rest)
        i += 1
    # 解析后续键
    while i < len(items):
        ind, content = items[i]
        if ind < key_indent:
            break
        if ind > key_indent:
            raise ValueError(f"mapping 键缩进不一致：{content!r}")
        if content.startswith("- "):
            break
        if ":" not in content:
            raise ValueError(f"mapping 行缺少冒号：{content!r}")
        k, r = content.split(":", 1)
        k = k.strip().strip("\"'")
        r = r.strip()
        if r == "":
            if i + 1 < len(items) and items[i + 1][0] > key_indent:
                val, i = _parse_block(items, i + 1, items[i + 1][0])
                m[k] = val
            else:
                m[k] = None
                i += 1
        else:
            m[k] = _parse_scalar(r)
            i += 1
    return m, i


def parse_yaml_simple(text: str):
    """解析 YAML 文本，返回顶层结构（dict）。"""
    items = _preprocess(text)
    if not items:
        return {}
    val, idx = _parse_block(items, 0, items[0][0])
    if idx != len(items):
        raise ValueError(f"解析未消费全部内容，停在索引 {idx}")
    return val


# ---------------------------------------------------------------------------
# Skill 发现与 frontmatter 解析
# ---------------------------------------------------------------------------

def discover_skills(root: str):
    """递归发现所有 SKILL.md，返回 (skill 目录名, SKILL.md 路径) 列表。"""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过缓存/临时目录，避免把 vendored 第三方内容当 Skill 扫描。
        dirnames[:] = [
            d for d in dirnames
            if d not in ("__pycache__", ".git", "node_modules", ".venv")
        ]
        if "SKILL.md" in filenames:
            rel = os.path.relpath(dirpath, root)
            found.append((rel.replace(os.sep, "/"), os.path.join(dirpath, "SKILL.md")))
    return sorted(found)


def parse_frontmatter(md_path: str):
    """提取 SKILL.md frontmatter 中的 name/description。返回 (meta, error)。"""
    try:
        # 使用 utf-8-sig 自动剥离 BOM，避免把带 BOM 的合法 frontmatter 误判为缺失。
        with open(md_path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as e:
        return None, f"无法读取：{e}"
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "缺少 frontmatter 起始行 '---'"
    meta = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            return meta, None
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("\"'")
    return meta, "frontmatter 未闭合"


# ---------------------------------------------------------------------------
# 路径引用提取与分类
# ---------------------------------------------------------------------------

def _looks_like_path(tok: str) -> bool:
    return ("/" in tok or "\\" in tok) or tok.startswith(_LOCAL_PREFIXES)


def extract_path_refs(content: str):
    """从 SKILL.md 正文提取候选路径引用，返回去重集合。"""
    refs = set()
    # Markdown 链接 [text](path)
    for m in re.finditer(r"\]\(([^)\s]+)\)", content):
        refs.add(m.group(1))
    # 反引号内容
    for m in re.finditer(r"`([^`]+)`", content):
        t = m.group(1).strip()
        if _looks_like_path(t):
            refs.add(t)
    # 已知本地/目标前缀的裸路径（仅 ASCII 字符，避免误抓中文短语）
    for m in re.finditer(
        r"\b((?:references|scripts|engine|docs|assets|agents|examples)/[A-Za-z0-9._/\-*]+)",
        content,
    ):
        refs.add(m.group(1))
    # 盘符绝对路径 / UNC
    for m in re.finditer(r"\b([A-Za-z]:[\\/][^\s`\"'()\[\]<>,;]+)", content):
        refs.add(m.group(1))
    return refs


def _find_repo_relative(root: str, rel: str):
    """在仓库内查找是否存在某个 skill 目录下的同名相对路径。返回匹配的绝对路径列表。"""
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        if "__pycache__" in dirpath or ".git" in dirpath:
            continue
        candidate = os.path.join(dirpath, rel)
        if os.path.exists(candidate):
            matches.append(candidate)
    return matches


def classify_path(ref: str, skill_dir: str, root: str):
    """把单个路径引用分类，返回 (类别, 是否存在, 说明)。"""
    ref = ref.strip().strip("`")
    # 通配符、占位符和由多个资源目录组成的模式不是单个文件依赖。
    # 例如 references/zm_api_*.md 不应被截断为 references/zm_api_ 后判缺失。
    if any(token in ref for token in ("*", "<", ">", "YYYY", "...")):
        return "pattern_reference", False, "通配符/占位符模式（不检查单个文件）"
    if re.match(r"^[A-Za-z]:[\\/]", ref) or ref.startswith("\\\\"):
        return "external_path", False, "外部绝对路径（本工具不检查）"
    if ref.startswith("../") or ref.startswith("..\\"):
        # 相对 Skill 目录向上解析，再检查相对仓库根的存在性。
        abs_path = os.path.normpath(os.path.join(skill_dir, ref))
        return "repository_dependency", os.path.exists(abs_path), "跨目录仓库依赖"
    # `docs/` may be a Skill-local reference (for example the bundled
    # version-check instructions) or a target repository output.  Resolve the
    # local file first so existing resources are not reported as missing.
    if ref.startswith("docs/"):
        local_docs = os.path.join(skill_dir, ref)
        if os.path.exists(local_docs):
            return "skill_local", True, "Skill 本地资源"
    if ref.startswith(_TARGET_PREFIXES):
        return "target_path", os.path.exists(os.path.join(root, ref)), "目标输出/仓库模板路径"
    if ref.startswith(_LOCAL_PREFIXES):
        local = os.path.join(skill_dir, ref)
        if os.path.exists(local):
            return "skill_local", True, "Skill 本地资源"
        repo_matches = _find_repo_relative(root, ref)
        if repo_matches:
            return "repository_dependency", True, "指向其他 Skill 的本地资源（引用可能跨 Skill）"
        skill_name = os.path.basename(skill_dir).casefold()
        if skill_name in _ILLUSTRATIVE_SKILL_DIRS:
            return "illustrative_example", False, "示例路径（不作为运行依赖）"
        return "unresolved", False, "本地资源引用但仓库内未找到"
    if "example" in ref.lower():
        return "example_path", False, "示例路径（不检查）"
    return "external_path", False, "外部/目标路径（不检查）"


def external_target_exists(root: str, ref: str) -> bool:
    """Resolve a target path through the declared repository dependency manifest."""
    manifest = os.path.join(root, "skill-dependencies.yaml")
    if not os.path.isfile(manifest):
        return False
    try:
        with open(manifest, "r", encoding="utf-8") as fh:
            data = parse_yaml_simple(fh.read()) or {}
    except (OSError, ValueError):
        return False
    for item in data.get("dependencies", []) if isinstance(data, dict) else []:
        if not isinstance(item, dict) or item.get("kind") != "repository_path":
            continue
        provider = str(item.get("provider", "")).strip()
        if not (re.match(r"^[A-Za-z]:[\\/]", provider) or provider.startswith("\\\\")):
            continue
        base = os.path.normpath(provider)
        for declared in item.get("paths", []) if isinstance(item.get("paths"), list) else []:
            declared = str(declared).replace("/", os.sep).replace("\\", os.sep).rstrip(os.sep)
            if ref.rstrip("/").rstrip("\\") == declared.replace(os.sep, "/"):
                return os.path.exists(os.path.join(base, declared))
            if ref.rstrip("/").rstrip("\\").startswith(declared.replace(os.sep, "/") + "/"):
                return os.path.exists(os.path.join(base, ref.replace("/", os.sep)))
    return False


# ---------------------------------------------------------------------------
# 缓存与临时文件检测
# ---------------------------------------------------------------------------

def find_cache_candidates(root: str):
    """检测缓存、临时文件与编译产物，只返回列表，不删除。"""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath:
            dirnames[:] = []
            continue
        for d in list(dirnames):
            if d == "__pycache__" or d.endswith(".egg-info"):
                hits.append(os.path.relpath(os.path.join(dirpath, d), root))
        for f in filenames:
            if any(p in f for p in _CACHE_PATTERNS):
                hits.append(os.path.relpath(os.path.join(dirpath, f), root))
    return sorted(hits)


def check_disposition_hashes(root: str, discovered, strict: bool = False):
    """Check skill-disposition.yaml source_hash values against local SKILL.md files."""
    path = os.path.join(root, "skill-disposition.yaml")
    if not os.path.exists(path):
        return [], [], {"present": False, "count": 0, "drift": []}

    errors: list[str] = []
    warnings: list[str] = []
    drift: list[str] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = parse_yaml_simple(fh.read()) or {}
    except Exception as exc:
        return [f"skill-disposition.yaml 解析失败：{exc}"], [], {
            "present": True,
            "count": 0,
            "drift": [],
        }

    entries = data.get("skills", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        return ["skill-disposition.yaml 缺少 skills 列表"], [], {
            "present": True,
            "count": 0,
            "drift": [],
        }

    disposition_paths: set[str] = set()
    for item in entries:
        if not isinstance(item, dict):
            errors.append("skill-disposition.yaml 存在非 mapping 条目")
            continue
        rel = str(item.get("path", "")).replace("\\", "/")
        expected = str(item.get("source_hash", ""))
        if not rel:
            errors.append("skill-disposition.yaml 条目缺少 path")
            continue
        disposition_paths.add(rel)
        skill_file = os.path.join(root, rel, "SKILL.md")
        if not os.path.isfile(skill_file):
            message = f"skill-disposition.yaml：path 不存在 SKILL.md：{rel}"
            (errors if strict else warnings).append(message)
            continue
        actual = hashlib.sha256(open(skill_file, "rb").read()).hexdigest()[:16]
        if expected != actual:
            message = f"skill-disposition.yaml：{rel} source_hash 漂移（记录 {expected or '<empty>'}，实际 {actual}）"
            drift.append(rel)
            (errors if strict else warnings).append(message)

    discovered_paths = {rel for rel, _ in discovered}
    if disposition_paths != discovered_paths:
        missing = sorted(discovered_paths - disposition_paths)
        stale = sorted(disposition_paths - discovered_paths)
        warnings.append(
            "skill-disposition.yaml 与磁盘 Skill 集合漂移："
            f"missing={missing[:5]} stale={stale[:5]}"
        )
    return errors, warnings, {
        "present": True,
        "count": len(entries),
        "drift": drift,
    }


# ---------------------------------------------------------------------------
# 主检查逻辑
# ---------------------------------------------------------------------------

def run_doctor(root: str, strict: bool = False):
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []
    unresolved_paths: list[str] = []
    dependency_checks: list[dict] = []
    release_validation: dict = {"status": "not_run"}
    dependency_validation: dict = {"status": "not_run"}
    behavior_validation: dict = {"status": "not_run"}

    registry_path = os.path.join(root, "skill-registry.yaml")
    registry = {}
    registry_count = 0
    if not os.path.exists(registry_path):
        errors.append("缺少 skill-registry.yaml")
    else:
        try:
            with open(registry_path, "r", encoding="utf-8") as fh:
                registry = parse_yaml_simple(fh.read()) or {}
        except Exception as e:
            errors.append(f"skill-registry.yaml 解析失败：{e}")
            registry = {}

    registry_scope = registry.get("registry_scope", "full") if isinstance(registry, dict) else "full"
    dependency_manifest = registry.get("dependency_manifest") if isinstance(registry, dict) else None
    if dependency_manifest and not os.path.exists(os.path.join(root, str(dependency_manifest))):
        errors.append(f"registry 声明的 dependency_manifest 不存在：{dependency_manifest}")
    release_manifest = registry.get("release_manifest") if isinstance(registry, dict) else None
    if release_manifest and not os.path.exists(os.path.join(root, str(release_manifest))):
        errors.append(f"registry 声明的 release_manifest 不存在：{release_manifest}")
    behavior_eval_manifest = registry.get("behavior_eval_manifest") if isinstance(registry, dict) else None
    if behavior_eval_manifest and not os.path.exists(os.path.join(root, str(behavior_eval_manifest))):
        errors.append(f"registry 声明的 behavior_eval_manifest 不存在：{behavior_eval_manifest}")
    delivery_contract = registry.get("delivery_contract") if isinstance(registry, dict) else None
    if delivery_contract and not os.path.exists(os.path.join(root, str(delivery_contract))):
        errors.append(f"registry 声明的 delivery_contract 不存在：{delivery_contract}")
    skills = registry.get("skills", []) if isinstance(registry, dict) else []
    registry_count = len(skills) if isinstance(skills, list) else 0

    # Manifest checks are intentionally separate from frontmatter checks. A
    # Skill tree can be locally readable while its published hash or external
    # dependency contract is stale; those are release-governance failures.
    try:
        from validate_skill_release import validate as validate_release
        from validate_skill_dependencies import validate as validate_dependencies
        from validate_behavior_evals import validate as validate_behavior_evals

        release_validation = validate_release(Path(root).resolve())
        dependency_validation = validate_dependencies(Path(root).resolve())
        behavior_validation = validate_behavior_evals(Path(root).resolve())
        if release_validation.get("status") == "fail":
            errors.extend([f"发布清单：{message}" for message in release_validation.get("errors", [])])
        if dependency_validation.get("status") == "fail":
            errors.extend([f"依赖清单：{message}" for message in dependency_validation.get("errors", [])])
        dependency_checks = dependency_validation.get("checks", [])
        if behavior_validation.get("status") == "fail":
            errors.extend([f"行为回归登记：{message}" for message in behavior_validation.get("errors", [])])
        warnings.extend([f"行为回归登记：{message}" for message in behavior_validation.get("warnings", [])])
        for check in dependency_checks:
            if check.get("status") == "missing":
                warnings.append(
                    f"外部依赖 {check.get('id')} 缺失（policy={check.get('missing_policy')}）："
                    f"{check.get('missing_paths')}"
                )
    except Exception as exc:
        errors.append(f"发布/依赖清单校验器加载失败：{exc}")

    # 注册表字段与重复检查
    required_fields = [
        "id", "path", "layer", "priority", "triggers", "excludes",
        "escalates_to", "supports", "required_contracts", "outputs",
        "aliases", "version", "status", "role", "routable",
        "dependencies",
    ]
    support_policy = registry.get("support_policy", {}) if isinstance(registry, dict) else {}
    support_max = support_policy.get("default_max", 2) if isinstance(support_policy, dict) else 2
    try:
        support_max = int(support_max)
    except (TypeError, ValueError):
        errors.append("skill-registry.yaml 的 support_policy.default_max 必须是整数")
        support_max = 2
    seen_ids: dict[str, str] = {}
    seen_paths: dict[str, str] = {}
    seen_aliases: dict[str, str] = {}
    registry_ids: set[str] = set()
    registry_aliases: set[str] = set()

    if isinstance(skills, list):
        for s in skills:
            if not isinstance(s, dict):
                errors.append("registry 中存在非映射类型的 skill 条目")
                continue
            sid = s.get("id")
            if not sid:
                errors.append("registry 存在缺少 id 的条目")
                continue
            registry_ids.add(str(sid))
            if sid in seen_ids:
                errors.append(f"重复的 Skill ID：{sid}")
            seen_ids[sid] = s.get("path", "")
            p = s.get("path")
            if p:
                if p in seen_paths:
                    errors.append(f"重复的 Skill path：{p}")
                seen_paths[p] = sid
                skill_entry = os.path.join(root, str(p), "SKILL.md")
                if not os.path.isfile(skill_entry):
                    errors.append(f"Skill {sid} 的 path 不存在 SKILL.md：{p}")
            for a in s.get("aliases", []) or []:
                registry_aliases.add(str(a))
                if a in seen_aliases:
                    errors.append(f"重复的 alias：{a}（冲突 Skill：{sid} 与 {seen_aliases[a]}）")
                seen_aliases[a] = str(sid)
            missing = [f for f in required_fields if f not in s]
            if missing:
                errors.append(f"Skill {sid} 缺少必要字段：{', '.join(missing)}")
            if s.get("layer") not in ("router", "domain", "delivery", "engineering", "knowledge"):
                errors.append(f"Skill {sid} 的 layer 非法：{s.get('layer')}")
            if s.get("status") not in ("active", "deprecated", "experimental"):
                errors.append(f"Skill {sid} 的 status 非法：{s.get('status')}")
            if s.get("role") not in ("primary", "support", "reference", "meta"):
                errors.append(f"Skill {sid} 的 role 非法：{s.get('role')}")
            if not isinstance(s.get("routable"), (bool, str)) or str(s.get("routable")).lower() not in ("true", "false"):
                errors.append(f"Skill {sid} 的 routable 必须是 true/false：{s.get('routable')}")
            if s.get("role") == "primary" and str(s.get("routable")).lower() != "true":
                errors.append(f"主入口 Skill {sid} 必须 routable=true")
            if s.get("role") != "primary" and str(s.get("routable")).lower() == "true":
                warnings.append(f"非主入口 Skill {sid} 标记为 routable=true，请确认是否应参与主路由")
            supports = s.get("supports", []) or []
            if isinstance(supports, list) and len(supports) > support_max:
                reason = s.get("support_override_reason")
                if not support_policy.get("override_requires_reason") or not reason:
                    errors.append(
                        f"Skill {sid} 的 supports={len(supports)} 超过默认上限 {support_max}，"
                        "且没有 support_override_reason"
                    )
            # 契约引用存在性
            for c in s.get("required_contracts", []) or []:
                if not os.path.exists(os.path.join(root, str(c))):
                    errors.append(f"Skill {sid} 引用的契约文件不存在：{c}")
    else:
        errors.append("skill-registry.yaml 缺少 skills 列表")

    # 发现所有 SKILL.md
    discovered = discover_skills(root)
    skill_count = len(discovered)

    # 全量资产台账与路由注册表分离；若存在 inventory，则检查它是否仍与
    # 磁盘上的 SKILL.md 集合一致，避免把过期清单当作当前事实。
    inventory_path = os.path.join(root, "skill-inventory.yaml")
    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, "r", encoding="utf-8") as fh:
                inventory = parse_yaml_simple(fh.read()) or {}
            inventory_skills = inventory.get("skills", []) if isinstance(inventory, dict) else []
            inventory_paths = {
                str(item.get("path")).replace("\\", "/")
                for item in inventory_skills
                if isinstance(item, dict) and item.get("path")
            }
            discovered_paths = {rel for rel, _ in discovered}
            if inventory.get("skill_count") not in (None, str(skill_count), skill_count):
                warnings.append(
                    f"skill-inventory.yaml skill_count={inventory.get('skill_count')} "
                    f"与磁盘发现数 {skill_count} 不一致，请重新生成"
                )
            if inventory_paths != discovered_paths:
                missing = sorted(discovered_paths - inventory_paths)
                stale = sorted(inventory_paths - discovered_paths)
                warnings.append(
                    "skill-inventory.yaml 与磁盘 Skill 集合漂移："
                    f"missing={missing[:5]} stale={stale[:5]}"
                )
        except Exception as exc:
            errors.append(f"skill-inventory.yaml 解析失败：{exc}")

    # 处置台账中的 source_hash 是版本锁定依据；默认只警告，strict 下阻断，
    # 这样有意修改 Skill 时必须同步更新台账，而不会把旧记录当作当前版本。
    disposition_errors, disposition_warnings, disposition_meta = check_disposition_hashes(
        root, discovered, strict=strict
    )
    errors.extend(disposition_errors)
    warnings.extend(disposition_warnings)

    # Skill 目录名 / frontmatter name / 注册表 ID 一致性
    registry_all_ids = registry_ids | registry_aliases
    unregistered: set[str] = set()
    unregistered_dirs: set[str] = set()
    registry_paths: set[str] = set()
    if isinstance(skills, list):
        registry_paths = {
            str(item.get("path", "")).replace("\\", "/")
            for item in skills
            if isinstance(item, dict) and item.get("path")
        }
    for rel_dir, md_path in discovered:
        dir_name = rel_dir.split("/")[-1]
        meta, err = parse_frontmatter(md_path)
        if err:
            errors.append(f"{rel_dir}/SKILL.md：{err}")
            continue
        if meta is None:
            continue
        name = meta.get("name")
        desc = meta.get("description")
        if not name:
            errors.append(f"{rel_dir}/SKILL.md：frontmatter 缺少 name")
        if not desc:
            errors.append(f"{rel_dir}/SKILL.md：frontmatter 缺少 description")
        if name and registry_all_ids and name not in registry_all_ids:
            unregistered.add(f"{rel_dir}: frontmatter={name}")
        if dir_name not in registry_all_ids and rel_dir not in registry_paths:
            unregistered.add(f"{rel_dir}: directory={dir_name}")
            unregistered_dirs.add(rel_dir)

        # 正文路径引用检查
        try:
            with open(md_path, "r", encoding="utf-8-sig") as fh:
                body = fh.read()
        except OSError as e:
            errors.append(f"{rel_dir}/SKILL.md 读取失败：{e}")
            continue

        # Markdown 代码块成对
        fence_count = body.count("```")
        if fence_count % 2 != 0:
            errors.append(f"{rel_dir}/SKILL.md：Markdown 代码块不成对（{fence_count} 个围栏）")

        # 路径引用
        skill_dir = os.path.dirname(md_path)
        for ref in extract_path_refs(body):
            cat, exists, note = classify_path(ref, skill_dir, root)
            if cat == "skill_local":
                if not exists:
                    errors.append(f"{rel_dir}：本地必需资源缺失：{ref}")
            elif cat == "unresolved":
                unresolved_paths.append(f"{rel_dir}::{ref}")
                if strict:
                    errors.append(f"{rel_dir}：未解决的本地资源引用：{ref}（strict）")
                else:
                    warnings.append(f"{rel_dir}：未解决的本地资源引用：{ref}")
            elif cat == "repository_dependency" and not exists:
                warnings.append(f"{rel_dir}：仓库依赖不存在：{ref}")
            elif cat == "target_path" and not exists:
                if not external_target_exists(root, ref):
                    warnings.append(f"{rel_dir}：目标输出路径不存在（仓库外模板）：{ref}")
            elif cat in ("pattern_reference", "illustrative_example"):
                # 示例和通配符不是运行依赖，也不应把 JSON suggestions 淹没。
                # 这类内容只在需要逐项排查时通过正文搜索发现。
                continue

    if unregistered:
        if registry_scope == "core_router":
            warnings.append(
                f"发现 {len(unregistered_dirs)} 个未登记 Skill 目录；registry_scope=core_router，"
                "它们仅作为发现结果，不参与主入口路由。"
            )
        else:
            warnings.extend([f"{item}（未登记）" for item in sorted(unregistered)])

    cache_candidates = find_cache_candidates(root)
    if cache_candidates:
        suggestions.append(f"发现 {len(cache_candidates)} 个缓存/临时/编译产物，仅报告未删除")

    if errors:
        status = "fail"
    elif warnings:
        status = "warning"
    else:
        status = "pass"

    return {
        "status": status,
        "root": os.path.abspath(root),
        "skill_count": skill_count,
        "registry_count": registry_count,
        "disposition_count": disposition_meta.get("count", 0),
        "disposition_hash_drift": disposition_meta.get("drift", []),
        "release_validation": release_validation,
        "dependency_validation": dependency_validation,
        "behavior_validation": behavior_validation,
        "dependency_checks": dependency_checks,
        "errors": errors,
        "warnings": warnings,
        "unresolved_paths": unresolved_paths,
        "cache_candidates": cache_candidates,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, suggestions


def _dump_yaml(obj, indent=0):
    """把简单 dict/list/scalar 序列化为 YAML 文本（仅本工具输出用）。"""
    pad = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(_dump_yaml(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{pad}{k}: []")
            else:
                lines.append(f"{pad}{k}: {v}")
        return "\n".join(lines)
    if isinstance(obj, list):
        if not obj:
            return f"{pad}[]"
        lines = []
        for item in obj:
            lines.append(f"{pad}- {item}")
        return "\n".join(lines)
    return f"{pad}{obj}"


def main(argv=None):
    _configure_stdout()
    parser = argparse.ArgumentParser(description="SharedSKILLS 只读体检工具")
    parser.add_argument("--root", default=".", help="SharedSKILLS 根目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    parser.add_argument("--strict", action="store_true", help="把未解决的本地资源引用判为失败")
    args = parser.parse_args(argv)

    result, suggestions = run_doctor(args.root, strict=args.strict)

    if args.json:
        payload = dict(result)
        payload["suggestions"] = suggestions
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        payload = dict(result)
        payload["suggestions"] = suggestions
        print(_dump_yaml(payload))

    if result["status"] == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
