"""Project configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_ROOT = Path(r"Y:\投顾管理人研究\fund_profile_wiki_docs")


def default_parsed_cache_root() -> Path:
    """Resolve the local parsed-text cache root without touching docs_root."""
    configured = os.getenv("FPW_PARSED_CACHE_ROOT")
    if configured:
        return Path(configured)
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "QuantSystem" / "fund-wiki" / "parsed_cache"
    return PROJECT_ROOT.parent / ".cache" / "fund-wiki" / "parsed_cache"


class Settings:
    """Runtime settings for scripts and services."""

    docs_root: Path = Path(os.getenv("FPW_DOCS_ROOT", str(DEFAULT_DOCS_ROOT)))
    source_notes_dir: Path = docs_root / "source_notes"
    product_profiles_dir: Path = docs_root / "product_profiles"
    indexes_dir: Path = docs_root / "indexes"
    reports_dir: Path = docs_root / "reports"
    run_logs_dir: Path = docs_root / "run_logs"
    source_snapshots_dir: Path = docs_root / "source_snapshots"

    product_profile_jsonl: str = "product_profiles.jsonl"
    product_profile_sqlite: str = "product_profiles.sqlite"
    source_manifest_jsonl: str = "source_manifest.jsonl"
    parsed_cache_root: Path = default_parsed_cache_root()
    parsed_cache_ttl_hours: float = float(os.getenv("FPW_PARSED_CACHE_TTL_HOURS", "48"))

    supported_extensions: tuple[str, ...] = (".pdf", ".txt", ".md", ".docx", ".pptx")

    skip_filename_keywords: tuple[str, ...] = (
        "营业执照",
        "身份证",
        "法人身份证",
        "公司章程",
        "公示信息",
        "备案证明",
        "备案函",
        "基金合同",
        "风险揭示书",
        "提供材料清单",
        "承诺函",
        "申报制度",
        "信息披露制度",
        "公平交易制度",
        "风险管理制度",
        "风险控制制度",
        "交易记录制度",
        "内部交易记录",
        "宣传推介",
        "投决会",
        "投委会",
        "投决",
        "投资决策委员会",
        "运营风险控制",
        "内幕交易",
        "合格投资者内部审核",
        "合格投资者风险揭示",
    )

    product_profile_max_evidence_items: int = int(
        os.getenv("FPW_MAX_EVIDENCE_ITEMS", "10")
    )
    product_profile_max_chars: int = int(os.getenv("FPW_PROFILE_MAX_CHARS", "480"))
    ingest_parse_max_workers: int = max(
        1, int(os.getenv("FPW_INGEST_PARSE_MAX_WORKERS", "4"))
    )
    ingest_priority_min_score: int = int(
        os.getenv("FPW_INGEST_PRIORITY_MIN_SCORE", "70")
    )
    llm_timeout_seconds: int = int(os.getenv("FPW_LLM_TIMEOUT_SECONDS", "120"))
    llm_max_retries: int = int(os.getenv("FPW_LLM_MAX_RETRIES", "1"))
    llm_input_max_chars: int = int(os.getenv("FPW_LLM_INPUT_MAX_CHARS", "60000"))
    zmdata_mode: str = os.getenv("FPW_ZMDATA_MODE", "auto").strip().lower() or "auto"
    zmdata_search_page_size: int = int(os.getenv("FPW_ZMDATA_SEARCH_PAGE_SIZE", "10"))

    kimi_api_key: str | None = os.getenv("KIMI_API_KEY")
    deepseek_api_key: str | None = os.getenv("DEEPSEEK_API_KEY")
    openai_api_key: str | None = os.getenv("CHATGPT_API_KEY") or os.getenv(
        "OPENAI_API_KEY"
    )

    kimi_base_url: str = "https://api.moonshot.cn/v1"
    deepseek_base_url: str = "https://api.deepseek.com"
    openai_base_url: str = "https://api.openai.com/v1"

    kimi_model: str | None = os.getenv("FPW_KIMI_MODEL")
    deepseek_model: str = os.getenv("FPW_DEEPSEEK_MODEL", "deepseek-chat")
    openai_model: str = os.getenv("FPW_OPENAI_MODEL", "gpt-4o")


def ensure_output_dirs(settings: type[Settings] = Settings) -> None:
    """Create all output directories."""
    for path in [
        settings.source_notes_dir,
        settings.product_profiles_dir,
        settings.indexes_dir,
        settings.reports_dir,
        settings.run_logs_dir,
        settings.source_snapshots_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
