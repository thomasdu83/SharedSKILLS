#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_UPDATE_BASE_URL = "http://10.168.30.147:5173"


def load_release(root: Path) -> dict:
    release_path = root / ".light-skill-release.json"
    with release_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cache(root: Path) -> dict:
    cache_path = root / ".light-skill-update-cache.json"
    if not cache_path.exists():
        return {}
    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_cache(root: Path, payload: dict) -> None:
    cache_path = root / ".light-skill-update-cache.json"
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
    if value.startswith("http://") or value.startswith("https://"):
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
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        release = load_release(root)
        cache = load_cache(root)
        if not args.force and cache_is_fresh(cache, check_interval_hours()):
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
        print(f'UPDATE_CHECK_UNAVAILABLE skill={skill} reason="{exc}"')
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
