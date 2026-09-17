from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_skill_inventory import build
from skill_doctor import parse_yaml_simple
from validate_route_decision import load_registry, validate


def decision(primary, supports=None):
    return dict(primary_skill=primary, support_skills=supports or [],
                task_class="consultation", risk_level=2,
                trigger_evidence=["用户明确指定任务与交付物"], excluded_skills=[],
                escalation=None, unresolved=[])


@pytest.mark.parametrize("short", ["kevin", "lqs", "lz", "myl", "wll", "zp"])
def test_named_analyst_can_be_a_single_primary(short):
    assert validate(decision(f"cicc-research-analyst-{short}-skill"), load_registry(ROOT))["status"] == "pass"


@pytest.mark.parametrize("old,canonical", [("frontend-design", "frontend-page-router"), ("architecture-diagram", "archify")])
def test_legacy_names_resolve_to_canonical_primary(old, canonical):
    result = validate(decision(old), load_registry(ROOT))
    assert result["status"] == "pass"
    assert result["normalized_decision"]["primary_skill"] == canonical


def test_source_review_and_new_model_have_distinct_valid_routes():
    reg = load_registry(ROOT)
    assert validate(decision("investment-paper-replication"), reg)["status"] == "pass"
    assert validate(decision("ai-quant-development-router", ["investment-paper-replication"]), reg)["status"] == "pass"


def test_monitor_contracting_hands_off_to_quant_development_router():
    reg = load_registry(ROOT)
    d = decision("research-monitor-contracting")
    d["escalation"] = "ai-quant-development-router"
    result = validate(d, reg)
    assert result["status"] == "pass"
    assert result["normalized_decision"]["escalation"] == "ai-quant-development-router"


def test_reference_registration_does_not_promote_inventory_to_primary(tmp_path):
    folder = tmp_path / "helper"
    folder.mkdir()
    (folder / "SKILL.md").write_text("---\nname: helper\ndescription: Helper\n---\n", encoding="utf-8")
    (tmp_path / "skill-registry.yaml").write_text("skills:\n  - id: helper\n    path: helper\n    role: reference\n    routable: false\n", encoding="utf-8")
    row = parse_yaml_simple(build(tmp_path))["skills"][0]
    assert row["role"] == "reference"
    assert str(row["routable"]).lower() == "false"


def test_alias_cannot_hide_duplicate_supports():
    result = validate(decision("ai-quant-development-router", ["frontend-design", "frontend-page-router"]), load_registry(ROOT))
    assert result["status"] == "fail"
    assert any("重复" in e for e in result["errors"])


@pytest.mark.parametrize("target", ["does-not-exist", "macro-strategy-learning"])
def test_escalation_must_be_declared_by_primary(target):
    d = decision("quant-research-coding")
    d["escalation"] = target
    assert validate(d, load_registry(ROOT))["status"] == "fail"


def test_empty_routing_evidence_is_rejected():
    d = decision("quant-research-coding")
    d["trigger_evidence"] = []
    assert validate(d, load_registry(ROOT))["status"] == "fail"


def test_macro_snapshot_can_consult_one_analyst_without_changing_primary():
    assert validate(decision("macro-strategy-learning", ["cicc-research-analyst-lz-skill"]), load_registry(ROOT))["status"] == "pass"
