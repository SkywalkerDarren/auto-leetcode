import os
from pathlib import Path
from unittest.mock import patch

import pytest

from auto_leetcode.config import Config, load_config
from auto_leetcode.errors import ConfigError


class TestConfig:
    def test_frozen_dataclass(self) -> None:
        config = Config(
            leetcode_session="sess",
            csrf_token="csrf",
            ai_provider="openai",
            ai_api_key="key",
            ai_base_url="http://localhost",
            ai_model="gpt-4o",
        )
        with pytest.raises(AttributeError):
            config.ai_model = "other"  # type: ignore[misc]

    def test_defaults(self) -> None:
        config = Config(
            leetcode_session="s",
            csrf_token="c",
            ai_provider="openai",
            ai_api_key="k",
            ai_base_url="http://localhost",
            ai_model="gpt-4o",
        )
        assert config.start_id == 1
        assert config.end_id == 3000
        assert config.max_retries == 3
        assert config.solutions_dir == Path("solutions")


class TestLoadConfig:
    def test_missing_env_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError, match="LEETCODE_SESSION"):
                load_config()

    def test_loads_from_env(self) -> None:
        env = {
            "LEETCODE_SESSION": "test_session",
            "CSRF_TOKEN": "test_csrf",
            "AI_API_KEY": "test_key",
            "AI_PROVIDER": "claude",
            "AI_BASE_URL": "http://proxy.example.com/v1",
            "AI_MODEL": "claude-sonnet-4-20250514",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
        assert config.leetcode_session == "test_session"
        assert config.ai_provider == "claude"
        assert config.ai_model == "claude-sonnet-4-20250514"

    def test_overrides(self) -> None:
        env = {
            "LEETCODE_SESSION": "s",
            "CSRF_TOKEN": "c",
            "AI_API_KEY": "k",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config(start_id=100, end_id=200)
        assert config.start_id == 100
        assert config.end_id == 200
