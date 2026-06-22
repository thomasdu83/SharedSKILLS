"""Manager alias registry for confirmed identity overrides."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import re
from typing import Iterable

import yaml


ENV_ALIAS_FILE = "FPW_MANAGER_ALIAS_FILE"
DEFAULT_ALIAS_FILE = (
    Path(__file__).resolve().parents[4] / "references" / "manager-aliases.yaml"
)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def registered_manager_aliases(manager: str, path: Path | None = None) -> list[str]:
    """Return confirmed aliases when *manager* belongs to a registry group."""

    key = normalize_alias_text(manager)
    if not key:
        return []
    for group in load_manager_alias_groups(path):
        if key in group["keys"]:
            return clean_aliases([group["canonical"], *group["aliases"]])
    return []


def registered_manager_identity_key(manager: str, path: Path | None = None) -> str:
    """Return a confirmed identity key for *manager* when one is registered."""

    key = normalize_alias_text(manager)
    if not key:
        return ""
    for group in load_manager_alias_groups(path):
        if key in group["keys"]:
            return normalize_alias_text(group["identity_key"] or group["canonical"])
    return ""


def load_manager_alias_groups(path: Path | None = None) -> list[dict]:
    alias_path = resolve_alias_file(path)
    return _load_manager_alias_groups(str(alias_path))


def clear_manager_alias_registry_cache() -> None:
    _load_manager_alias_groups.cache_clear()


def resolve_alias_file(path: Path | None = None) -> Path:
    if path is not None:
        return path
    env_path = os.environ.get(ENV_ALIAS_FILE)
    if env_path:
        return Path(env_path)
    return DEFAULT_ALIAS_FILE


@lru_cache(maxsize=16)
def _load_manager_alias_groups(path_text: str) -> list[dict]:
    path = Path(path_text)
    if not path.exists():
        return []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    if isinstance(payload, dict):
        rows = payload.get("managers", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []
    groups: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        canonical = str(row.get("canonical", "") or "").strip()
        if not canonical:
            continue
        aliases = normalize_list(row.get("aliases", []))
        identity_key = str(row.get("identity_key", "") or "").strip()
        keys = {
            normalize_alias_text(item)
            for item in [canonical, identity_key, *aliases]
            if normalize_alias_text(item)
        }
        groups.append(
            {
                "canonical": canonical,
                "aliases": aliases,
                "identity_key": identity_key,
                "keys": keys,
            }
        )
    return groups


def normalize_list(values: object) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    return clean_aliases(str(value).strip() for value in values if str(value).strip())


def clean_aliases(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = extract_wikilink(str(value or "").strip())
        key = normalize_alias_text(text)
        if len(key) < 2 or key in seen:
            continue
        result.append(text)
        seen.add(key)
    return result


def extract_wikilink(value: str) -> str:
    match = WIKILINK_RE.search(value)
    return match.group(1).strip() if match else value.strip("'\" ")


def normalize_alias_text(value: object) -> str:
    text = extract_wikilink(str(value or ""))
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[\W_]+", "", text).casefold()
