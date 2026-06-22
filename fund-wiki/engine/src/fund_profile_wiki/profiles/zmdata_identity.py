"""Optional zmdata-based product identity enrichment."""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import logging
import re
from typing import Any, Iterable

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZMDataCandidate:
    fund_id: str = ""
    fund_code: str = ""
    fund_name: str = ""
    fund_short_name: str = ""
    fund_name_use: str = ""
    manager_name: str = ""
    strategy_type: str = ""
    fund_type: str = ""
    bench_name: str = ""

    def aliases(self) -> list[str]:
        return dedupe(
            [
                self.fund_name,
                self.fund_short_name,
                self.fund_name_use,
            ]
        )

    def summary(self) -> str:
        parts = []
        if self.fund_id:
            parts.append(f"fundID={self.fund_id}")
        if self.fund_code:
            parts.append(f"fundCode={self.fund_code}")
        if self.fund_name:
            parts.append(f"fundName={self.fund_name}")
        if self.fund_short_name:
            parts.append(f"fundShortName={self.fund_short_name}")
        if self.fund_name_use:
            parts.append(f"fundNameUse={self.fund_name_use}")
        if self.manager_name:
            parts.append(f"manager={self.manager_name}")
        if self.strategy_type:
            parts.append(f"strategyType={self.strategy_type}")
        if self.fund_type:
            parts.append(f"fundType={self.fund_type}")
        if self.bench_name:
            parts.append(f"benchName={self.bench_name}")
        return " | ".join(parts)


@dataclass(frozen=True)
class ZMDataEnrichment:
    status: str = "off"
    fund_ids: list[str] = field(default_factory=list)
    fund_codes: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    candidate_matches: list[str] = field(default_factory=list)
    rejected_candidates: list[str] = field(default_factory=list)


def enrich_profile_with_zmdata(
    *,
    product_name: str,
    manager: str,
    product_aliases: Iterable[str],
    manager_aliases: Iterable[str],
    mode: str = "auto",
    page_size: int = 10,
) -> ZMDataEnrichment:
    normalized_mode = (mode or "auto").strip().lower()
    if normalized_mode == "off":
        return ZMDataEnrichment(status="off")

    client = load_zmdata_client()
    if client is None:
        return ZMDataEnrichment(status="unavailable")

    try:
        search_terms = build_search_terms(product_name, product_aliases)
        if not search_terms:
            return ZMDataEnrichment(status="not_found")
        candidates = search_candidates(client, search_terms, page_size=page_size)
        filtered, rejected = partition_candidates(
            candidates, product_name, manager, product_aliases, manager_aliases
        )
        if not filtered:
            return ZMDataEnrichment(
                status="cross_manager_candidates_only" if rejected else "not_found",
                rejected_candidates=[candidate.summary() for candidate in rejected[:5]],
            )

        unique_identity_keys = dedupe(
            [candidate_identity_key(candidate) for candidate in filtered]
        )
        candidate_matches = [candidate.summary() for candidate in filtered[:5]]
        rejected_candidates = [candidate.summary() for candidate in rejected[:5]]
        if len(unique_identity_keys) == 1:
            aliases = []
            fund_ids = []
            fund_codes = []
            for candidate in filtered:
                aliases.extend(candidate.aliases())
                if candidate.fund_id:
                    fund_ids.append(candidate.fund_id)
                if candidate.fund_code:
                    fund_codes.append(candidate.fund_code)
            return ZMDataEnrichment(
                status="matched",
                fund_ids=dedupe(fund_ids),
                fund_codes=dedupe(fund_codes),
                aliases=clean_aliases(aliases),
                candidate_matches=candidate_matches,
                rejected_candidates=rejected_candidates,
            )
        return ZMDataEnrichment(
            status="multiple_candidates_same_manager",
            candidate_matches=candidate_matches,
            rejected_candidates=rejected_candidates,
        )
    except Exception as exc:  # pragma: no cover - defensive degradation
        LOGGER.warning("zmdata enrichment failed for %s: %s", product_name, exc)
        return ZMDataEnrichment(status="error")


def load_zmdata_client() -> Any | None:
    try:
        return importlib.import_module("zmdata")
    except ModuleNotFoundError:
        LOGGER.info(
            "zmdata is not installed; skip external product identity enrichment"
        )
        return None
    except Exception as exc:  # pragma: no cover - defensive degradation
        LOGGER.warning("failed to import zmdata: %s", exc)
        return None


def build_search_terms(product_name: str, product_aliases: Iterable[str]) -> list[str]:
    values = clean_aliases([product_name, *product_aliases])
    return sorted(values, key=lambda item: (-len(normalize_for_match(item)), item))[:6]


def search_candidates(
    client: Any, search_terms: Iterable[str], page_size: int
) -> list[ZMDataCandidate]:
    candidates = []
    seen = set()
    for term in search_terms:
        if not term:
            continue
        records = data_frame_records(client.fund_search_quick(term, pageSize=page_size))
        for record in records:
            candidate = candidate_from_record(record)
            key = candidate_identity_key(candidate)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return candidates


