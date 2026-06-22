"""从 zm_fund_group_ids.md 加载受控词表，为标签提取和审核提供映射。

覆盖范围：zm样本库（策略类型 + 波动层级）和市场跟踪池（细分赛道）。
不覆盖：zmdata 分类层级（10220/10225/10230）、标尺库（1000000xxx）、内部运营标注等系统内置标签。
未命中词表的 labelID 不表示数据异常，仅表示该 ID 不属于样本库或跟踪池类目。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


_VOCAB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "zmdata-data-api" / "references" / "zm_fund_group_ids.md"
_VOCAB_PATH_ALT = Path(__file__).resolve().parent.parent / ".." / "zmdata-data-api" / "references" / "zm_fund_group_ids.md"
_FALLBACK_PATHS = [
    _VOCAB_PATH,
    _VOCAB_PATH_ALT,
]

SAMPLE_DB_PREFIX = "样本库"
TRACK_POOL_PREFIX = "跟踪池"

_SAMPLE_DB_STRATEGY = {
    20201: ("股票多头", "strategyType"),
    20202: ("债券", "strategyType"),
    20203: ("CTA", "strategyType"),
    20210: ("市场中性", "strategyType"),
}

_TRACK_POOL_PARENT = {
    42201: ("股票多头", "strategyType"),
    42202: ("债券", "strategyType"),
    42203: ("CTA", "strategyType"),
    42205: ("混合", "strategyType"),
    42210: ("市场中性", "strategyType"),
}


@dataclass
class LabelEntry:
    label_id: int
    name: str
    category: str
    parent: str
    system: str = SAMPLE_DB_PREFIX


@dataclass
class Vocabulary:
    entries: list[LabelEntry] = field(default_factory=list)
    _by_name: dict[str, list[LabelEntry]] = field(default_factory=dict)
    _by_id: dict[int, LabelEntry] = field(default_factory=dict)

    def lookup_by_name(self, name: str) -> list[LabelEntry]:
        return self._by_name.get(name, [])

    def lookup_by_id(self, label_id: int) -> LabelEntry | None:
        return self._by_id.get(label_id)

    def search(self, text: str) -> list[LabelEntry]:
        hits: list[LabelEntry] = []
        seen: set[int] = set()
        for entry in self.entries:
            if entry.label_id in seen:
                continue
            if _match_label_name(entry.name, text):
                hits.append(entry)
                seen.add(entry.label_id)
        return hits

    def id_to_names(self, label_ids: list[int]) -> list[str]:
        result: list[str] = []
        for lid in label_ids:
            entry = self._by_id.get(lid)
            if entry:
                result.append(entry.name)
            else:
                result.append(f"<{lid}>")
        return result

    def is_risk(self, name: str) -> bool:
        entries = self._by_name.get(name, [])
        return any(e.category == "fundType" for e in entries)

    def is_race(self, name: str) -> bool:
        entries = self._by_name.get(name, [])
        return any(e.category == "raceName" for e in entries)

    def is_strategy_type(self, name: str) -> bool:
        entries = self._by_name.get(name, [])
        return any(e.category == "strategyType" for e in entries)

    def parent_for(self, name: str) -> str:
        entries = self._by_name.get(name, [])
        if entries:
            return entries[0].parent
        return ""

    @property
    def all_strategy_types(self) -> list[str]:
        return sorted({e.name for e in self.entries if e.category == "strategyType"})

    @property
    def all_race_names(self) -> list[str]:
        return sorted({e.name for e in self.entries if e.category == "raceName"})

    @property
    def all_risk_labels(self) -> list[str]:
        return sorted({e.name for e in self.entries if e.category == "fundType"})


def _match_label_name(label: str, text: str) -> bool:
    if len(label) < 3:
        return False
    return text.lower() in label.lower()


@lru_cache(maxsize=1)
def load_vocabulary() -> Vocabulary:
    path = None
    for candidate in _FALLBACK_PATHS:
        if candidate.exists():
            path = candidate
            break
    if path is None:
        raise FileNotFoundError(f"未能找到 zm_fund_group_ids.md，已搜索: {_FALLBACK_PATHS}")

    text = path.read_text(encoding="utf-8")
    entries: list[LabelEntry] = []

    entries.extend(_parse_sample_db_tables(text))
    entries.extend(_parse_track_pool_tables(text))

    vocab = Vocabulary(entries=sorted(entries, key=lambda e: (e.category, e.name)))
    for entry in vocab.entries:
        vocab._by_name.setdefault(entry.name, []).append(entry)
        vocab._by_id[entry.label_id] = entry

    return vocab


_TABLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|")


def _parse_sample_db_tables(text: str) -> list[LabelEntry]:
    entries: list[LabelEntry] = []
    current_parent: str = ""
    in_sample_db = False
    for line in text.splitlines():
        line_stripped = line.strip()

        if in_sample_db and line_stripped.startswith("## ") and "市场跟踪池" in line_stripped:
            break

        if "## zm样本库" in line_stripped or "## 2." in line_stripped:
            in_sample_db = True
            continue
        if in_sample_db and line_stripped.startswith("## ") and "样本库" not in line_stripped:
            break

        parent_match = re.match(r"^\*\*(.+?)\*\*:\s*$", line_stripped)
        if parent_match:
            raw = parent_match.group(1)
            if raw.startswith("公募"):
                continue
            normalized = raw.replace("私募", "").strip()
            current_parent = normalized
            continue

        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        label_id = int(m.group(1))
        name = m.group(2).strip()

        if name.startswith("公募"):
            continue

        known = _SAMPLE_DB_STRATEGY.get(label_id)
        if known is not None:
            current_parent, _cat = known
            entries.append(LabelEntry(label_id=label_id, name=known[0], category="strategyType", parent=current_parent, system=SAMPLE_DB_PREFIX))
            continue

        parent_map = {
            20101: 20201, 201010: 20201,
            20102: 20202, 201022: 20202,
            20103: 20203, 201034: 20203,
            20110: 20210,
        }
        mapped_parent_id = None
        for prefix, parent_id in parent_map.items():
            if label_id == prefix or str(label_id).startswith(str(prefix)):
                mapped_parent_id = parent_id
                break

        if mapped_parent_id is None:
            for parent_entry in entries:
                if parent_entry.category == "strategyType" and str(label_id).startswith(str(parent_entry.label_id)):
                    mapped_parent_id = parent_entry.label_id
                    break

        if mapped_parent_id is not None:
            parent_name = _SAMPLE_DB_STRATEGY.get(mapped_parent_id, (current_parent,))[0]
        else:
            parent_name = current_parent

        if "波动" in name or "(全部)" in name:
            risk_name = name.split("-")[-1].strip() if "-" in name else name
            if "(全部)" in risk_name:
                risk_name = name
            entries.append(LabelEntry(label_id=label_id, name=risk_name, category="fundType", parent=parent_name, system=SAMPLE_DB_PREFIX))
        else:
            strategy_name = name.replace("(全部)", "").strip()
            if strategy_name and strategy_name != current_parent:
                entries.append(LabelEntry(label_id=label_id, name=strategy_name, category="strategyType", parent=parent_name, system=SAMPLE_DB_PREFIX))

    return entries


def _parse_track_pool_tables(text: str) -> list[LabelEntry]:
    entries: list[LabelEntry] = []
    current_parent: str = ""
    for line in text.splitlines():
        line_stripped = line.strip()

        parent_match = re.match(r"^###\s+(.+?)赛道\s*$", line_stripped)
        if parent_match:
            current_parent = parent_match.group(1).strip()
            continue

        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        label_id = int(m.group(1))
        name = m.group(2).strip()

        prefix_1 = label_id // 100000
        prefix_2 = label_id // 100
        known = _TRACK_POOL_PARENT.get(prefix_2)
        if known is not None:
            current_parent = known[0]
        else:
            known = _TRACK_POOL_PARENT.get(prefix_1)
            if known is not None:
                current_parent = known[0]

        category = "raceName"
        for risk_term in ("高波动", "次高波动", "中波动", "次低波动", "低波动"):
            if risk_term == name:
                category = "fundType"
                break

        entries.append(LabelEntry(label_id=label_id, name=name, category=category, parent=current_parent, system=TRACK_POOL_PREFIX))

    return entries


if __name__ == "__main__":
    import sys

    vocab = load_vocabulary()
    if len(sys.argv) < 2:
        print("usage: python _vocabulary.py <search|lookup|strategy-types|race-names|risk-labels> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not query:
            print("usage: python _vocabulary.py search <keyword>")
            sys.exit(1)
        hits = vocab.search(query)
        for e in hits:
            print(f"[{e.system}] label_id={e.label_id}  name={e.name}  category={e.category}  parent={e.parent}")
        if not hits:
            print("(no matches)")
    elif cmd == "lookup":
        if len(sys.argv) < 3:
            print("usage: python _vocabulary.py lookup <id>  or  lookup <id1,id2,id3>")
            sys.exit(1)
        id_text = sys.argv[2]
        id_strs = [t.strip() for t in id_text.split(",") if t.strip()]
        if not id_strs:
            print("(no ids provided)")
            sys.exit(1)
        for id_str in id_strs:
            try:
                lid = int(id_str)
            except ValueError:
                print(f"(invalid: {id_str})")
                continue
            entry = vocab.lookup_by_id(lid)
            if entry:
                print(f"[{entry.system}] label_id={entry.label_id}  name={entry.name}  category={entry.category}  parent={entry.parent}")
            else:
                print(f"(label_id {lid} not found)")
    elif cmd == "strategy-types":
        for name in vocab.all_strategy_types:
            print(name)
    elif cmd == "race-names":
        for name in vocab.all_race_names:
            print(name)
    elif cmd == "risk-labels":
        for name in vocab.all_risk_labels:
            print(name)
    else:
        print(f"unknown command: {cmd}")
        sys.exit(1)
