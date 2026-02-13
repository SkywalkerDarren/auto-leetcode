class AutoLeetCodeError(Exception):
    """Base exception for all project errors."""


class ConfigError(AutoLeetCodeError):
    """Missing or invalid configuration."""


class LeetCodeClientError(AutoLeetCodeError):
    """LeetCode API communication failure."""


class LeetCodeAuthError(LeetCodeClientError):
    """Authentication failed (expired session)."""


class LeetCodeRateLimitError(LeetCodeClientError):
    """Rate limited by LeetCode."""


class AIGenerationError(AutoLeetCodeError):
    """AI failed to generate a valid solution."""


class StorageError(AutoLeetCodeError):
    """Failed to read/write local storage."""
