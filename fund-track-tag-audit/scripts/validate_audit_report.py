#!/usr/bin/env python3
"""Validate a single-fund audit report Markdown against the required template.

报告采用混合格式：「基金记录（zmdata）」和「字段审核」章节允许 Markdown 表格，
其余章节使用列表格式。校验聚焦于六段结构和关键内容规则。

Exits 0 on pass, 1 on errors, 2 on warnings-only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "结论摘要",
    "基金记录（zmdata）",
    "字段审核",
    "策略画像",
    "关键证据",
    "口径说明",
]

VALID_PRIORITIES = {"P1", "P2"}
VALID_EVIDENCE_STRENGTHS = {"高", "中", "低"}
AUDIT_FIELDS = ("strategyType", "raceName", "fundType")
TABLE_ALLOWED_SECTIONS = ["基金记录（zmdata）", "字段审核"]
PORTRAIT_ROWS = [
    "一级赛道",
    "细分赛道",
    "策略属性",
    "收益来源",
    "投资范围",
    "风险画像",
    "标签映射",
]

SPECULATIVE_PATTERNS = [
    re.compile(r"可能为旧版"),
    re.compile(r"可能已废弃"),
    re.compile(r"可能是旧版"),
    re.compile(r"可能是已废弃"),
    re.compile(r"可能已被废弃"),
    re.compile(r"可能为已废弃"),
]

INDIRECT_FUND_TYPE_PATTERNS = [
    re.compile(r"来自同系列推断"),
    re.compile(r"同系列推断"),
    re.compile(r"间接证据"),
    re.compile(r"无直接证据"),
    re.compile(r"缺少直接"),
    re.compile(r"依赖同系列"),
    re.compile(r"全部来自同.*系列"),
    re.compile(r"基准体系不一致"),
    re.compile(r"杠杆.*不一致"),
    re.compile(r"波动特征未直接验证"),
]

_errors: list[str] = []
_warnings: list[str] = []


def _section_chunk(content: str, section: str) -> str:
    pattern = re.compile(rf"^###\s+{re.escape(section)}", re.MULTILINE)
    m = pattern.search(content)
    if m is None:
        return ""
    idx = m.start()

    chunk = content[idx:]
    next_section: tuple[int, str] | None = None
    for candidate in REQUIRED_SECTIONS:
        if candidate == section:
            continue
        candidate_pattern = re.compile(rf"^###\s+{re.escape(candidate)}", re.MULTILINE)
        cm = candidate_pattern.search(chunk)
        if cm is not None and (next_section is None or cm.start() < next_section[0]):
            next_section = (cm.start(), candidate)
    if next_section:
        chunk = chunk[: next_section[0]]
    return chunk


def _check_sections(content: str) -> None:
    for section in REQUIRED_SECTIONS:
        if section not in content:
            _errors.append(f"缺少必需章节：「{section}」")


def _build_allowed_line_set(content: str) -> set[int]:
    allowed: set[int] = set()
    for section in TABLE_ALLOWED_SECTIONS:
        chunk = _section_chunk(content, section)
        if not chunk:
            continue
        idx = content.find(chunk)
        if idx == -1:
            continue
        prefix = content[:idx]
        start_line = prefix.count("\n") + 1
        end_line = start_line + chunk.count("\n")
        allowed.update(range(start_line, end_line + 1))
    return allowed


def _check_no_markdown_tables(content: str) -> None:
    allowed_lines = _build_allowed_line_set(content)
    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if i not in allowed_lines:
                _errors.append(
                    "Markdown 表格仅允许出现在「基金记录（zmdata）」和「字段审核」章节中；"
                    "其他章节请改用列表格式"
                )
                return


def _check_portrait_format(content: str, strict: bool = False) -> None:
    chunk = _section_chunk(content, "策略画像")
    if not chunk:
        return

    if "```" in chunk:
        _errors.append("「策略画像」不应使用代码块（```）；必须为 7 行列表")

    portrait_rows_found = [dim for dim in PORTRAIT_ROWS if dim in chunk]
    missing = [d for d in PORTRAIT_ROWS if d not in chunk]
    found_count = len(portrait_rows_found)
    total = len(PORTRAIT_ROWS)

    if found_count < 6:
        msg = f"「策略画像」缺少以下维度: {', '.join(missing)}"
        if strict:
            _errors.append(msg)
        else:
            _warnings.append(msg)
    elif found_count < total and strict:
        _errors.append(
            f"「策略画像」缺少以下维度: {', '.join(missing)}（strict 要求完整 7 维）"
        )


def _check_evidence_priorities(content: str) -> None:
    """检查「关键证据」中是否出现无效优先级 P3/P4 等。

    匹配 **P3**、P3、**P4** 等格式。
    """
    chunk = _section_chunk(content, "关键证据")
    if not chunk:
        return

    priority_pattern = re.compile(r"(?:\*\*)?P(\d)(?:\*\*)?")
    for match in priority_pattern.finditer(chunk):
        pri = f"P{match.group(1)}"
        if pri not in VALID_PRIORITIES:
            _errors.append(f"「关键证据」中出现了无效优先级 {pri}（只允许 P1/P2）")


def _check_evidence_strength(content: str, strict: bool = False) -> None:
    lines = [line for line in content.splitlines() if "证据强度" in line]
    if not lines:
        _errors.append("「结论摘要」需明确写出证据强度，且只能为 高/中/低")
        return

    for line in lines:
        match = re.search(
            r"(?:\*\*)?证据强度(?:\*\*)?\s*[：:]\s*(?:\*\*)?\s*([^*，,。；;\s<]+)", line
        )
        if not match:
            _errors.append("证据强度格式无效，应写为「证据强度：**高/中/低**」")
            continue
        value = match.group(1).strip("*` ")
        if value not in VALID_EVIDENCE_STRENGTHS:
            _errors.append(f"证据强度只能使用 高/中/低，当前为「{value}」")
            continue
        if strict and "**" not in line:
            _warnings.append("证据强度建议使用加粗格式「**高/中/低**」")


def _check_speculative_language(content: str, strict: bool = False) -> None:
    for pattern in SPECULATIVE_PATTERNS:
        for match in pattern.finditer(content):
            msg = (
                f"含无证据推测表述: 「{match.group()}」"
                "（如果不是人工复核假设，请删除或标注为假设）"
            )
            if strict:
                _errors.append(msg)
            else:
                _warnings.append(msg)


def _check_table_cell_breaks(content: str) -> None:
    """检测表格单元格内是否误用物理回车而非 <br>。

    在一个表格段内（以 |---| 分隔行为标志），表格行的数量必须与分隔行数量匹配。
    如果在两个 |---| 分隔行之间出现了不以 | 开头的非空行，说明表格被物理回车截断了。
    """
    lines = content.splitlines()
    in_table = False
    sep_count = 0
    rows_since_sep = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|---"):
            in_table = True
            sep_count += 1
            rows_since_sep = 0
            continue
        if in_table and stripped.startswith("|") and stripped.endswith("|"):
            rows_since_sep += 1
            continue
        if in_table and stripped == "":
            in_table = False
            continue
        if in_table and not stripped.startswith("|") and stripped != "":
            _errors.append(
                f"第 {i + 1} 行：表格单元格内疑似使用了物理回车，"
                "如需换行请使用 `<br>` 标签"
            )
            in_table = False


def _parse_table_rows(chunk: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in chunk.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _field_audit_rows(content: str) -> dict[str, list[str]]:
    chunk = _section_chunk(content, "字段审核")
    rows: dict[str, list[str]] = {}
    for cells in _parse_table_rows(chunk):
        if len(cells) < 4:
            continue
        field = re.sub(r"[`*\s]", "", cells[0])
        if field in AUDIT_FIELDS:
            rows[field] = cells
    return rows


def _check_required_audit_rows(content: str, strict: bool = False) -> None:
    rows = _field_audit_rows(content)
    missing = [field for field in AUDIT_FIELDS if field not in rows]
    if not missing:
        return
    msg = f"「字段审核」缺少必审字段行: {', '.join(missing)}"
    if strict:
        _errors.append(msg)
    else:
        _warnings.append(msg)


def _check_race_name_suggestion(content: str) -> None:
    row = _field_audit_rows(content).get("raceName")
    if row is None:
        return

    conclusion = row[2]
    row_text = " ".join(row)
    needs_suggestion = any(
        label in conclusion for label in ("需补充", "需修正", "需复核补充")
    )
    if not needs_suggestion:
        return

    suggestion_matches = re.findall(r"建议\s*[:：]\s*([^<|)）]+)", row_text)
    if not suggestion_matches:
        _errors.append("`raceName` 为补充/修正/复核结论时必须写出唯一「建议: <候选值>」")
        return
    if len(suggestion_matches) > 1:
        _errors.append("`raceName` 只能出现一个首选建议值；比较论证请移至口径说明")
        return

    candidate = suggestion_matches[0].strip(" *`。；;，,")
    if not candidate or candidate in {"待人工确认", "人工确认"}:
        _errors.append("`raceName` 的建议值不能为空或仅写「待人工确认」")
        return
    if re.search(r"(、|，|,|；|;|\s或\s|\sor\s)", candidate, re.I):
        _errors.append(
            "`raceName` 的建议值疑似包含多个候选；字段审核中必须保留唯一首选"
        )


def _check_fund_type_conservative(content: str) -> None:
    row = _field_audit_rows(content).get("fundType")
    if row is None:
        return

    conclusion = row[2]
    row_text = " ".join(row)
    has_indirect_risk = any(
        pattern.search(row_text) for pattern in INDIRECT_FUND_TYPE_PATTERNS
    )
    if not has_indirect_risk:
        return

    if "待人工确认" not in row_text:
        _errors.append(
            "`fundType` 涉及同系列/间接/混杂推断时必须标注「待人工确认」"
        )
    if re.search(r"建议\s*[:：]", conclusion):
        _errors.append(
            "`fundType` 涉及同系列/间接/混杂推断时不得在结论单元格给出具体候选值"
        )


def _check_inference_boundary_first(content: str) -> None:
    chunk = _section_chunk(content, "口径说明")
    if not chunk:
        return

    first_item = ""
    for line in chunk.splitlines()[1:]:
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        first_item = stripped
        break

    if not first_item:
        _errors.append("「口径说明」必须包含列表项，第一条为「推论边界风险」")
        return
    if not first_item.startswith("- "):
        _errors.append("「口径说明」必须使用列表格式，第一条为「推论边界风险」")
        return
    if "推论边界风险" not in first_item:
        _errors.append("「口径说明」第一条必须单独开列「推论边界风险」")
        return
    if "**推论边界风险**" not in first_item:
        _errors.append("「推论边界风险」必须使用加粗格式：`- **推论边界风险**：...`")


def _check_evidence_chain(content: str, strict: bool = False) -> None:
    """检查「关键证据」中是否包含证据链小结。

    仅当关键证据 ≥ 3 条且有时序/逻辑演进关系时给出警告（非强制），
    因为单份证据场景不需要小结。
    """
    chunk = _section_chunk(content, "关键证据")
    if not chunk:
        return

    priority_lines = [
        line for line in chunk.splitlines() if line.strip().startswith("**P")
    ]
    has_chain = "证据链小结" in chunk

    if len(priority_lines) >= 3 and not has_chain:
        _warnings.append(
            "「关键证据」含 3 条以上 P1/P2 证据，建议添加「📌 证据链小结」"
            "按时间线或逻辑线串联关键发现"
        )


def validate_markdown(
    content: str, strict: bool = False
) -> tuple[list[str], list[str]]:
    global _errors, _warnings
    _errors = []
    _warnings = []

    _check_sections(content)
    _check_no_markdown_tables(content)
    _check_table_cell_breaks(content)
    _check_required_audit_rows(content, strict=strict)
    _check_race_name_suggestion(content)
    _check_fund_type_conservative(content)
    _check_inference_boundary_first(content)
    _check_portrait_format(content, strict=strict)
    _check_evidence_priorities(content)
    _check_evidence_strength(content, strict=strict)
    _check_evidence_chain(content, strict=strict)
    _check_speculative_language(content, strict=strict)

    return _errors, _warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a single-fund audit report Markdown."
    )
    parser.add_argument(
        "report_path", nargs="?", help="Path to the report Markdown file"
    )
    parser.add_argument(
        "--content", help="Report content as a string (alternative to file)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit code 1 instead of 2)",
    )
    args = parser.parse_args()

    if args.content:
        text = args.content
    elif args.report_path:
        try:
            text = Path(args.report_path).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"无法读取报告文件：{args.report_path}；{exc}", file=sys.stderr)
            return 1
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("请通过文件路径、--content 参数或 stdin 传入报告内容", file=sys.stderr)
        return 1

    errors, warnings = validate_markdown(text, strict=args.strict)

    if errors:
        print("=== 错误 ===")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print("=== 警告 ===")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        return 1
    if warnings:
        return 2 if not args.strict else 1
    print("✅ 报告格式校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
