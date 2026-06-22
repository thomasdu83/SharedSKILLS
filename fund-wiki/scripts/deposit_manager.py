#!/usr/bin/env python3
"""Deposit one manager's raw due-diligence materials into fund_profile_wiki."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import ctypes
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

from _env import load_env_files
from _paths import (
    PathResolutionError,
    default_python,
    resolve_docs_root,
    resolve_project_root,
    resolve_raw_root,
)
from find_manager_materials import (
    ManagerMatch,
    find_manager_folders,
    find_same_code_folders,
    render_matches,
)


SUPPORTED_PROVIDERS = ("deepseek", "openai", "kimi")


def progress_line(run_id: str, stage: str, message: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] [INFO] run_id={run_id} stage={stage} {message}"


def write_progress(
    run_id: str, stage: str, message: str, log_path: Path | None = None
) -> None:
    line = progress_line(run_id, stage, message)
    print(line, file=sys.stderr, flush=True)
    if log_path:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass


class ManagerLock:
    def __init__(
        self,
        docs_root: Path,
        manager: str,
        run_id: str,
        *,
        stale_hours: float | None = None,
    ):
        self.path = docs_root / "run_logs" / "locks" / f"{safe_filename(manager)}.lock"
        self.manager = manager
        self.run_id = run_id
        self.stale_hours = (
            stale_hours
            if stale_hours is not None
            else float(os.environ.get("FPW_LOCK_STALE_HOURS", "6"))
        )
        self.fd: int | None = None
        self.acquired = False
        self.recovered_stale_lock = False
        self.existing_lock_info: dict = {}

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._try_acquire()

    def _try_acquire(self) -> None:
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(
                self.fd,
                json.dumps(self._payload(), ensure_ascii=False).encode("utf-8"),
            )
            self.acquired = True
        except FileExistsError as exc:
            self.existing_lock_info = self._read_existing_lock()
            if self._recover_existing_lock(self.existing_lock_info):
                self.recovered_stale_lock = True
                self._try_acquire()
                return
            raise RuntimeError(
                f"管理人任务正在运行，锁文件已存在: {self.path} "
                f"{json.dumps(self.existing_lock_info, ensure_ascii=False)}"
            ) from exc

    def _payload(self) -> dict:
        return {
            "run_id": self.run_id,
            "manager": self.manager,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "pid": os.getpid(),
            "host": socket.gethostname(),
        }

    def _read_existing_lock(self) -> dict:
        try:
            text = self.path.read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"raw": text}
        if not isinstance(payload, dict):
            return {"raw": text}
        return payload

    def _is_stale(self, payload: dict) -> bool:
        if self.stale_hours <= 0:
            return False
        created_at = str(payload.get("created_at", "") or "")
        try:
            created = datetime.fromisoformat(created_at)
        except ValueError:
            try:
                created = datetime.fromtimestamp(self.path.stat().st_mtime)
            except OSError:
                return False
        return datetime.now() - created > timedelta(hours=self.stale_hours)

    def _is_recoverable_lock(self, payload: dict) -> bool:
        return self._is_orphaned_local_pid(payload) or self._is_stale(payload)

    def _recover_existing_lock(self, payload: dict) -> bool:
        if not self._is_recoverable_lock(payload):
            return False
        # Re-read before archiving so we do not remove a newer lock created by
        # another process after our first existence check.
        current_payload = self._read_existing_lock()
        if current_payload != payload:
            return False
        if not self._is_recoverable_lock(current_payload):
            return False
        self._archive_stale_lock()
        return True

    def _is_orphaned_local_pid(self, payload: dict) -> bool:
        host = str(payload.get("host", "") or "")
        if host and host.casefold() != socket.gethostname().casefold():
            return False
        try:
            pid = int(payload.get("pid", 0) or 0)
        except (TypeError, ValueError):
            return False
        if pid <= 0:
            return False
        return not self._pid_exists(pid)

    def _pid_exists(self, pid: int) -> bool:
        if pid == os.getpid():
            return True
        if os.name == "nt":
            return self._windows_pid_exists(pid)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def _windows_pid_exists(self, pid: int) -> bool:
        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)

    def _archive_stale_lock(self) -> None:
        archive_dir = self.path.parent / "stale"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = (
            archive_dir
            / f"{self.path.stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.lock"
        )
        try:
            self.path.replace(archive_path)
        except OSError:
            self.path.unlink()

    def release(self) -> dict:
        result = {
            "attempted": bool(self.acquired),
            "released": False,
            "path": str(self.path),
            "error": "",
            "exists_after_release": False,
        }
        if not self.acquired:
            result["exists_after_release"] = self.path.exists()
            return result
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
            result["released"] = True
        except FileNotFoundError:
            result["released"] = True
        except OSError as exc:
            result["error"] = str(exc)
        result["exists_after_release"] = self.path.exists()
        return result


LEGAL_NAME_TOKENS: tuple[str, ...] = (
    "私募基金管理有限公司",
    "证券投资基金管理有限公司",
    "基金管理有限公司",
    "资产管理有限公司",
    "投资管理有限公司",
    "投资有限公司",
    "有限公司",
)


def choose_match(matches: list[ManagerMatch], *, first: bool = False) -> ManagerMatch:
    if not matches:
        raise RuntimeError("未找到匹配的管理人文件夹。")
    if first or len(matches) == 1:
        return matches[0]
    top = matches[0]
    runner_up = matches[1]
    if top.score >= runner_up.score + 10:
        return top
    close_matches = [match for match in matches if top.score - match.score <= 10]
    shared_code = shared_nonempty_code(close_matches)
    if shared_code:
        return preferred_manager_folder_name(close_matches)
    raise RuntimeError(
        "管理人文件夹匹配不唯一，请使用更具体的名称或 --first。\n"
        + render_matches(matches)
    )


def shared_nonempty_code(matches: list[ManagerMatch]) -> str:
    codes = {match.code for match in matches if match.code}
    return next(iter(codes)) if len(codes) == 1 else ""


def preferred_manager_folder_name(matches: list[ManagerMatch]) -> ManagerMatch:
    return max(matches, key=manager_folder_preference_key)


def manager_folder_preference_key(match: ManagerMatch) -> tuple[int, int, int, str]:
    name = re.sub(r"^\d{4,}[_\-\s]*", "", match.name)
    legal_score = 0
    for index, token in enumerate(LEGAL_NAME_TOKENS):
        if token in name:
            legal_score = len(LEGAL_NAME_TOKENS) - index
            break
    normalized = re.sub(r"\s+", "", name)
    return (legal_score, match.score, len(normalized), normalized)


def partition_matches_for_output(
    matches: list[ManagerMatch],
    *,
    threshold: int = 30,
    limit: int = 10,
) -> tuple[list[ManagerMatch], list[ManagerMatch]]:
    """Keep high-signal matches visible and move weak fuzzy hits to diagnostics."""
    visible: list[ManagerMatch] = []
    diagnostic: list[ManagerMatch] = []
    for index, match in enumerate(matches[:limit]):
        if index == 0 or match.score >= threshold:
            visible.append(match)
        else:
            diagnostic.append(match)
    return visible, diagnostic


def build_raw_folder_group(
    selected: ManagerMatch,
    same_code_candidates: list[ManagerMatch],
    *,
    single_folder: bool = False,
) -> list[ManagerMatch]:
    """Return the raw folders that should be deposited for one manager run."""
    if single_folder:
        return [selected]
    result: list[ManagerMatch] = []
    seen_paths: set[str] = set()
    for match in [selected, *same_code_candidates]:
        key = str(Path(match.path).resolve(strict=False)).casefold()
        if key in seen_paths:
            continue
        result.append(match)
        seen_paths.add(key)
    return result


def run_command(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print("")
    print("Running:")
    print(" ".join(f'"{part}"' if " " in part else part for part in command))
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(
            f"命令失败，退出码 {completed.returncode}: {' '.join(command)}"
        )


def run_command_capture(
    command: list[str], *, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_command_stream(
    command: list[str], *, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []

    def drain_stdout() -> None:
        if process.stdout is None:
            return
        try:
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                stdout_parts.append(chunk)
        finally:
            process.stdout.close()

    stdout_thread = threading.Thread(target=drain_stdout, daemon=True)
    stdout_thread.start()

    if process.stderr is not None:
        try:
            for line in process.stderr:
                stderr_parts.append(line)
                print(line, file=sys.stderr, end="", flush=True)
        finally:
            process.stderr.close()

    assert process.stdout is not None
    returncode = process.wait()
    stdout_thread.join(timeout=5)
    return subprocess.CompletedProcess(
        command, returncode, "".join(stdout_parts), "".join(stderr_parts)
    )


def parse_json_last_line(
    stdout: str, *, stage: str, run_id: str, log_path: Path
) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        write_progress(
            run_id,
            stage,
            "json_parse failed reason=empty_stdout",
            log_path,
        )
        raise RuntimeError("无法解析 ingest JSON 输出: stdout 为空")
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        tail = lines[-1][-500:]
        write_progress(
            run_id,
            stage,
            f"json_parse failed stdout_chars={len(stdout)} last_line_tail={tail!r}",
            log_path,
        )
        raise RuntimeError(f"无法解析 ingest JSON 输出: {stdout}") from exc
    if not isinstance(payload, dict):
        write_progress(
            run_id,
            stage,
            f"json_parse failed reason=not_object type={type(payload).__name__}",
            log_path,
        )
        raise RuntimeError(f"无法解析 ingest JSON 输出: {stdout}")
    write_progress(
        run_id,
        stage,
        f"json_parse done stdout_chars={len(stdout)} keys={','.join(sorted(payload.keys()))}",
        log_path,
    )
    return payload


def parse_json_stdout(stdout: str) -> dict:
    """Parse a JSON payload from a subprocess stdout buffer."""

    text = stdout.strip()
    if not text:
        raise ValueError("stdout is empty")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload is not an object: {type(payload).__name__}")
    return payload


def as_list(value) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def summarize_smoke_query_payload(
    query: str,
    payload: dict | None,
    *,
    returncode: int = 0,
    error: str = "",
) -> dict:
    """Build a compact validation summary from query_fund_wiki.py JSON output."""

    if returncode != 0 or error:
        return {
            "status": "error",
            "query": query,
            "result_count": 0,
            "group_count": 0,
            "returncode": returncode,
            "error": error,
        }
    if not isinstance(payload, dict):
        return {
            "status": "error",
            "query": query,
            "result_count": 0,
            "group_count": 0,
            "returncode": returncode,
            "error": "query JSON payload is missing",
        }

    results = as_list(payload.get("results"))
    grouped_results = as_list(payload.get("grouped_results"))
    top = results[0] if results and isinstance(results[0], dict) else {}
    payload_status = str(payload.get("status", ""))
    if payload_status and payload_status != "success":
        status = "error"
        summary_error = str(payload.get("error", "") or payload_status)
    elif not results:
        status = "warning"
        summary_error = "no_results"
    else:
        status = "success"
        summary_error = ""

    return {
        "status": status,
        "query": query,
        "result_count": len(results),
        "group_count": len(grouped_results),
        "returncode": returncode,
        "intent_mode": payload.get("intent_mode", ""),
        "recognized_manager": payload.get("recognized_manager", ""),
        "recognized_product": payload.get("recognized_product", ""),
        "hard_filters": as_list(payload.get("hard_filters")),
        "top_product": top.get("product_name", ""),
        "top_manager": top.get("manager", ""),
        "top_path": top.get("path", ""),
        "top_hard_filter_satisfied": top.get("hard_filter_satisfied", False),
        "top_hard_filter_status": top.get("hard_filter_status", ""),
        "top_primary_strategy_tags": as_list(top.get("primary_strategy_tags")),
        "top_secondary_strategy_tags": as_list(top.get("secondary_strategy_tags")),
        "error": summary_error,
    }


def run_smoke_query(
    *,
    project_root: Path,
    docs_root: Path,
    python_exe: str,
    manager: str,
    env: dict[str, str],
    run_id: str,
    log_path: Path,
) -> dict:
    query_script = Path(__file__).with_name("query_fund_wiki.py")
    query_text = f"{manager} 产品"
    command = [
        python_exe,
        str(query_script),
        query_text,
        "--docs-root",
        str(docs_root),
        "--project-root",
        str(project_root),
        "--python",
        python_exe,
        "--limit",
        "5",
        "--json",
    ]
    write_progress(run_id, "smoke_query", f"start query={query_text}", log_path)
    completed = run_command_capture(command, cwd=project_root, env=env)
    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout).strip()
        summary = summarize_smoke_query_payload(
            query_text,
            None,
            returncode=completed.returncode,
            error=error,
        )
    else:
        try:
            payload = parse_json_stdout(completed.stdout)
            summary = summarize_smoke_query_payload(query_text, payload)
        except (ValueError, json.JSONDecodeError) as exc:
            summary = summarize_smoke_query_payload(
                query_text,
                None,
                returncode=0,
                error=f"query JSON parse failed: {exc}",
            )
    write_progress(
        run_id,
        "smoke_query",
        (
            f"done status={summary.get('status')} "
            f"results={summary.get('result_count')} "
            f"top={summary.get('top_product', '')}"
        ),
        log_path,
    )
    return summary


def count_profiles(docs_root: Path) -> int:
    return count_markdown_files(docs_root / "product_profiles")


def count_manager_profiles(docs_root: Path, manager: str) -> int:
    normalized_manager = normalize_for_match(manager)
    if not normalized_manager:
        return 0
    profile_root = docs_root / "product_profiles"
    if not profile_root.exists():
        return 0
    count = 0
    for path in profile_root.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if normalized_manager in normalize_for_match(text):
            count += 1
    return count


def load_manager_index_records(docs_root: Path, manager: str) -> list[dict]:
    normalized_manager = normalize_for_match(manager)
    if not normalized_manager:
        return []
    index_path = docs_root / "indexes" / "product_profiles.jsonl"
    if not index_path.exists():
        return []
    records: list[dict] = []
    try:
        with index_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                searchable = " ".join(
                    [
                        str(payload.get("manager", "")),
                        str(payload.get("product_name", "")),
                        " ".join(
                            str(item)
                            for item in payload.get("manager_aliases", []) or []
                        ),
                    ]
                )
                if normalized_manager in normalize_for_match(searchable):
                    records.append(payload)
    except OSError:
        return []
    return records


def count_manager_index_records(docs_root: Path, manager: str) -> int:
    return len(load_manager_index_records(docs_root, manager))


def build_manager_profile_quality(docs_root: Path, manager: str) -> dict:
    records = load_manager_index_records(docs_root, manager)
    quality_counts = Counter(
        str(record.get("profile_quality_status", "") or "confirmed")
        for record in records
    )
    reason_counts = Counter(
        str(record.get("product_name_reason", "") or "unknown")
        for record in records
    )
    canonical_groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        key = str(
            record.get("canonical_product_name")
            or record.get("product_name")
            or ""
        ).strip()
        canonical_groups[key].append(record)
    duplicate_groups = {
        key: items
        for key, items in canonical_groups.items()
        if key and len(items) > 1
    }
    suspicious = [
        str(record.get("product_name", "") or "")
        for record in records
        if str(record.get("profile_quality_status", "") or "confirmed")
        != "confirmed"
    ][:20]
    non_confirmed_count = sum(
        1
        for record in records
        if str(record.get("profile_quality_status", "") or "confirmed")
        != "confirmed"
    )
    status = "warning" if duplicate_groups or non_confirmed_count else "ok"
    duplicate_preview = [
        {
            "canonical_product_name": key,
            "product_names": [
                str(item.get("product_name", "") or "") for item in items[:10]
            ],
        }
        for key, items in list(duplicate_groups.items())[:10]
    ]
    return {
        "status": status,
        "manager": manager,
        "profile_count": len(records),
        "canonical_product_count": len(canonical_groups),
        "generic_profile_count": non_confirmed_count,
        "duplicate_group_count": len(duplicate_groups),
        "suspicious_product_names": suspicious,
        "quality_status_counts": dict(quality_counts),
        "product_name_reason_counts": dict(reason_counts),
        "duplicate_groups": duplicate_preview,
    }


def determine_final_status(
    *,
    source_count_after: int,
    manager_profile_count: int,
    manager_index_count: int,
    manager_profile_quality: dict,
    failed: int,
    processed: int,
    skipped: int,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if source_count_after == 0:
        return "error_no_source_notes", [
            "No source_notes were generated for this manager."
        ]
    if manager_profile_count == 0 or manager_index_count == 0:
        return "partial_success_profile_missing", [
            "Source notes were generated, but no product profile/index record was found for this manager. "
            "Run structured extraction or check whether source notes contain mentioned_products_simple/system product JSON."
        ]
    if manager_profile_quality.get("status") == "warning":
        warnings.append(
            "Product profiles were generated and indexed for this manager, but manager-scoped profile quality warnings were found. "
            "Check manager_profile_quality in the JSON payload for duplicate or non-confirmed product-name signals."
        )
        return "partial_success_quality_warning", warnings
    if failed:
        return "partial_success", warnings
    status = "skipped" if processed == 0 and skipped else "success"
    return status, warnings


def count_markdown_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*.md") if path.is_file())


def load_profile_quality_report(docs_root: Path) -> dict:
    report_path = docs_root / "reports" / "profile_quality.json"
    if not report_path.exists():
        return {}
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_health_check_report(docs_root: Path) -> dict:
    report_path = docs_root / "reports" / "health_check.json"
    if not report_path.exists():
        return {}
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def safe_filename(name: str) -> str:
    for ch in '<>:"/\\|?*\n\r\t':
        name = name.replace(ch, "_")
    return name.strip(" .") or "untitled"


def ascii_safe_filename(name: str) -> str:
    """Return a Windows-friendly ASCII path component with a stable hash suffix."""
    text = safe_filename(name)
    ascii_text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip(" ._")
    if ascii_text == text and ascii_text:
        return ascii_text
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    prefix = ascii_text[:80].strip(" ._") or "run"
    return f"{prefix}_{digest}"


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "").lower()


def configured_default_provider() -> str:
    provider = os.environ.get("FPW_DEFAULT_PROVIDER", "deepseek").strip().lower()
    if provider in {"auto", *SUPPORTED_PROVIDERS}:
        return provider
    return "deepseek"


def default_parsed_cache_root(project_root: Path) -> Path:
    configured = os.environ.get("FPW_PARSED_CACHE_ROOT")
    if configured:
        return Path(configured)
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "QuantSystem" / "fund-wiki" / "parsed_cache"
    return project_root.parent / ".cache" / "fund-wiki" / "parsed_cache"


def parsed_cache_run_dir(root: Path, run_id: str, manager: str) -> Path:
    return root / ascii_safe_filename(run_id or "manual-run")


def parsed_cache_manager_dir(root: Path, run_id: str, manager: str) -> Path:
    return parsed_cache_run_dir(root, run_id, manager) / safe_filename(manager)


def cleanup_expired_parsed_cache(root: Path, ttl_hours: float) -> int:
    if ttl_hours <= 0 or not root.exists():
        return 0
    cutoff = datetime.now() - timedelta(hours=ttl_hours)
    deleted = 0
    try:
        children = list(root.iterdir())
    except OSError:
        return 0
    for child in children:
        if not child.is_dir():
            continue
        try:
            modified = datetime.fromtimestamp(child.stat().st_mtime)
        except OSError:
            continue
        if modified >= cutoff:
            continue
        deleted += remove_tree_within_root(root, child)
    return deleted


def remove_tree_within_root(root: Path, target: Path) -> int:
    if not target.exists():
        return 0
    root_resolved = root.resolve(strict=False)
    target_resolved = target.resolve(strict=False)
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError:
        return 0
    if target_resolved == root_resolved:
        return 0
    deleted = count_files(target_resolved)
    shutil.rmtree(target_resolved, ignore_errors=True)
    return deleted


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def parsed_cache_ttl_hours() -> float:
    try:
        return float(os.environ.get("FPW_PARSED_CACHE_TTL_HOURS", "48"))
    except ValueError:
        return 48.0


def should_cleanup_parsed_cache(
    *,
    final_status: str,
    failed: int,
    smoke_query: dict,
    keep_parsed_cache: bool,
) -> bool:
    """Return whether the run-scoped parsed cache is no longer needed."""
    if keep_parsed_cache:
        return False
    if final_status in {"success", "skipped"}:
        return True
    quality_only_warning = (
        final_status in {"partial_success_quality_warning", "success_with_warnings"}
        and failed == 0
        and smoke_query.get("status") == "success"
    )
    return quality_only_warning


def add_nonblocking_runtime_warnings(
    *,
    status: str,
    warnings: list[str],
    ingest_payload: dict,
) -> str:
    """Promote successful runs to success_with_warnings for runtime issues."""

    cache_failures = int(ingest_payload.get("parsed_cache_write_failures", 0) or 0)
    if cache_failures:
        warnings.append(
            f"Parsed cache write failed for {cache_failures} file(s); the deposit continued, "
            "but local parse-cache recovery/reuse was unavailable for those files."
        )
    if status == "success" and cache_failures:
        return "success_with_warnings"
    return status


def provider_sequence(provider: str) -> list[str]:
    provider = provider.strip().lower()
    if provider == "auto":
        ordered = [configured_default_provider(), "deepseek", "openai", "kimi"]
    else:
        ordered = [provider]
    result: list[str] = []
    for item in ordered:
        if item == "auto":
            continue
        if item not in SUPPORTED_PROVIDERS:
            raise RuntimeError(f"Unsupported provider: {item}")
        if item not in result:
            result.append(item)
    return result


def make_run_id(manager: str) -> str:
    return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{safe_filename(manager)}"


def parse_built_count(stdout: str) -> int | None:
    match = re.search(r"Built\s+(\d+)\s+product profiles", stdout)
    return int(match.group(1)) if match else None


def parse_index_count(stdout: str) -> int | None:
    match = re.search(r"Indexed\s+(\d+)\s+product profiles", stdout)
    return int(match.group(1)) if match else None


def parse_relation_count(stdout: str) -> int | None:
    match = re.search(r"Relations:\s+(\d+)", stdout)
    return int(match.group(1)) if match else None


def emit_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    default_snapshot_mode = os.environ.get("FPW_SNAPSHOT_MODE", "manifest")
    if default_snapshot_mode == "copy":
        default_snapshot_mode = "manifest"
    parser = argparse.ArgumentParser(
        description="Deposit manager materials into fund-wiki."
    )
    parser.add_argument("manager", help="Manager keyword, e.g. 双隆")
    parser.add_argument("--raw-root", help="Explicit raw material root.")
    parser.add_argument("--docs-root", help="Explicit fund_profile_wiki_docs root.")
    parser.add_argument(
        "--project-root", help="Explicit fund_profile_wiki project root."
    )
    parser.add_argument("--env-file", help="Explicit .env file to load before running.")
    parser.add_argument(
        "--python",
        default=default_python(),
        help="Python executable for fund_profile_wiki scripts.",
    )
    parser.add_argument("--provider", choices=["auto", "kimi", "deepseek", "openai"])
    parser.add_argument(
        "--use-llm", action="store_true", help="Use LLM extraction during ingest."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit structured JSON only.",
    )
    parser.add_argument(
        "--snapshot",
        default=default_snapshot_mode,
        choices=["manifest", "none"],
    )
    parser.add_argument(
        "--changed-only",
        dest="changed_only",
        action="store_true",
        default=True,
        help="Skip unchanged files using source_manifest.jsonl.",
    )
    parser.add_argument(
        "--all-files",
        dest="changed_only",
        action="store_false",
        help="Scan/process all files unless --force is used.",
    )
    parser.add_argument(
        "--parse-workers",
        type=int,
        help="Max workers for parse-stage parallelism during ingest.",
    )
    parser.add_argument(
        "--ingest-scope",
        default=os.environ.get("FPW_INGEST_SCOPE", "all"),
        choices=["all", "priority"],
        help="Ingest all supported files or only high-priority source catalog files.",
    )
    parser.add_argument(
        "--parsed-cache-root",
        help="Local parsed-text cache root. Defaults to FPW_PARSED_CACHE_ROOT or local user cache.",
    )
    parser.add_argument(
        "--keep-parsed-cache",
        action="store_true",
        help="Keep this run's local parsed-text cache for debugging/recovery.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing even when file hashes are unchanged.",
    )
    parser.add_argument("--run-id", help="Explicit run id.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve paths and print planned commands only.",
    )
    parser.add_argument(
        "--first",
        action="store_true",
        help="Use the highest-scoring folder if multiple match.",
    )
    parser.add_argument(
        "--single-folder",
        action="store_true",
        help="Only ingest the selected folder; do not merge same-code sibling folders.",
    )
    parser.add_argument("--allow-local-docs-fallback", action="store_true")
    args = parser.parse_args()
    loaded_env_files = load_env_files(args.env_file)
    requested_provider = (args.provider or configured_default_provider()).lower()
    run_id = args.run_id or make_run_id(args.manager)

    try:
        project_root = resolve_project_root(args.project_root)
        raw_root = resolve_raw_root(args.raw_root)
        docs_root = resolve_docs_root(
            args.docs_root,
            allow_local_fallback=args.allow_local_docs_fallback,
            create=not args.dry_run,
            accept_creatable=args.dry_run,
        )
        matches = find_manager_folders(raw_root, args.manager)
        selected = choose_match(matches, first=args.first)
        same_code_candidates = find_same_code_folders(raw_root, selected)
        raw_folder_group = build_raw_folder_group(
            selected,
            same_code_candidates,
            single_folder=args.single_folder,
        )
        parsed_cache_root = (
            Path(args.parsed_cache_root)
            if args.parsed_cache_root
            else default_parsed_cache_root(project_root)
        )
        parsed_cache_run_root = parsed_cache_run_dir(
            parsed_cache_root, run_id, args.manager
        )
        parsed_cache_dir = parsed_cache_manager_dir(
            parsed_cache_root, run_id, args.manager
        )
    except (PathResolutionError, RuntimeError) as exc:
        if args.json_output:
            emit_json(
                {
                    "status": "error",
                    "stage": "path_resolve",
                    "manager": args.manager,
                    "run_id": run_id,
                    "error": str(exc),
                }
            )
        else:
            print(str(exc), file=sys.stderr)
        return 2

    ingest_cmd_base = [args.python, "scripts\\ingest_raw_docs.py"]
    for raw_folder in raw_folder_group:
        ingest_cmd_base.extend(["--input", raw_folder.path])
    ingest_cmd_base.extend(["--manager", args.manager])
    providers_to_try = provider_sequence(requested_provider) if args.use_llm else []

    def ingest_command(provider: str | None = None) -> list[str]:
        command = list(ingest_cmd_base)
        if provider:
            command.extend(["--use-llm", "--provider", provider])
        command.extend(["--snapshot", args.snapshot, "--run-id", run_id, "--json"])
        command.extend(
            [
                "--log-path",
                str(docs_root / "run_logs" / "runs" / f"{safe_filename(run_id)}.log"),
            ]
        )
        if args.parse_workers is not None:
            command.extend(["--parse-workers", str(args.parse_workers)])
        command.extend(["--ingest-scope", args.ingest_scope])
        command.extend(["--parsed-cache-root", str(parsed_cache_root)])
        if args.changed_only:
            command.append("--changed-only")
        if args.force:
            command.append("--force")
        return command

    manager_source_dir = docs_root / "source_notes" / safe_filename(args.manager)
    build_profiles_cmd = [
        args.python,
        "scripts\\build_product_profiles.py",
        "--source-root",
        str(manager_source_dir),
    ]
    build_index_cmd = [args.python, "scripts\\build_profile_index.py"]
    visible_matches, diagnostic_matches = partition_matches_for_output(matches)

    plan_payload = {
        "status": "dry_run" if args.dry_run else "planned",
        "stage": "plan",
        "run_id": run_id,
        "manager": args.manager,
        "selected_raw_folder": selected.path,
        "selected_raw_folders": [match.path for match in raw_folder_group],
        "raw_folder_count": len(raw_folder_group),
        "raw_root": str(raw_root),
        "docs_root": str(docs_root),
        "project_root": str(project_root),
        "loaded_env_files": [str(path) for path in loaded_env_files],
        "use_llm": args.use_llm,
        "provider_requested": requested_provider if args.use_llm else "",
        "provider_fallback_order": providers_to_try
        if args.use_llm and requested_provider == "auto"
        else [],
        "snapshot": args.snapshot,
        "parse_workers": args.parse_workers,
        "ingest_scope": args.ingest_scope,
        "parsed_cache_root": str(parsed_cache_root),
        "parsed_cache_run_dir": str(parsed_cache_run_root),
        "parsed_cache_manager_dir": str(parsed_cache_dir),
        "keep_parsed_cache": args.keep_parsed_cache,
        "parsed_cache_ttl_hours": parsed_cache_ttl_hours(),
        "changed_only": args.changed_only,
        "force": args.force,
        "matches": [match.__dict__ for match in visible_matches],
        "diagnostic_matches": [match.__dict__ for match in diagnostic_matches],
        "match_display_threshold": 30,
        "same_code_merge_enabled": not args.single_folder,
        "same_code_candidates": [
            match.__dict__ for match in same_code_candidates[:10]
        ],
        "same_code_folders_processed": [
            match.__dict__ for match in raw_folder_group
        ],
        "same_code_folders_ignored": [
            match.__dict__
            for match in ([] if not args.single_folder else same_code_candidates)
        ],
    }

    if not args.json_output:
        print("fund-wiki deposit plan")
        print(f"- manager: {args.manager}")
        print(f"- selected raw folder: {selected.path}")
        print(f"- raw folders to ingest: {len(raw_folder_group)}")
        for raw_folder in raw_folder_group:
            print(f"  - {raw_folder.path}")
        if same_code_candidates:
            action = "ignored by --single-folder" if args.single_folder else "merged"
            print(
                f"- same code candidates ({action}): "
                + ", ".join(match.name for match in same_code_candidates[:5])
            )
        print(f"- raw root: {raw_root}")
        print(f"- docs root: {docs_root}")
        print(f"- project root: {project_root}")
        print(f"- run_id: {run_id}")
        if loaded_env_files:
            print(f"- loaded .env: {', '.join(str(path) for path in loaded_env_files)}")
        print(f"- use LLM: {args.use_llm}")
        print(f"- provider: {requested_provider if args.use_llm else 'n/a'}")
        if args.use_llm and requested_provider == "auto":
            print(f"- provider fallback order: {', '.join(providers_to_try)}")
        print(f"- snapshot: {args.snapshot}")
        print(f"- parse workers: {args.parse_workers or 'default'}")
        print(f"- changed_only: {args.changed_only}")
        print(f"- parsed cache: {parsed_cache_dir}")
        print(f"- keep parsed cache: {args.keep_parsed_cache}")

        if len(visible_matches) > 1:
            print("")
            print(render_matches(visible_matches))

    if args.dry_run:
        preview_ingest = ingest_command(
            providers_to_try[0] if providers_to_try else None
        )
        plan_payload["planned_commands"] = [
            preview_ingest,
            build_profiles_cmd,
            build_index_cmd,
        ]
        if args.json_output:
            emit_json(plan_payload)
        else:
            print("")
            print("Dry run only. Planned commands:")
            for command in (preview_ingest, build_profiles_cmd, build_index_cmd):
                print(
                    " ".join(f'"{part}"' if " " in part else part for part in command)
                )
        return 0

    source_count_before = count_markdown_files(manager_source_dir)
    profile_count_before = count_profiles(docs_root)

    env = os.environ.copy()
    env["FPW_DOCS_ROOT"] = str(docs_root)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    lock = ManagerLock(docs_root, args.manager, run_id)
    warnings: list[str] = []
    if args.single_folder and same_code_candidates:
        warnings.append(
            "Found additional raw material folders with the same manager code, but --single-folder was used; coverage may be incomplete."
        )
    ingest_payload: dict = {}
    provider_used = ""
    built_count: int | None = None
    index_count: int | None = None
    relation_count: int | None = None
    parsed_cache_ttl_deleted_files = 0
    parsed_cache_deleted_files = 0
    parsed_cache_cleaned = False
    parsed_cache_cleanup_reason = "not_evaluated"
    lock_release_info: dict = {
        "attempted": False,
        "released": False,
        "path": str(lock.path),
        "error": "",
        "exists_after_release": False,
    }
    smoke_query: dict = {
        "status": "not_run",
        "query": args.manager,
        "result_count": 0,
        "group_count": 0,
    }
    try:
        lock.acquire()
        run_log_path = docs_root / "run_logs" / "runs" / f"{safe_filename(run_id)}.log"
        parsed_cache_ttl_deleted_files = cleanup_expired_parsed_cache(
            parsed_cache_root, parsed_cache_ttl_hours()
        )
        if parsed_cache_ttl_deleted_files:
            write_progress(
                run_id,
                "parsed_cache",
                f"ttl_cleanup deleted_files={parsed_cache_ttl_deleted_files} root={parsed_cache_root}",
                run_log_path,
            )
        if lock.recovered_stale_lock:
            warnings.append("Recovered a stale manager lock before starting this run.")
        write_progress(
            run_id,
            "deposit",
            f"start manager={args.manager} raw_folders={len(raw_folder_group)} folders={'; '.join(match.path for match in raw_folder_group)}",
            run_log_path,
        )
        write_progress(
            run_id,
            "lock",
            f"acquired path={lock.path} pid={os.getpid()} python={sys.executable} docs_root={docs_root}",
            run_log_path,
        )
        if args.use_llm:
            last_error: RuntimeError | None = None
            for provider in providers_to_try:
                write_progress(
                    run_id, "ingest", f"start provider={provider}", run_log_path
                )
                completed = run_command_stream(
                    ingest_command(provider), cwd=project_root, env=env
                )
                write_progress(
                    run_id,
                    "ingest",
                    (
                        f"subprocess returned provider={provider} "
                        f"returncode={completed.returncode} "
                        f"stdout_chars={len(completed.stdout)} stderr_chars={len(completed.stderr)}"
                    ),
                    run_log_path,
                )
                if completed.returncode == 0:
                    ingest_payload = parse_json_last_line(
                        completed.stdout,
                        stage="ingest",
                        run_id=run_id,
                        log_path=run_log_path,
                    )
                    provider_used = provider
                    write_progress(
                        run_id, "ingest", f"done provider={provider}", run_log_path
                    )
                    break
                last_error = RuntimeError(
                    completed.stderr.strip()
                    or completed.stdout.strip()
                    or f"Provider {provider} failed"
                )
                if requested_provider != "auto":
                    raise last_error
                warnings.append(f"Provider {provider} failed; trying next provider.")
                if not args.json_output:
                    print(warnings[-1], file=sys.stderr)
            else:
                raise last_error or RuntimeError("所有 LLM provider 均失败。")
        else:
            write_progress(run_id, "ingest", "start provider=n/a", run_log_path)
            completed = run_command_stream(ingest_command(), cwd=project_root, env=env)
            write_progress(
                run_id,
                "ingest",
                (
                    f"subprocess returned provider=n/a returncode={completed.returncode} "
                    f"stdout_chars={len(completed.stdout)} stderr_chars={len(completed.stderr)}"
                ),
                run_log_path,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    completed.stderr.strip()
                    or completed.stdout.strip()
                    or "ingest failed"
                )
            ingest_payload = parse_json_last_line(
                completed.stdout,
                stage="ingest",
                run_id=run_id,
                log_path=run_log_path,
            )
            write_progress(run_id, "ingest", "done provider=n/a", run_log_path)

        write_progress(run_id, "build_profiles", "start", run_log_path)
        completed = run_command_capture(build_profiles_cmd, cwd=project_root, env=env)
        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or "build_product_profiles failed"
            )
        built_count = parse_built_count(completed.stdout)
        write_progress(
            run_id, "build_profiles", f"done built={built_count}", run_log_path
        )
        if not args.json_output and completed.stdout:
            print(completed.stdout.rstrip())

        write_progress(run_id, "build_index", "start", run_log_path)
        completed = run_command_capture(build_index_cmd, cwd=project_root, env=env)
        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or "build_profile_index failed"
            )
        index_count = parse_index_count(completed.stdout)
        relation_count = parse_relation_count(completed.stdout)
        write_progress(
            run_id,
            "build_index",
            f"done indexed={index_count} relations={relation_count}",
            run_log_path,
        )
        if not args.json_output and completed.stdout:
            print(completed.stdout.rstrip())
    except RuntimeError as exc:
        error_cache_files = count_files(parsed_cache_run_root)
        if args.json_output:
            emit_json(
                {
                    "status": "error",
                    "stage": "deposit",
                    "run_id": run_id,
                    "manager": args.manager,
                    "error": str(exc),
                    "warnings": warnings,
                    "parsed_cache": {
                        "root": str(parsed_cache_root),
                        "run_dir": str(parsed_cache_run_root),
                        "manager_dir": str(parsed_cache_dir),
                        "files": error_cache_files,
                        "cleaned": False,
                        "cleanup_reason": "error_retained",
                        "ttl_deleted_files": parsed_cache_ttl_deleted_files,
                    },
                }
            )
        else:
            print(str(exc), file=sys.stderr)
            print(
                f"parsed cache retained: {parsed_cache_run_root} ({error_cache_files} files)",
                file=sys.stderr,
            )
        return 1
    finally:
        lock_release_info = lock.release()

    source_count_after = count_markdown_files(manager_source_dir)
    profile_count_after = count_profiles(docs_root)
    manager_profile_count = count_manager_profiles(docs_root, args.manager)
    manager_index_count = count_manager_index_records(docs_root, args.manager)
    profile_quality = load_profile_quality_report(docs_root)
    manager_profile_quality = build_manager_profile_quality(docs_root, args.manager)
    health_check = load_health_check_report(docs_root)
    failed = int(ingest_payload.get("failed", 0) or 0)
    processed = int(ingest_payload.get("processed", 0) or 0)
    skipped = int(ingest_payload.get("skipped", 0) or 0)
    final_status, status_warnings = determine_final_status(
        source_count_after=source_count_after,
        manager_profile_count=manager_profile_count,
        manager_index_count=manager_index_count,
        manager_profile_quality=manager_profile_quality,
        failed=failed,
        processed=processed,
        skipped=skipped,
    )
    warnings.extend(status_warnings)
    final_status = add_nonblocking_runtime_warnings(
        status=final_status,
        warnings=warnings,
        ingest_payload=ingest_payload,
    )
    if lock_release_info.get("error") or lock_release_info.get("exists_after_release"):
        warnings.append(
            "Manager lock was not fully released; future runs may need stale-lock recovery."
        )
        if final_status == "success":
            final_status = "success_with_warnings"
    smoke_query = run_smoke_query(
        project_root=project_root,
        docs_root=docs_root,
        python_exe=args.python,
        manager=args.manager,
        env=env,
        run_id=run_id,
        log_path=run_log_path,
    )
    if smoke_query.get("status") != "success":
        warnings.append(
            "Post-deposit smoke query did not return a clean success; check smoke_query in the JSON payload."
        )
    parsed_cache_files_before_cleanup = count_files(parsed_cache_run_root)
    if args.keep_parsed_cache:
        parsed_cache_cleanup_reason = "keep_parsed_cache"
    elif should_cleanup_parsed_cache(
        final_status=final_status,
        failed=failed,
        smoke_query=smoke_query,
        keep_parsed_cache=args.keep_parsed_cache,
    ):
        parsed_cache_deleted_files = remove_tree_within_root(
            parsed_cache_root, parsed_cache_run_root
        )
        parsed_cache_cleaned = True
        parsed_cache_cleanup_reason = final_status
        write_progress(
            run_id,
            "parsed_cache",
            f"cleanup done status={final_status} deleted_files={parsed_cache_deleted_files} path={parsed_cache_run_root}",
            run_log_path,
        )
    else:
        parsed_cache_cleanup_reason = f"{final_status}_retained"
        write_progress(
            run_id,
            "parsed_cache",
            f"retained status={final_status} files={parsed_cache_files_before_cleanup} path={parsed_cache_run_root}",
            run_log_path,
        )
    source_coverage = {
        "folder_count": int(
            ingest_payload.get("input_root_count", len(raw_folder_group)) or 0
        ),
        "input_roots": ingest_payload.get(
            "input_roots", [match.path for match in raw_folder_group]
        ),
        "source_root": ingest_payload.get("source_root", str(raw_root)),
        "catalog_entries": int(ingest_payload.get("catalog_entries", 0) or 0),
        "catalog_category_counts": ingest_payload.get("catalog_category_counts", {}),
        "catalog_source_folder_counts": ingest_payload.get(
            "catalog_source_folder_counts", {}
        ),
        "encrypted_pdfs_skipped": int(
            ingest_payload.get("encrypted_pdfs_skipped", 0) or 0
        ),
    }
    result_payload = {
        **plan_payload,
        "status": final_status,
        "stage": "completed",
        "provider_used": provider_used,
        "ingest": ingest_payload,
        "source_coverage": source_coverage,
        "manager_source_notes": source_count_after,
        "manager_source_notes_delta": source_count_after - source_count_before,
        "product_profiles_total": profile_count_after,
        "product_profiles_delta": profile_count_after - profile_count_before,
        "manager_product_profiles": manager_profile_count,
        "manager_index_records": manager_index_count,
        "profile_quality": profile_quality,
        "global_profile_quality": profile_quality,
        "manager_profile_quality": manager_profile_quality,
        "stale_lock_recovered": lock.recovered_stale_lock,
        "existing_lock_info": lock.existing_lock_info,
        "lock": {
            "path": str(lock.path),
            "recovered_stale_lock": lock.recovered_stale_lock,
            "existing_lock_info": lock.existing_lock_info,
            "release": lock_release_info,
        },
        "built_product_profiles": built_count,
        "indexed_product_profiles": index_count,
        "relation_records": relation_count,
        "index_jsonl": str(docs_root / "indexes" / "product_profiles.jsonl"),
        "index_sqlite": str(docs_root / "indexes" / "product_profiles.sqlite"),
        "relations_jsonl": str(docs_root / "indexes" / "relations.jsonl"),
        "relations_sqlite": str(docs_root / "indexes" / "relations.sqlite"),
        "health_check": health_check,
        "health_check_json": str(docs_root / "reports" / "health_check.json"),
        "health_check_md": str(docs_root / "reports" / "health_check.md"),
        "smoke_query": smoke_query,
        "parsed_cache": {
            "root": str(parsed_cache_root),
            "run_dir": str(parsed_cache_run_root),
            "manager_dir": str(parsed_cache_dir),
            "files_before_cleanup": parsed_cache_files_before_cleanup,
            "deleted_files": parsed_cache_deleted_files,
            "cleaned": parsed_cache_cleaned,
            "cleanup_reason": parsed_cache_cleanup_reason,
            "cleanup_owner": "deposit_manager",
            "cleanup_stage": "post_deposit",
            "ttl_deleted_files": parsed_cache_ttl_deleted_files,
            "keep": args.keep_parsed_cache,
            "write_failures": int(
                ingest_payload.get("parsed_cache_write_failures", 0) or 0
            ),
        },
        "governance_docs": [
            str(docs_root / "fund_wiki_purpose.md"),
            str(docs_root / "fund_wiki_schema.md"),
            str(docs_root / "index.md"),
            str(docs_root / "overview.md"),
            str(docs_root / "log.md"),
        ],
        "manifest": str(docs_root / "run_logs" / "source_manifest.jsonl"),
        "run_log": str(
            docs_root / "run_logs" / "runs" / f"{safe_filename(run_id)}.log"
        ),
        "warnings": warnings,
    }
    if args.json_output:
        emit_json(result_payload)
    else:
        print("")
        print("fund-wiki deposit completed")
        print(f"- status: {final_status}")
        print(f"- raw folders were read only: {len(raw_folder_group)}")
        for raw_folder in raw_folder_group:
            print(f"  - {raw_folder.path}")
        print(f"- docs root: {docs_root}")
        print(
            f"- manager source notes: {source_count_after} (delta {source_count_after - source_count_before:+d})"
        )
        print(
            f"- total product profiles: {profile_count_after} (delta {profile_count_after - profile_count_before:+d})"
        )
        print(f"- manager product profiles: {manager_profile_count}")
        print(f"- manager index records: {manager_index_count}")
        print(
            f"- manager profile quality: {manager_profile_quality.get('status', 'unknown')} "
            f"(duplicates={manager_profile_quality.get('duplicate_group_count', 0)}, "
            f"non_confirmed={manager_profile_quality.get('generic_profile_count', 0)})"
        )
        print(
            f"- global profile quality: {profile_quality.get('status', 'unknown')} "
            f"(diagnostic only)"
        )
        print(f"- manifest: {docs_root / 'run_logs' / 'source_manifest.jsonl'}")
        print(f"- JSONL index: {docs_root / 'indexes' / 'product_profiles.jsonl'}")
        print(f"- SQLite index: {docs_root / 'indexes' / 'product_profiles.sqlite'}")
        print(f"- relation index: {docs_root / 'indexes' / 'relations.jsonl'}")
        print(f"- health check: {docs_root / 'reports' / 'health_check.md'}")
        print(
            f"- smoke query: {smoke_query.get('status')} "
            f"(results={smoke_query.get('result_count')}, top={smoke_query.get('top_product', '')})"
        )
        print(
            f"- parsed cache: {parsed_cache_run_root} "
            f"(cleaned={parsed_cache_cleaned}, reason={parsed_cache_cleanup_reason})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
