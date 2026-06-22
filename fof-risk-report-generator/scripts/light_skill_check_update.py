#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
from typing import Optional, Set
import urllib.error
import urllib.parse
import urllib.request
import zipfile


DEFAULT_UPDATE_BASE_URL = "http://10.168.30.147:5173"
CACHE_FILE_NAME = ".light-skill-update-cache.json"
BACKUP_ROOT_NAME = ".light-skill-backups"
REQUIRED_ZIP_FILES = {"SKILL.md", ".light-skill-release.json"}


def load_release(root: Path) -> dict:
    release_path = root / ".light-skill-release.json"
    with release_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cache(root: Path) -> dict:
    cache_path = root / CACHE_FILE_NAME
    if not cache_path.exists():
        return {}
    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_cache(root: Path, payload: dict) -> None:
    cache_path = root / CACHE_FILE_NAME
    try:
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError:
        pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def check_interval_hours() -> int:
    raw = os.environ.get("LIGHT_SKILL_UPDATE_CHECK_INTERVAL_HOURS", "24")
    try:
        return max(0, int(raw))
    except ValueError:
        return 24


def cache_is_fresh(cache: dict, interval_hours: int) -> bool:
    if interval_hours == 0:
        return False
    raw = cache.get("lastCheckedAt", "")
    if not raw:
        return False
    try:
        checked_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    return utc_now() - checked_at < timedelta(hours=interval_hours)


def resolve_url(value: str) -> str:
    if value.startswith("http://") or value.startswith("https://") or value.startswith("file://"):
        return value
    base_url = os.environ.get("LIGHT_SKILL_UPDATE_BASE_URL", DEFAULT_UPDATE_BASE_URL).rstrip("/")
    if not base_url:
        return value
    return f"{base_url}{value if value.startswith('/') else '/' + value}"


def fetch_latest(check_url: str, release: dict) -> dict:
    query = urllib.parse.urlencode(
        {
            "installedReleaseId": release.get("releaseId", ""),
            "installedVersion": release.get("version", ""),
        }
    )
    separator = "&" if "?" in check_url else "?"
    request_url = f"{check_url}{separator}{query}"
    with urllib.request.urlopen(request_url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, target_path: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response:
        with target_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def safe_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", ".", "_") else "-" for ch in str(value or "unknown"))
    safe = "-".join(part for part in safe.split("-") if part)
    return safe[:80] or "unknown"


def zip_entry_mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0o777777


def validate_zip_entry(info: zipfile.ZipInfo) -> str:
    raw_name = info.filename
    normalized = raw_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if raw_name.startswith("/") or path.is_absolute():
        raise ValueError(f"zip entry uses an absolute path: {raw_name}")
    if not normalized or normalized in (".", "/"):
        raise ValueError("zip entry has an empty path")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"zip entry uses an unsafe path: {raw_name}")
    first_part = path.parts[0] if path.parts else ""
    if ":" in first_part:
        raise ValueError(f"zip entry uses an unsafe drive-like path: {raw_name}")
    if stat.S_ISLNK(zip_entry_mode(info)):
        raise ValueError(f"zip entry is a symlink: {raw_name}")
    return normalized


def extract_validated_zip(zip_path: Path, extract_dir: Path) -> dict:
    with zipfile.ZipFile(zip_path) as archive:
        names = {validate_zip_entry(info).rstrip("/") for info in archive.infolist()}
        missing = sorted(REQUIRED_ZIP_FILES - names)
        if missing:
            raise ValueError(f"zip is missing required file(s): {', '.join(missing)}")
        archive.extractall(extract_dir)

    return load_release(extract_dir)


