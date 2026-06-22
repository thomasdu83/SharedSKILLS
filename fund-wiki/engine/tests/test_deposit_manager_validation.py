from __future__ import annotations

import json
import importlib.util
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def load_deposit_manager():
    script_path = (
        Path(__file__).resolve().parents[1].parent / "scripts" / "deposit_manager.py"
    )
    sys.path.insert(0, str(script_path.parent))
    spec = importlib.util.spec_from_file_location("deposit_manager", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manager_profile_and_index_counts_are_manager_specific(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    docs_root = tmp_path / "docs"
    profile_root = docs_root / "product_profiles"
    index_root = docs_root / "indexes"
    profile_root.mkdir(parents=True)
    index_root.mkdir(parents=True)
    (profile_root / "other.md").write_text(
        """---
profile_type: ProductProfile
product_name: "[[其他产品]]"
manager: "[[其他管理人]]"
---
""",
        encoding="utf-8",
    )
    (index_root / "product_profiles.jsonl").write_text(
        '{"product_name":"其他产品","manager":"其他管理人","manager_aliases":[]}\n',
        encoding="utf-8",
    )

    assert deposit_manager.count_manager_profiles(docs_root, "平方和") == 0
    assert deposit_manager.count_manager_index_records(docs_root, "平方和") == 0

    (profile_root / "pfh.md").write_text(
        """---
profile_type: ProductProfile
product_name: "[[平方和鼎盛中证500指数增强18号]]"
manager: "[[平方和]]"
---
""",
        encoding="utf-8",
    )
    (index_root / "product_profiles.jsonl").write_text(
        '{"product_name":"平方和鼎盛中证500指数增强18号","manager":"平方和","manager_aliases":["平方和"]}\n',
        encoding="utf-8",
    )

    assert deposit_manager.count_manager_profiles(docs_root, "平方和") == 1
    assert deposit_manager.count_manager_index_records(docs_root, "平方和") == 1


def test_manager_profile_quality_is_scoped_to_current_manager(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    docs_root = tmp_path / "docs"
    index_root = docs_root / "indexes"
    index_root.mkdir(parents=True)
    (index_root / "product_profiles.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "product_name": "ManagerA Product 1",
                        "manager": "ManagerA",
                        "canonical_product_name": "ManagerA Product 1",
                        "profile_quality_status": "confirmed",
                        "product_name_reason": "product_specific",
                        "manager_aliases": ["Manager A"],
                    }
                ),
                json.dumps(
                    {
                        "product_name": "Other Short",
                        "manager": "OtherManager",
                        "canonical_product_name": "Other Short",
                        "profile_quality_status": "needs_review",
                        "product_name_reason": "suspicious_short_name",
                        "manager_aliases": [],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manager_quality = deposit_manager.build_manager_profile_quality(
        docs_root, "ManagerA"
    )
    other_quality = deposit_manager.build_manager_profile_quality(
        docs_root, "OtherManager"
    )

    assert manager_quality["status"] == "ok"
    assert manager_quality["profile_count"] == 1
    assert manager_quality["quality_status_counts"] == {"confirmed": 1}
    assert other_quality["status"] == "warning"
    assert other_quality["suspicious_product_names"] == ["Other Short"]


def test_final_status_uses_manager_scoped_quality_not_global_warning() -> None:
    deposit_manager = load_deposit_manager()

    status, warnings = deposit_manager.determine_final_status(
        source_count_after=8,
        manager_profile_count=2,
        manager_index_count=2,
        manager_profile_quality={"status": "ok"},
        failed=0,
        processed=8,
        skipped=0,
    )

    assert status == "success"
    assert warnings == []


def test_final_status_warns_only_for_manager_scoped_quality() -> None:
    deposit_manager = load_deposit_manager()

    status, warnings = deposit_manager.determine_final_status(
        source_count_after=8,
        manager_profile_count=2,
        manager_index_count=2,
        manager_profile_quality={"status": "warning"},
        failed=0,
        processed=8,
        skipped=0,
    )

    assert status == "partial_success_quality_warning"
    assert warnings
    assert "manager-scoped" in warnings[0]


def test_match_output_partitions_low_score_candidates() -> None:
    deposit_manager = load_deposit_manager()
    matches = [
        deposit_manager.ManagerMatch("299409_ManagerA", "W:/299409_ManagerA", 90, "299409"),
        deposit_manager.ManagerMatch("270508_LowA", "W:/270508_LowA", 10, "270508"),
        deposit_manager.ManagerMatch("270509_MidA", "W:/270509_MidA", 35, "270509"),
    ]

    visible, diagnostic = deposit_manager.partition_matches_for_output(matches)

    assert [item.name for item in visible] == ["299409_ManagerA", "270509_MidA"]
    assert [item.name for item in diagnostic] == ["270508_LowA"]


def test_choose_match_auto_selects_canonical_name_for_same_code_candidates() -> None:
    deposit_manager = load_deposit_manager()
    matches = [
        deposit_manager.ManagerMatch(
            "353725_三亚托特私募",
            "W:/353725_三亚托特私募",
            90,
            "353725",
        ),
        deposit_manager.ManagerMatch(
            "353725_托特（三亚）私募基金管理有限公司",
            "W:/353725_托特（三亚）私募基金管理有限公司",
            90,
            "353725",
        ),
    ]

    selected = deposit_manager.choose_match(matches)

    assert selected.name == "353725_托特（三亚）私募基金管理有限公司"


def test_choose_match_still_rejects_close_different_code_candidates() -> None:
    deposit_manager = load_deposit_manager()
    matches = [
        deposit_manager.ManagerMatch("353725_托特私募", "W:/353725_托特私募", 90, "353725"),
        deposit_manager.ManagerMatch("361819_托特私募", "W:/361819_托特私募", 88, "361819"),
    ]

    try:
        deposit_manager.choose_match(matches)
    except RuntimeError as exc:
        assert "匹配不唯一" in str(exc)
    else:
        raise AssertionError("different-code close matches should still require confirmation")


def test_find_same_code_folders_reports_siblings_without_merging(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    selected_dir = raw_root / "353725_三亚托特私募"
    sibling_dir = raw_root / "353725_托特（三亚）私募基金管理有限公司"
    other_dir = raw_root / "361819_上海特夫私募基金管理有限公司"
    selected_dir.mkdir()
    sibling_dir.mkdir()
    other_dir.mkdir()
    selected = deposit_manager.ManagerMatch(
        selected_dir.name,
        str(selected_dir),
        90,
        "353725",
    )

    matches = deposit_manager.find_same_code_folders(raw_root, selected)

    assert [match.name for match in matches] == [sibling_dir.name]


def test_raw_folder_group_merges_same_code_siblings_by_default() -> None:
    deposit_manager = load_deposit_manager()
    selected = deposit_manager.ManagerMatch("353725_ManagerA", "W:/353725_ManagerA", 90, "353725")
    sibling = deposit_manager.ManagerMatch("353725_ManagerAlias", "W:/353725_ManagerAlias", 0, "353725")

    group = deposit_manager.build_raw_folder_group(selected, [sibling])

    assert [match.name for match in group] == [
        "353725_ManagerA",
        "353725_ManagerAlias",
    ]


def test_raw_folder_group_can_stay_single_folder() -> None:
    deposit_manager = load_deposit_manager()
    selected = deposit_manager.ManagerMatch("353725_ManagerA", "W:/353725_ManagerA", 90, "353725")
    sibling = deposit_manager.ManagerMatch("353725_ManagerAlias", "W:/353725_ManagerAlias", 0, "353725")

    group = deposit_manager.build_raw_folder_group(
        selected, [sibling], single_folder=True
    )

    assert [match.name for match in group] == ["353725_ManagerA"]


def test_manager_lock_recovers_stale_lock(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    docs_root = tmp_path / "docs"
    lock_dir = docs_root / "run_logs" / "locks"
    lock_dir.mkdir(parents=True)
    lock_path = lock_dir / "平方和.lock"
    old_created = (datetime.now() - timedelta(hours=7)).isoformat(timespec="seconds")
    lock_path.write_text(
        json.dumps({"run_id": "old", "created_at": old_created}, ensure_ascii=False),
        encoding="utf-8",
    )

    lock = deposit_manager.ManagerLock(docs_root, "平方和", "new-run", stale_hours=1)
    lock.acquire()

    try:
        assert lock.acquired is True
        assert lock.recovered_stale_lock is True
        assert lock.existing_lock_info["run_id"] == "old"
        assert (lock_dir / "stale").exists()
    finally:
        release = lock.release()
        assert release["released"] is True
        assert release["exists_after_release"] is False


def test_parsed_cache_run_dir_uses_ascii_stable_component(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()

    run_dir = deposit_manager.parsed_cache_run_dir(
        tmp_path / "cache", "20260606-115253_托特", "托特"
    )

    assert run_dir.name.startswith("20260606-115253_")
    assert all(ord(ch) < 128 for ch in run_dir.name)


def test_runtime_cache_warning_promotes_success_status() -> None:
    deposit_manager = load_deposit_manager()
    warnings: list[str] = []

    status = deposit_manager.add_nonblocking_runtime_warnings(
        status="success",
        warnings=warnings,
        ingest_payload={"parsed_cache_write_failures": 2},
    )

    assert status == "success_with_warnings"
    assert "Parsed cache write failed" in warnings[0]


def test_manager_lock_blocks_fresh_lock(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    docs_root = tmp_path / "docs"
    lock_dir = docs_root / "run_logs" / "locks"
    lock_dir.mkdir(parents=True)
    lock_path = lock_dir / "平方和.lock"
    lock_path.write_text(
        json.dumps(
            {
                "run_id": "running",
                "created_at": datetime.now().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lock = deposit_manager.ManagerLock(docs_root, "平方和", "new-run", stale_hours=1)

    try:
        lock.acquire()
    except RuntimeError as exc:
        assert "锁文件已存在" in str(exc)
    else:
        raise AssertionError("fresh manager lock should block a new run")


def test_manager_lock_recovers_orphaned_local_pid_lock(
    monkeypatch, tmp_path: Path
) -> None:
    deposit_manager = load_deposit_manager()
    docs_root = tmp_path / "docs"
    lock_dir = docs_root / "run_logs" / "locks"
    lock_dir.mkdir(parents=True)
    lock_path = lock_dir / "平方和.lock"
    lock_path.write_text(
        json.dumps(
            {
                "run_id": "orphaned",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "pid": 999999,
                "host": deposit_manager.socket.gethostname(),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        deposit_manager.ManagerLock,
        "_pid_exists",
        lambda self, pid: False,
    )

    lock = deposit_manager.ManagerLock(docs_root, "平方和", "new-run", stale_hours=6)
    lock.acquire()

    try:
        assert lock.acquired is True
        assert lock.recovered_stale_lock is True
        assert lock.existing_lock_info["run_id"] == "orphaned"
        assert (lock_dir / "stale").exists()
    finally:
        lock.release()


def test_manager_lock_does_not_archive_changed_lock_during_recovery(
    monkeypatch, tmp_path: Path
) -> None:
    deposit_manager = load_deposit_manager()
    docs_root = tmp_path / "docs"
    old_payload = {
        "run_id": "old",
        "created_at": (datetime.now() - timedelta(hours=7)).isoformat(
            timespec="seconds"
        ),
    }
    new_payload = {
        "run_id": "running",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pid": os.getpid(),
        "host": deposit_manager.socket.gethostname(),
    }
    lock = deposit_manager.ManagerLock(docs_root, "平方和", "new-run", stale_hours=1)
    monkeypatch.setattr(
        lock,
        "_read_existing_lock",
        lambda: new_payload,
    )
    monkeypatch.setattr(
        lock,
        "_archive_stale_lock",
        lambda: (_ for _ in ()).throw(
            AssertionError("should not archive changed lock")
        ),
    )

    assert lock._recover_existing_lock(old_payload) is False


def test_run_command_stream_drains_stdout_while_streaming_stderr(
    tmp_path: Path,
) -> None:
    deposit_manager = load_deposit_manager()
    child = tmp_path / "child_large_stdout.py"
    child.write_text(
        """
import json
import sys

for i in range(200):
    print(f"log {i}", file=sys.stderr, flush=True)

sys.stdout.write(json.dumps({"written": ["x" * 1000 for _ in range(200)]}))
sys.stdout.flush()
""".strip(),
        encoding="utf-8",
    )

    completed = deposit_manager.run_command_stream(
        [sys.executable, str(child)],
        cwd=tmp_path,
        env=os.environ.copy(),
    )

    assert completed.returncode == 0
    assert '"written"' in completed.stdout
    assert "log 199" in completed.stderr


def test_parsed_cache_cleanup_helpers_are_scoped_to_cache_root(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    cache_root = tmp_path / "parsed_cache"
    run_dir = cache_root / "run-1" / "平方和"
    run_dir.mkdir(parents=True)
    (run_dir / "alpha.md").write_text("cache", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.md").write_text("keep", encoding="utf-8")

    assert deposit_manager.remove_tree_within_root(cache_root, outside) == 0
    assert outside.exists()
    assert deposit_manager.remove_tree_within_root(cache_root, run_dir) == 1
    assert not run_dir.exists()


def test_expired_parsed_cache_cleanup_removes_old_run_dirs(tmp_path: Path) -> None:
    deposit_manager = load_deposit_manager()
    cache_root = tmp_path / "parsed_cache"
    old_run = cache_root / "old-run"
    fresh_run = cache_root / "fresh-run"
    old_run.mkdir(parents=True)
    fresh_run.mkdir(parents=True)
    (old_run / "old.md").write_text("old", encoding="utf-8")
    (fresh_run / "fresh.md").write_text("fresh", encoding="utf-8")
    old_time = (datetime.now() - timedelta(hours=72)).timestamp()
    os.utime(old_run, (old_time, old_time))

    deleted = deposit_manager.cleanup_expired_parsed_cache(cache_root, ttl_hours=48)

    assert deleted == 1
    assert not old_run.exists()
    assert fresh_run.exists()


def test_parsed_cache_cleanup_policy_keeps_real_partial_failures() -> None:
    deposit_manager = load_deposit_manager()

    assert deposit_manager.should_cleanup_parsed_cache(
        final_status="partial_success",
        failed=1,
        smoke_query={"status": "success"},
        keep_parsed_cache=False,
    ) is False
    assert deposit_manager.should_cleanup_parsed_cache(
        final_status="partial_success_quality_warning",
        failed=0,
        smoke_query={"status": "warning"},
        keep_parsed_cache=False,
    ) is False


def test_parsed_cache_cleanup_policy_cleans_quality_only_success() -> None:
    deposit_manager = load_deposit_manager()

    assert deposit_manager.should_cleanup_parsed_cache(
        final_status="partial_success_quality_warning",
        failed=0,
        smoke_query={"status": "success"},
        keep_parsed_cache=False,
    ) is True
    assert deposit_manager.should_cleanup_parsed_cache(
        final_status="partial_success_quality_warning",
        failed=0,
        smoke_query={"status": "success"},
        keep_parsed_cache=True,
    ) is False


def test_summarize_smoke_query_payload_extracts_compact_fields() -> None:
    deposit_manager = load_deposit_manager()
    payload = {
        "status": "success",
        "intent_mode": "manager_lookup",
        "recognized_manager": "ManagerA",
        "recognized_product": "",
        "hard_filters": ["ManagerA"],
        "grouped_results": [{"group_name": "ManagerA"}],
        "results": [
            {
                "product_name": "ProductA",
                "manager": "ManagerA Investment",
                "path": "Y:/docs/product_profiles/ProductA.md",
                "hard_filter_satisfied": True,
                "hard_filter_status": "satisfied",
                "primary_strategy_tags": ["IndexEnhanced"],
                "secondary_strategy_tags": ["CSI1000"],
            }
        ],
    }

    summary = deposit_manager.summarize_smoke_query_payload("ManagerA", payload)

    assert summary == {
        "status": "success",
        "query": "ManagerA",
        "result_count": 1,
        "group_count": 1,
        "returncode": 0,
        "intent_mode": "manager_lookup",
        "recognized_manager": "ManagerA",
        "recognized_product": "",
        "hard_filters": ["ManagerA"],
        "top_product": "ProductA",
        "top_manager": "ManagerA Investment",
        "top_path": "Y:/docs/product_profiles/ProductA.md",
        "top_hard_filter_satisfied": True,
        "top_hard_filter_status": "satisfied",
        "top_primary_strategy_tags": ["IndexEnhanced"],
        "top_secondary_strategy_tags": ["CSI1000"],
        "error": "",
    }


def test_summarize_smoke_query_payload_warns_on_no_results() -> None:
    deposit_manager = load_deposit_manager()
    summary = deposit_manager.summarize_smoke_query_payload(
        "ManagerA",
        {
            "status": "success",
            "results": [],
            "grouped_results": [],
        },
    )

    assert summary["status"] == "warning"
    assert summary["result_count"] == 0
    assert summary["error"] == "no_results"


def test_parse_json_stdout_accepts_log_prefixed_pretty_json() -> None:
    deposit_manager = load_deposit_manager()
    payload = deposit_manager.parse_json_stdout(
        'log before json\n{\n  "status": "success",\n  "results": []\n}\n'
    )

    assert payload["status"] == "success"
    assert payload["results"] == []
