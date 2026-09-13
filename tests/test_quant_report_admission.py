import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quant_report_admission import classify_admission


def base(**overrides):
    value = {
        "score": 70,
        "score_basis": "confirmed",
        "nav_weeks": 52,
        "nav_source": "live_custody",
        "evidence_state": "complete",
        "severe_short_history": False,
    }
    value.update(overrides)
    return value


def test_score_65_is_borderline():
    result = classify_admission(base(score=65))
    assert result["admission_status"] == "borderline"
    assert result["risk_level"] == "needs_review"


def test_confirmed_live_custody_passes():
    result = classify_admission(base())
    assert (result["admission_status"], result["risk_level"]) == ("pass", 1)


def test_provisional_score_cannot_pass():
    result = classify_admission(base(score_basis="provisional"))
    assert result["admission_status"] == "needs_review"


def test_backtest_is_highest_risk():
    result = classify_admission(base(nav_source="backtest"))
    assert (result["admission_status"], result["risk_level"]) == ("fail", 5)


def test_missing_evidence_blocks_before_scoring():
    result = classify_admission(base(evidence_state="missing"))
    assert result["admission_status"] == "needs_review"
    assert result["risk_level"] == "needs_review"


def test_short_custody_history_is_level_three():
    result = classify_admission(base(score=70, nav_weeks=30))
    assert (result["admission_status"], result["risk_level"]) == ("fail", 3)


def test_low_score_severe_history_is_level_four():
    result = classify_admission(base(score=60, nav_weeks=20, severe_short_history=True))
    assert (result["admission_status"], result["risk_level"]) == ("fail", 4)


def test_stitched_nav_is_level_two():
    result = classify_admission(base(nav_source="live_stitched"))
    assert (result["admission_status"], result["risk_level"]) == ("fail", 2)