def validate_downloaded_release(current_release: dict, latest: dict, downloaded_release: dict) -> None:
    current_skill_id = current_release.get("skillId", "")
    downloaded_skill_id = downloaded_release.get("skillId", "")
    if downloaded_skill_id != current_skill_id:
        raise ValueError(
            f"downloaded skillId mismatch: expected {current_skill_id}, got {downloaded_skill_id}"
        )

    expected_release_id = latest.get("releaseId", "")
    downloaded_release_id = downloaded_release.get("releaseId", "")
    if not expected_release_id:
        raise ValueError("version response is missing releaseId")
    if downloaded_release_id != expected_release_id:
        raise ValueError(
            f"downloaded releaseId mismatch: expected {expected_release_id}, got {downloaded_release_id}"
        )


def copy_tree_contents(source: Path, target: Path, skip_names: Optional[Set[str]] = None) -> None:
    skip_names = skip_names or set()
    target.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        if entry.name in skip_names:
            continue
        destination = target / entry.name
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        if entry.is_dir() and not entry.is_symlink():
            shutil.copytree(entry, destination)
        else:
            shutil.copy2(entry, destination)


def clear_skill_root(root: Path, preserve_names: Set[str]) -> None:
    for entry in root.iterdir():
        if entry.name in preserve_names:
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def restore_from_backup(root: Path, backup_path: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(backup_path, root)


def backup_current_skill(root: Path, release: dict) -> Path:
    skill_id = safe_name(release.get("skillId", root.name))
    release_id = safe_name(release.get("releaseId") or release.get("version") or "unknown")
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    backup_dir = root.parent / BACKUP_ROOT_NAME / skill_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"{timestamp}-{release_id}"
    suffix = 1
    while backup_path.exists():
        backup_path = backup_dir / f"{timestamp}-{release_id}-{suffix}"
        suffix += 1

    shutil.copytree(root, backup_path)
    return backup_path


def install_update(root: Path, release: dict, latest: dict, download_url: str) -> dict:
    resolved_download_url = resolve_url(download_url)
    if not resolved_download_url:
        raise ValueError("version response did not include a downloadUrl")

    with tempfile.TemporaryDirectory(prefix=".light-skill-upgrade-", dir=str(root.parent)) as temp_root:
        temp_dir = Path(temp_root)
        zip_path = temp_dir / "latest.zip"
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()

        download_file(resolved_download_url, zip_path)
        downloaded_release = extract_validated_zip(zip_path, extract_dir)
        validate_downloaded_release(release, latest, downloaded_release)

        backup_path = backup_current_skill(root, release)
        try:
            clear_skill_root(root, {CACHE_FILE_NAME})
            copy_tree_contents(extract_dir, root, {CACHE_FILE_NAME})
            write_cache(
                root,
                cache_payload(
                    "UPDATED",
                    downloaded_release,
                    downloaded_release.get("version") or downloaded_release.get("releaseId") or "unknown",
                    downloaded_release.get("update", {}).get("downloadUrl", resolved_download_url),
                ),
            )
        except Exception:
            restore_from_backup(root, backup_path)
            raise

    return {
        "status": "UPDATED",
        "skillId": downloaded_release.get("skillId", release.get("skillId", "unknown")),
        "previousReleaseId": release.get("releaseId", ""),
        "currentReleaseId": downloaded_release.get("releaseId", ""),
        "previousVersion": release.get("version", ""),
        "currentVersion": downloaded_release.get("version", ""),
        "backupPath": str(backup_path),
        "downloadUrl": resolved_download_url,
    }


def upgrade_if_available(root: Path, release: dict, latest: dict) -> dict:
    latest_version = latest.get("version") or latest.get("releaseId") or "unknown"
    download_url = latest.get("downloadUrl") or release.get("update", {}).get("downloadUrl", "")
    if not latest.get("updateAvailable"):
        write_cache(root, cache_payload("UP_TO_DATE", latest, latest_version, download_url))
        return {
            "status": "UP_TO_DATE",
            "skillId": latest.get("skillId", release.get("skillId", "unknown")),
            "previousReleaseId": release.get("releaseId", ""),
            "currentReleaseId": latest.get("releaseId", release.get("releaseId", "")),
            "previousVersion": release.get("version", ""),
            "currentVersion": latest.get("version", release.get("version", "")),
            "backupPath": "",
            "downloadUrl": download_url,
        }

    return install_update(root, release, latest, download_url)


def cache_payload(status: str, latest: dict, latest_version: str, download_url: str) -> dict:
    return {
        "schemaVersion": 1,
        "lastCheckedAt": iso_utc(utc_now()),
        "lastStatus": status,
        "latestReleaseId": latest.get("releaseId", ""),
        "latestVersion": latest_version,
        "downloadUrl": download_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether this Light Skill package has an update.")
    parser.add_argument("--brief", action="store_true", help="print a single agent-friendly status")
    parser.add_argument("--force", action="store_true", help="ignore local daily cache and request latest version")
    parser.add_argument("--json", action="store_true", help="print raw JSON result")
    parser.add_argument("--upgrade", action="store_true", help="download and install the latest package when an update is available")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        release = load_release(root)
        cache = load_cache(root)
        if not args.force and not args.upgrade and cache_is_fresh(cache, check_interval_hours()):
            skill = release.get("skillId", "unknown")
            status = cache.get("lastStatus", "UNKNOWN")
            checked_at = cache.get("lastCheckedAt", "")
            if args.json:
                print(json.dumps({"skillId": skill, "status": "SKIPPED_RECENTLY", **cache}, ensure_ascii=False, indent=2))
            else:
                print(f"SKIPPED_RECENTLY skill={skill} lastStatus={status} lastCheckedAt={checked_at}")
            return 0

        check_url = resolve_url(release.get("update", {}).get("checkUrl", ""))
        latest = fetch_latest(check_url, release)
    except (OSError, json.JSONDecodeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        skill = "unknown"
        try:
            skill = load_release(root).get("skillId", "unknown")
        except Exception:
            pass
        if args.json:
            print(json.dumps({"skillId": skill, "status": "UPDATE_CHECK_UNAVAILABLE", "reason": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f'UPDATE_CHECK_UNAVAILABLE skill={skill} reason="{exc}"')
        return 0

    if args.upgrade:
        try:
            result = upgrade_if_available(root, release, latest)
        except Exception as exc:
            skill = release.get("skillId", "unknown")
            if args.json:
                print(json.dumps({"skillId": skill, "status": "UPDATE_FAILED", "reason": str(exc)}, ensure_ascii=False, indent=2))
            else:
                print(f'UPDATE_FAILED skill={skill} reason="{exc}"')
            return 1

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result["status"] == "UPDATED":
            print(
                f"UPDATED skill={result['skillId']} previous={result['previousReleaseId']} "
                f"current={result['currentReleaseId']} backup={result['backupPath']}"
            )
        else:
            print(
                f"UP_TO_DATE skill={result['skillId']} installed={result['previousVersion'] or result['previousReleaseId'] or 'unknown'} "
                f"latest={result['currentVersion'] or result['currentReleaseId'] or 'unknown'}"
            )
        return 0

    if args.json:
        print(json.dumps(latest, ensure_ascii=False, indent=2))
        return 0

    skill_id = latest.get("skillId", release.get("skillId", "unknown"))
    installed = release.get("version") or release.get("releaseId") or "unknown"
    latest_version = latest.get("version") or latest.get("releaseId") or "unknown"
    download_url = latest.get("downloadUrl") or release.get("update", {}).get("downloadUrl", "")

    if latest.get("updateAvailable"):
        write_cache(root, cache_payload("UPDATE_AVAILABLE", latest, latest_version, download_url))
        print(
            f"UPDATE_AVAILABLE skill={skill_id} installed={installed} "
            f"latest={latest_version} download={download_url}"
        )
        notes = latest.get("releaseNotes", "")
        if notes:
            print(f"Release notes: {notes}")
        return 0

    write_cache(root, cache_payload("UP_TO_DATE", latest, latest_version, download_url))
    print(f"UP_TO_DATE skill={skill_id} installed={installed} latest={latest_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
