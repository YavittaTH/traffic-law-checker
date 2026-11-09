"""All runtime settings, read from the environment (and an optional .env file).

Nothing else in the project reads os.environ directly -- import `get_settings()` instead.
Secrets (API key / base URL) are never given defaults, so a missing key fails loudly.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "index"
EVAL_DIR = PROJECT_ROOT / "eval"

SECTIONS_PATH = PROCESSED_DIR / "sections.jsonl"
PENALTIES_PATH = DATA_DIR / "penalties.csv"


class ConfigError(RuntimeError):
    """Raised when a required setting is missing or invalid."""


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from e


def _float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        return float(raw)
    except ValueError as e:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from e


@dataclass(frozen=True)
class Settings:
    # LLM proxy
    openai_api_key: str | None
    openai_base_url: str | None
    llm_model: str
    # retrieval
    embed_model: str
    # classic RAG (rag.py): sources per answer and the BM25 floor
    rag_k: int
    rag_min_score: float
    # agent
    agent_max_steps: int
    # point system (ระเบียบ...คะแนนความประพฤติ พ.ศ. ๒๕๖๕ ข้อ ๗ and ข้อ ๑๑)
    points_start: int
    points_incident_cap: int

    def require_llm(self) -> None:
        """Call before any LLM request; gives a clear message instead of an auth error."""
        missing = [n for n, v in (("OPENAI_API_KEY", self.openai_api_key),
                                  ("OPENAI_BASE_URL", self.openai_base_url)) if not v]
        if missing:
            raise ConfigError(
                f"Missing {', '.join(missing)}. Copy .env.example to .env and fill them in."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:  # python-dotenv is optional for the offline tests
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env", override=False)
    except ImportError:
        pass
    s = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
        llm_model=os.getenv("LLM_MODEL") or "gemma-4-E4B-it",
        embed_model=os.getenv("EMBED_MODEL", "BAAI/bge-m3"),
        rag_k=_int("RAG_K", 8),
        rag_min_score=_float("RAG_MIN_SCORE", 1.0),
        agent_max_steps=_int("AGENT_MAX_STEPS", 6),
        points_start=_int("POINTS_START", 12),
        points_incident_cap=_int("POINTS_INCIDENT_CAP", 8),
    )
    if not 1 <= s.agent_max_steps <= 20:
        raise ConfigError("AGENT_MAX_STEPS must be between 1 and 20")
    if s.points_start <= 0:
        raise ConfigError("POINTS_START must be positive")
    return s