def data_frame_records(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if hasattr(result, "to_dict"):
        try:
            return list(result.to_dict("records"))
        except TypeError:
            pass
    if isinstance(result, dict):
        return [result]
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    return []


def candidate_from_record(record: dict[str, Any]) -> ZMDataCandidate:
    return ZMDataCandidate(
        fund_id=clean_cell(record.get("fundID") or record.get("FundID")),
        fund_code=clean_cell(record.get("fundCode") or record.get("FundCode")),
        fund_name=clean_cell(record.get("fundName") or record.get("FundName")),
        fund_short_name=clean_cell(
            record.get("fundShortName") or record.get("fund_short_name")
        ),
        fund_name_use=clean_cell(record.get("fundNameUse")),
        manager_name=clean_cell(
            record.get("fundManageCompany")
            or record.get("fundManageCompanyStr")
            or record.get("fundmanagecompany")
            or record.get("Manager")
        ),
        strategy_type=clean_cell(record.get("strategyType")),
        fund_type=clean_cell(record.get("fundType")),
        bench_name=clean_cell(record.get("benchName")),
    )


def filter_candidates(
    candidates: Iterable[ZMDataCandidate],
    product_name: str,
    manager: str,
    product_aliases: Iterable[str],
    manager_aliases: Iterable[str],
) -> list[ZMDataCandidate]:
    return partition_candidates(
        candidates, product_name, manager, product_aliases, manager_aliases
    )[0]


def partition_candidates(
    candidates: Iterable[ZMDataCandidate],
    product_name: str,
    manager: str,
    product_aliases: Iterable[str],
    manager_aliases: Iterable[str],
) -> tuple[list[ZMDataCandidate], list[ZMDataCandidate]]:
    product_norms = {
        normalize_product_alias(value)
        for value in [product_name, *product_aliases]
        if normalize_product_alias(value)
    }
    manager_norms = {
        normalize_manager_alias(value)
        for value in [manager, *manager_aliases]
        if normalize_manager_alias(value)
    }
    filtered: list[tuple[int, ZMDataCandidate]] = []
    rejected: list[ZMDataCandidate] = []
    for candidate in candidates:
        score = 0
        candidate_manager = normalize_manager_alias(candidate.manager_name)
        candidate_names = {
            normalize_product_alias(alias)
            for alias in candidate.aliases()
            if normalize_product_alias(alias)
        }
        product_score = product_match_score(product_norms, candidate_names)
        if manager_norms:
            if candidate_manager in manager_norms:
                score += 4
            elif any(
                candidate_manager.startswith(alias)
                or alias.startswith(candidate_manager)
                for alias in manager_norms
                if alias and candidate_manager
            ):
                score += 2
            else:
                if product_score > 0:
                    rejected.append(candidate)
                continue
        score += product_score
        if score > 0:
            filtered.append((score, candidate))
    filtered.sort(
        key=lambda item: (
            -item[0],
            len(normalize_product_alias(item[1].fund_name_use or item[1].fund_name)),
            item[1].fund_id,
            item[1].fund_name,
        )
    )
    return [candidate for _, candidate in filtered], rejected


def product_match_score(product_norms: set[str], candidate_names: set[str]) -> int:
    if product_norms & candidate_names:
        return 4
    if any(
        product_norm in candidate_name or candidate_name in product_norm
        for product_norm in product_norms
        for candidate_name in candidate_names
        if product_norm and candidate_name
    ):
        return 2
    return 0


def normalize_product_alias(value: str) -> str:
    text = normalize_for_match(str(value or ""))
    text = text.replace("私募证券投资基金", "")
    text = text.replace("证券投资基金", "")
    text = text.replace("私募基金", "")
    text = text.replace("资产管理计划", "")
    text = text.replace("资管计划", "")
    return replace_chinese_number_suffixes(text)


def normalize_manager_alias(value: str) -> str:
    text = normalize_for_match(str(value or ""))
    for suffix in (
        "私募基金管理有限公司",
        "资产管理有限公司",
        "投资管理有限公司",
        "投资有限公司",
        "资本管理有限公司",
        "资本有限公司",
        "基金管理有限公司",
        "有限公司",
    ):
        text = text.replace(normalize_for_match(suffix), "")
    return text


def replace_chinese_number_suffixes(value: str) -> str:
    result = value
    for chinese, arabic in (
        ("一号", "1号"),
        ("二号", "2号"),
        ("三号", "3号"),
        ("四号", "4号"),
        ("五号", "5号"),
        ("六号", "6号"),
        ("七号", "7号"),
        ("八号", "8号"),
        ("九号", "9号"),
        ("十号", "10号"),
    ):
        result = result.replace(chinese, arabic)
    return result


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def candidate_identity_key(candidate: ZMDataCandidate) -> str:
    return (
        candidate.fund_id
        or candidate.fund_code
        or normalize_product_alias(candidate.fund_name_use or candidate.fund_name)
    )


def dedupe(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def clean_aliases(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        key = normalize_product_alias(text)
        if len(key) < 2 or key in seen:
            continue
        result.append(text)
        seen.add(key)
    return sorted(result, key=lambda item: (-len(normalize_product_alias(item)), item))


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "").casefold()
