"""Progress logging for long-running fund-wiki jobs."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from threading import Lock

from fund_profile_wiki.config import Settings


class ProgressLogger:
    """Write progress to stderr and a per-run log file."""

    def __init__(self, run_id: str = "", log_path: str | None = None):
        self.run_id = run_id or "no-run-id"
        explicit_path = log_path or os.environ.get("FPW_RUN_LOG_PATH")
        self.path = (
            Path(explicit_path)
            if explicit_path
            else Settings.run_logs_dir / "runs" / f"{safe_filename(self.run_id)}.log"
        )
        self._lock = Lock()

    def info(self, stage: str, message: str) -> None:
        self._write("INFO", stage, message)

    def warning(self, stage: str, message: str) -> None:
        self._write("WARN", stage, message)

    def error(self, stage: str, message: str) -> None:
        self._write("ERROR", stage, message)

    def _write(self, level: str, stage: str, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] run_id={self.run_id} stage={stage} {message}"
        with self._lock:
            print(line, file=sys.stderr, flush=True)
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
            except OSError:
                pass


def safe_filename(name: str) -> str:
    for ch in '<>:"/\\|?*\n\r\t':
        name = name.replace(ch, "_")
    return name.strip(" .") or "untitled"
