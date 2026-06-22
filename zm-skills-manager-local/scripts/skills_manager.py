#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile


DEFAULT_BASE_URL = "http://10.168.30.147:5173"
TARGET_DIRS = {
    "codex": Path.home() / ".codex" / "skills",
    "trae": Path.home() / ".trae" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
    "claude": Path.home() / ".claude" / "skills",
}


def base_url() -> str:
    return os.environ.get("LIGHT_SKILL_MANAGER_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def api_url(path: str, query: dict | None = None) -> str:
    url = f"{base_url()}{path if path.startswith('/') else '/' + path}"
    if query:
        items = {key: value for key, value in query.items() if value not in (None, "")}
        if items:
            url = f"{url}?{urllib.parse.urlencode(items)}"
    return url


def request_json(path: str, query: dict | None = None) -> dict:
    with urllib.request.urlopen(api_url(path, query), timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_zip_name(info: zipfile.ZipInfo) -> str:
    raw = info.filename
    normalized = raw.replace("\\", "/")
    path = PurePosixPath(normalized)
    if raw.startswith("/") or path.is_absolute() or not normalized:
        raise ValueError(f"unsafe zip entry: {raw}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe zip entry: {raw}")
    if ":" in (path.parts[0] if path.parts else ""):
        raise ValueError(f"unsafe zip entry: {raw}")
    return normalized


def extract_skill_zip(zip_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        names = {safe_zip_name(info).rstrip("/") for info in archive.infolist()}
        if "SKILL.md" not in names:
            raise ValueError("zip does not contain root-level SKILL.md")
        archive.extractall(target_dir)


def detect_targets() -> list[tuple[str, Path]]:
    return [(name, path) for name, path in TARGET_DIRS.items() if path.exists()]


def resolve_target(args) -> Path:
    if args.dest:
        return Path(args.dest).expanduser().resolve()
    if args.target:
        return TARGET_DIRS[args.target].expanduser().resolve()
    detected = detect_targets()
    if len(detected) == 1:
        return detected[0][1].resolve()
    if len(detected) > 1:
        print("TARGET_REQUIRED multiple skills directories found:")
        for name, path in detected:
            print(f"{name}\t{path}")
        raise SystemExit(2)
    print("TARGET_REQUIRED no default skills directory found; pass --dest")
    raise SystemExit(2)


def command_targets(_args) -> None:
    for name, path in TARGET_DIRS.items():
        status = "exists" if path.exists() else "missing"
        print(f"{name}\t{status}\t{path}")


def command_find(args) -> None:
    payload = request_json("/api/hub/skills", {"q": args.query, "tag": args.tag})
    skills = payload.get("skills", [])
    if args.json:
        print(json.dumps(skills, ensure_ascii=False, indent=2))
        return
    for skill in skills:
        tags = ",".join(skill.get("tags") or [])
        print(f"{skill.get('id')}\t{skill.get('sourceKind', '')}\t{tags}\t{skill.get('name')}\t{skill.get('description')}")


def command_info(args) -> None:
    skill = request_json(f"/api/hub/skills/{args.skill_id}")
    if args.json:
        print(json.dumps(skill, ensure_ascii=False, indent=2))
        return
    print(f"id: {skill.get('id')}")
    print(f"name: {skill.get('name')}")
    print(f"sourceKind: {skill.get('sourceKind')}")
    print(f"tags: {', '.join(skill.get('tags') or [])}")
    print(f"description: {skill.get('description')}")
    print(f"download: {base_url()}{skill.get('downloadPath') or skill.get('downloadUrl')}")


def download_skill(skill_id: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    url = api_url(f"/api/hub/skills/{skill_id}/download")
    request = urllib.request.Request(url, headers={"accept": "application/zip"})
    with urllib.request.urlopen(request, timeout=120) as response:
        disposition = response.headers.get("content-disposition", "")
        match = None
        for part in disposition.split(";"):
            part = part.strip()
            if part.lower().startswith("filename="):
                match = part.split("=", 1)[1].strip('"')
        filename = match or f"{skill_id}.zip"
        zip_path = out_dir / filename
        with zip_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    return zip_path


def command_download(args) -> None:
    zip_path = download_skill(args.skill_id, Path(args.out).expanduser().resolve())
    print(f"DOWNLOADED skill={args.skill_id} path={zip_path}")


def command_install(args) -> None:
    target_root = resolve_target(args)
    target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zm-skills-manager-") as temp:
        zip_path = download_skill(args.skill_id, Path(temp))
        install_dir = target_root / args.skill_id
        if install_dir.exists() and not args.force:
            print(f"INSTALL_EXISTS skill={args.skill_id} path={install_dir}")
            raise SystemExit(2)
        staging = Path(temp) / "extract"
        staging.mkdir()
        extract_skill_zip(zip_path, staging)
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.copytree(staging, install_dir)
    print(f"INSTALLED skill={args.skill_id} path={install_dir}")


def iter_installed_skills(root: Path):
    if not root.exists():
        return
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / ".light-skill-release.json").exists():
            yield child


def update_one(skill_dir: Path) -> int:
    checker = skill_dir / "scripts" / "light_skill_check_update.py"
    if not checker.exists():
        print(f"SKIP_NO_CHECKER path={skill_dir}")
        return 0
    result = subprocess.run(
        [sys.executable, str(checker), "--force", "--upgrade", "--brief"],
        cwd=str(skill_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout or result.stderr or "").strip()
    print(output or f"UPDATE_EXIT code={result.returncode} path={skill_dir}")
    return result.returncode


def command_update(args) -> None:
    target_root = resolve_target(args)
    if args.all:
        failures = 0
        for skill_dir in iter_installed_skills(target_root) or []:
            failures += 1 if update_one(skill_dir) else 0
        raise SystemExit(1 if failures else 0)
    if not args.skill_id:
        print("skill id is required unless --all is used")
        raise SystemExit(2)
    raise SystemExit(update_one(target_root / args.skill_id))


def zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(source_dir).as_posix()
            if rel.startswith((".git/", ".venv/", "node_modules/")):
                continue
            archive.write(path, rel)


def multipart_upload(fields: dict, file_path: Path) -> dict:
    boundary = "----zm-skills-manager-boundary"
    chunks: list[bytes] = []
    for key, value in fields.items():
        if value is None:
            continue
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
            str(value).encode("utf-8"),
            b"\r\n",
        ])
    chunks.extend([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
        b"Content-Type: application/zip\r\n\r\n",
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    data = b"".join(chunks)
    request = urllib.request.Request(
        api_url("/api/hub/skills/uploads"),
        data=data,
        method="POST",
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def command_upload(args) -> None:
    source = Path(args.path).expanduser().resolve()
    if not source.exists():
        print(f"UPLOAD_SOURCE_MISSING path={source}")
        raise SystemExit(2)
    with tempfile.TemporaryDirectory(prefix="zm-skills-manager-upload-") as temp:
        if source.is_dir():
            zip_path = Path(temp) / f"{source.name}.zip"
            zip_directory(source, zip_path)
        else:
            zip_path = source
        payload = multipart_upload(
            {
                "name": args.name,
                "owner": args.owner,
                "description": args.description or "",
                "requestedId": args.requested_id or "",
                "tags": ",".join(args.tag or []),
                "force": "true" if args.force else "",
            },
            zip_path,
        )
    print(
        "UPLOAD_PUBLISHED "
        f"skill={payload.get('skillId')} "
        f"sourceKind={payload.get('sourceKind')} "
        f"tags={','.join(payload.get('tags') or [])}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find, install, update, and upload ZM Skills.")
    sub = parser.add_subparsers(required=True)

    find = sub.add_parser("find")
    find.add_argument("query", nargs="?", default="")
    find.add_argument("--tag", default="")
    find.add_argument("--json", action="store_true")
    find.set_defaults(func=command_find)

    info = sub.add_parser("info")
    info.add_argument("skill_id")
    info.add_argument("--json", action="store_true")
    info.set_defaults(func=command_info)

    download = sub.add_parser("download")
    download.add_argument("skill_id")
    download.add_argument("--out", default=".")
    download.set_defaults(func=command_download)

    install = sub.add_parser("install")
    install.add_argument("skill_id")
    install.add_argument("--target", choices=sorted(TARGET_DIRS))
    install.add_argument("--dest")
    install.add_argument("--force", action="store_true")
    install.set_defaults(func=command_install)

    update = sub.add_parser("update")
    update.add_argument("skill_id", nargs="?")
    update.add_argument("--all", action="store_true")
    update.add_argument("--target", choices=sorted(TARGET_DIRS))
    update.add_argument("--dest")
    update.set_defaults(func=command_update)

    upload = sub.add_parser("upload")
    upload.add_argument("path")
    upload.add_argument("--name", required=True)
    upload.add_argument("--owner", required=True)
    upload.add_argument("--description", default="")
    upload.add_argument("--requested-id")
    upload.add_argument("--tag", action="append")
    upload.add_argument("--force", action="store_true")
    upload.set_defaults(func=command_upload)

    targets = sub.add_parser("targets")
    targets.set_defaults(func=command_targets)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
