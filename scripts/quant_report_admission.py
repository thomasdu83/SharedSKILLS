#!/usr/bin/env python3
"""Deterministic admission/risk classifier for quant-report QA.

The Skill document explains the policy and evidence requirements.  This small
stdlib-only function makes the high-risk boundary decisions regression-testable
for weaker LLMs and future edits.  It does not fetch reports or infer missing
inputs; callers must supply the normalized fields from the contract.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


VALID_SCORE_BASIS = {"confirmed", "provisional", "unknown"}
VALID_NAV_SOURCE = {"live_custody", "live_stitched", "simulated", "backtest", "unknown"}
VALID_EVIDENCE_STATE = {"complete", "missing", "conflict"}


def classify_admission(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify one normalized quant-report admission payload.

    The order mirrors ``shared-contracts/quant-report-admission.yaml`` and
    ``quant-report-qa-interpreter/SKILL.md``.  Every path returns an explicit
    status; malformed or uncovered combinations become ``needs_review``.
    """
    score = payload.get("score")
    score_basis = payload.get("score_basis", "unknown")
    nav_weeks = payload.get("nav_weeks")
    nav_source = payload.get("nav_source", "unknown")
    evidence_state = payload.get("evidence_state", "missing")
    severe_short_history = payload.get("severe_short_history", "unknown")
    unresolved: list[str] = []

    if score_basis not in VALID_SCORE_BASIS:
        unresolved.append(f"invalid score_basis: {score_basis}")
    if nav_source not in VALID_NAV_SOURCE:
        unresolved.append(f"invalid nav_source: {nav_source}")
    if evidence_state not in VALID_EVIDENCE_STATE:
        unresolved.append(f"invalid evidence_state: {evidence_state}")
    if severe_short_history not in (True, False, "unknown"):
        unresolved.append(f"invalid severe_short_history: {severe_short_history}")
    if score is not None and not isinstance(score, (int, float)):
        unresolved.append("score must be number or null")
    if nav_weeks is not None and not isinstance(nav_weeks, (int, float)):
        unresolved.append("nav_weeks must be number or null")
    if unresolved:
        return _review("invalid_input", unresolved)

    # Completeness and conflict always take precedence over a tempting result.
    if evidence_state in {"missing", "conflict"} or score_basis == "unknown" or score is None or nav_weeks is None:
        if evidence_state == "conflict":
            unresolved.append("evidence conflict requires resolution")
        if score is None:
            unresolved.append("score is missing")
        if nav_weeks is None:
            unresolved.append("nav_weeks is missing")
        if score_basis == "unknown":
            unresolved.append("score basis is unknown")
        return _review("evidence_missing_or_conflict", unresolved)

    if score == 65:
        return {
            "admission_status": "borderline",
            "risk_level": "needs_review",
            "primary_reason": "score_boundary_65",
            "matched_rule": 2,
            "unresolved": ["制度需确认 score==65 的风险等级解释"],
        }

    if nav_source in {"backtest", "simulated"}:
        reason = "backtest" if nav_source == "backtest" else "simulated"
        return {
            "admission_status": "fail",
            "risk_level": 5,
            "primary_reason": reason,
            "matched_rule": 3,
            "unresolved": [],
        }

    if score_basis == "provisional":
        return _review("provisional_score", ["score basis must be confirmed before formal admission"])

    if score > 65 and nav_weeks >= 52 and nav_source == "live_custody":
        return {
            "admission_status": "pass",
            "risk_level": 1,
            "primary_reason": "meets_score_and_history",
            "matched_rule": 5,
            "unresolved": [],
        }

    if score >= 65 and (39 <= nav_weeks < 52 or nav_source == "live_stitched"):
        reason = "stitched_nav" if nav_source == "live_stitched" else "short_nav_history"
        return {
            "admission_status": "fail",
            "risk_level": 2,
            "primary_reason": reason,
            "matched_rule": 6,
            "unresolved": [],
        }

    if score < 65 and severe_short_history is True:
        return {
            "admission_status": "fail",
            "risk_level": 4,
            "primary_reason": "low_score_and_severe_short_history",
            "matched_rule": 7,
            "unresolved": [],
        }

    if score < 65 or (nav_weeks < 52 and nav_source != "live_custody"):
        return {
            "admission_status": "fail",
            "risk_level": 3,
            "primary_reason": "low_score" if score < 65 else "short_nav_history",
            "matched_rule": 8,
            "unresolved": [] if severe_short_history != "unknown" else [
                "severe_short_history threshold is not institution-defined"
            ],
        }

    if score >= 65 and nav_weeks < 52 and nav_source == "live_custody":
        return {
            "admission_status": "fail",
            "risk_level": 3,
            "primary_reason": "short_nav_history",
            "matched_rule": 9,
            "unresolved": [] if severe_short_history != "unknown" else [
                "severe_short_history threshold is not institution-defined"
            ],
        }

    return _review("uncovered_combination", ["input combination is not covered by the current policy table"])


def _review(reason: str, unresolved: list[str]) -> dict[str, Any]:
    return {
        "admission_status": "needs_review",
        "risk_level": "needs_review",
        "primary_reason": reason,
        "matched_rule": None,
        "unresolved": unresolved,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify normalized quant-report admission fields")
    parser.add_argument("--json", required=True, help="JSON object containing contract input fields")
    args = parser.parse_args()
    try:
        payload = json.loads(args.json)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(classify_admission(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
