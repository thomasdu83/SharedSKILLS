#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_CONFIG = Path.home() / ".config" / "codex-custom-gpt-image-2" / "config.json"


def load_config(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("base_url", "api_key"):
        if not cfg.get(key):
            raise SystemExit(f"Missing required config field: {key}")
    cfg.setdefault("model", "gpt-image-2")
    return cfg


def read_prompt(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.prompt_file:
        parts.append(Path(args.prompt_file).read_text(encoding="utf-8"))
    if args.prompt:
        parts.append(args.prompt)
    prompt = "\n\n".join(p.strip() for p in parts if p and p.strip())
    if not prompt:
        raise SystemExit("Provide --prompt or --prompt-file")
    return prompt


def request_image(cfg: dict, payload: dict, timeout: int) -> dict:
    url = cfg["base_url"].rstrip("/") + "/v1/images/generations"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + cfg["api_key"],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {body[:4000]}")
    except Exception as e:
        raise SystemExit(f"Request failed: {e!r}")


def save_image(data: dict, cfg: dict, out: Path, timeout: int) -> None:
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise SystemExit("Unexpected response: missing data[]")
    item = items[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    if "b64_json" in item:
        out.write_bytes(base64.b64decode(item["b64_json"]))
        return
    if "url" in item:
        req = urllib.request.Request(
            item["url"],
            headers={"Authorization": "Bearer " + cfg["api_key"]},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                out.write_bytes(resp.read())
                return
        except Exception as e:
            raise SystemExit(f"Could not download image URL: {e!r}")
    raise SystemExit("Unexpected response: no b64_json or url in data[0]")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an image with the configured custom gpt-image-2 endpoint.")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--out", required=True)
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    parser.add_argument("--model", help="Override configured model")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_config(Path(args.config).expanduser())
    prompt = read_prompt(args)
    payload = {
        "model": args.model or cfg.get("model", "gpt-image-2"),
        "prompt": prompt,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
    }
    if args.dry_run:
        safe_payload = dict(payload)
        safe_cfg = {"base_url": cfg["base_url"], "model": cfg.get("model", "gpt-image-2"), "api_key": "***"}
        print(json.dumps({"config": safe_cfg, "payload": safe_payload, "out": args.out}, ensure_ascii=False, indent=2))
        return 0

    data = request_image(cfg, payload, args.timeout)
    out = Path(args.out)
    save_image(data, cfg, out, args.timeout)
    print(out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
