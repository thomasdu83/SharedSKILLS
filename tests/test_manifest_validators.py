import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_skill_dependencies import validate as validate_dependencies
from validate_skill_release import validate as validate_release


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_matches_all_skills():
    result = validate_release(ROOT)
    assert result["status"] == "pass", result["errors"]


def test_dependency_manifest_is_structurally_valid():
    result = validate_dependencies(ROOT)
    assert result["status"] == "pass", result["errors"]
