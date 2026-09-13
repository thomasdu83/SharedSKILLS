import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from investment_feedback import validate_feedback


def base(**overrides):
    value = {
        "artifact_id": "artifact-001",
        "model_id": "model-001",
        "run_id": "run-001",
        "decision_use": "portfolio_input",
        "phase": "proposal",
        "owner": "pm",
        "reviewer": "risk",
        "review_status": "approved",
        "evidence": [{"id": "ev-1"}],
        "target_weights": [{"asset": "A", "weight": 1.0}],
        "portfolio_constraints": [{"name": "max_weight", "value": 1.0}],
        "cost_assumptions": [{"name": "fee_bps", "value": 10}],
        "lifecycle_action": "none",
    }
    value.update(overrides)
    return value


def test_research_only_cannot_claim_portfolio_ready():
    result = validate_feedback(base(decision_use="research_only", target_weights=[]))
    assert result["status"] == "ready"
    assert "portfolio_input" in result["unresolved"][0]


def test_empty_evidence_blocks_even_research_only():
    result = validate_feedback(base(decision_use="research_only", evidence=[]))
    assert result["status"] == "blocked"
    assert "evidence" in result["missing_fields"]


def test_internal_decision_does_not_require_target_weights():
    result = validate_feedback(base(
        decision_use="internal_decision",
        target_weights=[],
        portfolio_constraints=[],
        cost_assumptions=[],
    ))
    assert result["status"] == "ready"


def test_portfolio_proposal_requires_target_weights():
    result = validate_feedback(base(target_weights=[]))
    assert result["status"] == "blocked"
    assert "target_weights" in result["missing_fields"]


def test_draft_cannot_promote_to_portfolio_input():
    result = validate_feedback(base(review_status="draft"))
    assert result["status"] == "blocked"
    assert "review_status=approved" in result["missing_fields"]


def test_live_outcome_requires_execution_and_attribution():
    result = validate_feedback(base(decision_use="live", phase="outcome"))
    assert result["status"] == "blocked"
    assert "actual_positions" in result["missing_fields"]
    assert "pnl" in result["missing_fields"]
    assert "attribution" in result["missing_fields"]


def test_live_outcome_is_ready_with_actual_evidence():
    result = validate_feedback(base(
        decision_use="live",
        phase="outcome",
        actual_positions=[{"asset": "A", "weight": 0.9}],
        trades=[{"asset": "A", "quantity": 10}],
        realized_costs=[{"type": "fee", "value": 2}],
        pnl={"net": 0.03, "benchmark": 0.01},
        attribution=[{"source": "asset", "contribution": 0.02}],
    ))
    assert result["status"] == "ready"


def test_retire_requires_kill_condition_and_remains_human_review():
    missing = validate_feedback(base(lifecycle_action="retire"))
    assert missing["status"] == "blocked"
    assert "kill_conditions" in missing["missing_fields"]

    pending = validate_feedback(base(
        lifecycle_action="retire",
        kill_conditions=[{"metric": "drawdown", "threshold": 0.2}],
    ))
    assert pending["status"] == "needs_review"


def test_research_only_retire_cannot_bypass_kill_gate():
    result = validate_feedback(base(decision_use="research_only", lifecycle_action="retire"))
    assert result["status"] == "blocked"
    assert "kill_conditions" in result["missing_fields"]
    assert result["decision_use"] == "research_only"
