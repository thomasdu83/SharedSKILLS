import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from skill_doctor import parse_yaml_simple
from validate_route_decision import validate


def registry():
    return parse_yaml_simple(
        (Path(__file__).resolve().parents[1] / "skill-registry.yaml").read_text(encoding="utf-8")
    )


def base(**overrides):
    value = {
        "primary_skill": "quant-research-coding",
        "support_skills": ["zmdata-data-api"],
        "task_class": "light_research",
        "risk_level": 2,
        "trigger_evidence": ["用户只要求一次性因子检查"],
        "excluded_skills": ["quant-develop"],
        "escalation": None,
        "unresolved": [],
    }
    value.update(overrides)
    return value


def test_valid_route_decision():
    assert validate(base(), registry())["status"] == "pass"


def test_route_cannot_use_excluded_support():
    result = validate(base(support_skills=["quant-develop"]), registry())
    assert result["status"] == "fail"
    assert any("excludes" in error for error in result["errors"])


def test_route_support_must_be_declared_by_primary():
    result = validate(base(support_skills=["old-coder"]), registry())
    assert result["status"] == "fail"
    assert any("supports" in error for error in result["errors"])


def test_route_support_count_is_bounded():
    result = validate(base(support_skills=["zmdata-data-api", "fund-wiki", "old-coder"]), registry())
    assert result["status"] == "fail"
    assert any("最多两个" in error for error in result["errors"])
