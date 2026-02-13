import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from auto_leetcode.errors import ConfigError


@dataclass(frozen=True)
class Config:
    leetcode_session: str
    csrf_token: str
    ai_provider: str
    ai_api_key: str
    ai_base_url: str
    ai_model: str
    start_id: int = 1
    end_id: int = 3000
    max_retries: int = 3
    retry_delay_seconds: float = 5.0
    submit_delay_seconds: float = 10.0
    solutions_dir: Path = field(default_factory=lambda: Path("solutions"))
    results_path: Path = field(default_factory=lambda: Path("results.jsonl"))


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ConfigError(f"Missing required environment variable: {key}")
    return value


def load_config(**overrides: Any) -> Config:
    load_dotenv()
    kwargs: dict[str, Any] = {
        "leetcode_session": _require_env("LEETCODE_SESSION"),
        "csrf_token": _require_env("CSRF_TOKEN"),
        "ai_provider": os.environ.get("AI_PROVIDER", "openai"),
        "ai_api_key": _require_env("AI_API_KEY"),
        "ai_base_url": os.environ.get("AI_BASE_URL", "https://api.openai.com/v1"),
        "ai_model": os.environ.get("AI_MODEL", "gpt-4o"),
    }
    kwargs.update(overrides)
    return Config(**kwargs)
