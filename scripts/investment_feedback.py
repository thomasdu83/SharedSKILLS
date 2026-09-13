#!/usr/bin/env python3
"""Deterministic checks for the research-to-portfolio feedback contract.

The function validates normalized fields only. It does not infer weights, PnL,
capacity, or kill conditions from prose and it cannot approve an investment
decision on behalf of a human reviewer.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


DECISION_USES = {"research_only", "internal_decision", "portfolio_input", "live"}
PHASES = {"proposal", "execution", "outcome"}
REVIEW_STATUSES = {"draft", "reviewed", "approved"}
LIFECYCLE_ACTIONS = {"none", "continue", "degrade", "pause", "retire"}


def _blocked(
    reason: str,
    missing: list[str] | None = None,
    unresolved: list[str] | None = None,
    decision_use: str | None = None,
    phase: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "decision_use": decision_use,
        "phase": phase,
        "missing_fields": missing or [],
        "unresolved": unresolved or [],
        "evidence": [],
        "next_action": "补齐字段后重新校验",
    }


def _needs_review(
    reason: str,
    unresolved: list[str],
    decision_use: str | None = None,
    phase: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "needs_review",
        "decision": reason,
        "decision_use": decision_use,
        "phase": phase,
        "missing_fields": [],
        "unresolved": unresolved,
        "evidence": [],
        "next_action": "由负责人/评审人复核并记录人工结论",
    }


def validate_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one normalized investment-feedback payload."""
    required = ("artifact_id", "model_id", "run_id", "decision_use", "phase", "owner", "review_status")
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return _blocked("required_identity_or_lifecycle_fields_missing", missing=missing)

    decision_use = payload["decision_use"]
    phase = payload["phase"]
    review_status = payload["review_status"]
    action = payload.get("lifecycle_action", "none")
    invalid = []
    if decision_use not in DECISION_USES:
        invalid.append(f"invalid decision_use: {decision_use}")
    if phase not in PHASES:
        invalid.append(f"invalid phase: {phase}")
    if review_status not in REVIEW_STATUSES:
        invalid.append(f"invalid review_status: {review_status}")
    if action not in LIFECYCLE_ACTIONS:
        invalid.append(f"invalid lifecycle_action: {action}")
    if invalid:
        return _blocked("invalid_input", unresolved=invalid, decision_use=str(decision_use), phase=str(phase))

    evidence = payload.get("evidence")
    if not isinstance(evidence, list):
        return _blocked("evidence_must_be_list", missing=["evidence"], decision_use=decision_use, phase=phase)
    if not evidence:
        return _blocked("evidence_missing", missing=["evidence"], decision_use=decision_use, phase=phase)

    # Pause/retire is a lifecycle decision, even for research-only artifacts;
    # never let an early research-only return bypass its evidence gate.
    if action in {"pause", "retire"}:
        if not payload.get("kill_conditions"):
            return _blocked(
                "lifecycle_action_requires_defined_kill_condition",
                missing=["kill_conditions"],
                decision_use=decision_use,
                phase=phase,
            )
        return _needs_review(
            "lifecycle_action_pending_human_decision",
            [f"requested action: {action}"],
            decision_use=decision_use,
            phase=phase,
        )

    if phase == "proposal":
        # Research output can be delivered as research_only, but promotion is
        # never implicit. Internal decisions may omit target weights; portfolio
        # and live proposals may not.
        if decision_use == "research_only":
            return {
                "status": "ready",
                "decision": "research_only_result_only",
                "decision_use": decision_use,
                "phase": phase,
                "missing_fields": [],
                "unresolved": ["不得据此声称 portfolio_input 或 live"],
                "evidence": evidence,
                "next_action": "如需进入组合，提交新的晋级记录并完成人工评审",
            }
        if decision_use in {"portfolio_input", "live"}:
            required_proposal = {
                "target_weights": payload.get("target_weights"),
                "portfolio_constraints": payload.get("portfolio_constraints"),
                "cost_assumptions": payload.get("cost_assumptions"),
                "reviewer": payload.get("reviewer"),
            }
            missing = [name for name, value in required_proposal.items() if not value]
            if review_status != "approved":
                missing.append("review_status=approved")
            if missing:
                return _blocked(
                    "portfolio_promotion_gate_incomplete",
                    missing=missing,
                    decision_use=decision_use,
                    phase=phase,
                )
    else:
        required_execution = {
            "actual_positions": payload.get("actual_positions"),
            "trades": payload.get("trades"),
            "realized_costs": payload.get("realized_costs"),
        }
        missing = [name for name, value in required_execution.items() if not value]
        if phase == "outcome":
            if not payload.get("pnl"):
                missing.append("pnl")
            if not payload.get("attribution"):
                missing.append("attribution")
        if missing:
            return _blocked(
                "portfolio_execution_or_outcome_evidence_incomplete",
                missing=missing,
                decision_use=decision_use,
                phase=phase,
            )

    if decision_use == "live" and not payload.get("reviewer"):
        return _blocked("live_use_requires_reviewer", missing=["reviewer"], decision_use=decision_use, phase=phase)

    if decision_use in {"portfolio_input", "live"} and review_status != "approved":
        return _blocked(
            "portfolio_use_requires_approved_review",
            missing=["review_status=approved"],
            decision_use=decision_use,
            phase=phase,
        )

    return {
        "status": "ready",
        "decision": "portfolio_feedback_complete",
        "decision_use": decision_use,
        "phase": phase,
        "missing_fields": [],
        "unresolved": [],
        "evidence": evidence,
        "next_action": "按既定评审与运行流程继续，并保留本次快照",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate investment-feedback contract fields")
    parser.add_argument("--json", required=True, help="JSON object containing normalized contract fields")
    args = parser.parse_args()
    try:
        payload = json.loads(args.json)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(validate_feedback(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
