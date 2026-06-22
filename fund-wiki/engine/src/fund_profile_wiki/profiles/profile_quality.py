"""Profile quality reporting helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable, Protocol


class ProfileLike(Protocol):
    product_name: str
    manager: str
    entity_type: str
    entity_confidence: str
    canonical_product_name: str
    profile_quality_status: str
    product_name_reason: str
    review_reasons: list[str]
    source_notes: list[str]


@dataclass(frozen=True)
class ProfileQualityReport:
    status: str
    profile_count: int
    canonical_product_count: int
    generic_profile_count: int
    duplicate_group_count: int
    suspicious_product_names: list[str]
    entity_type_counts: dict[str, int]
    entity_confidence_counts: dict[str, int]
    review_reason_counts: dict[str, int]
    quality_status_counts: dict[str, int]
    product_name_reason_counts: dict[str, int]
    removed_existing_profiles: int = 0


def build_profile_quality_report(
    profiles: Iterable[ProfileLike],
    *,
    removed_existing_profiles: int = 0,
) -> ProfileQualityReport:
    rows = list(profiles)
    quality_counts = Counter(
        getattr(profile, "profile_quality_status", "") or "unknown"
        for profile in rows
    )
    reason_counts = Counter(
        getattr(profile, "product_name_reason", "") or "unknown" for profile in rows
    )
    entity_type_counts = Counter(
        getattr(profile, "entity_type", "") or "unknown" for profile in rows
    )
    entity_confidence_counts = Counter(
        getattr(profile, "entity_confidence", "") or "unknown" for profile in rows
    )
    review_reason_counts = Counter(
        reason
        for profile in rows
        for reason in (getattr(profile, "review_reasons", []) or [])
    )
    canonical_groups: dict[str, list[ProfileLike]] = defaultdict(list)
    for profile in rows:
        key = getattr(profile, "canonical_product_name", "") or profile.product_name
        canonical_groups[key].append(profile)
    duplicate_groups = {
        key: items for key, items in canonical_groups.items() if len(items) > 1
    }
    suspicious = [
        profile.product_name
        for profile in rows
        if (getattr(profile, "profile_quality_status", "") or "confirmed")
        not in {"confirmed"}
    ][:20]
    generic_count = sum(
        1
        for profile in rows
        if (getattr(profile, "profile_quality_status", "") or "") != "confirmed"
    )
    status = "ok"
    if duplicate_groups or generic_count:
        status = "warning"
    return ProfileQualityReport(
        status=status,
        profile_count=len(rows),
        canonical_product_count=len(canonical_groups),
        generic_profile_count=generic_count,
        duplicate_group_count=len(duplicate_groups),
        suspicious_product_names=suspicious,
        entity_type_counts=dict(entity_type_counts),
        entity_confidence_counts=dict(entity_confidence_counts),
        review_reason_counts=dict(review_reason_counts),
        quality_status_counts=dict(quality_counts),
        product_name_reason_counts=dict(reason_counts),
        removed_existing_profiles=removed_existing_profiles,
    )


def write_profile_quality_report(
    profiles: Iterable[ProfileLike],
    path: Path,
    *,
    removed_existing_profiles: int = 0,
) -> ProfileQualityReport:
    report = build_profile_quality_report(
        profiles, removed_existing_profiles=removed_existing_profiles
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    return report
