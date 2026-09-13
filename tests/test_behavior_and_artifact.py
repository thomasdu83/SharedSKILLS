from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_artifact import validate as validate_artifact
from validate_behavior_evals import validate as validate_behavior_evals


ROOT = Path(__file__).resolve().parents[1]


def test_behavior_registry_is_structurally_valid_but_pending():
    result = validate_behavior_evals(ROOT)
    assert result["status"] == "warning", result["errors"]
    assert result["run_count"] == 0
    assert result["executed_count"] == 0


def test_artifact_validator_accepts_frozen_research_artifact():
    artifact = ROOT / "tests" / "fixtures" / "artifact-research.yaml"
    result = validate_artifact(artifact)
    assert result["status"] == "pass", result["errors"]


def test_artifact_validator_rejects_unreviewed_portfolio_input():
    artifact = ROOT / "tests" / "fixtures" / "artifact-portfolio-invalid.yaml"
    result = validate_artifact(artifact)
    assert result["status"] == "fail"
    assert any("judgments" in error for error in result["errors"])
