from __future__ import annotations

import logging
from pathlib import Path

from auto_leetcode.errors import StorageError
from auto_leetcode.models.solution import Solution

logger = logging.getLogger(__name__)


class FileSaver:
    def __init__(self, solutions_dir: Path) -> None:
        self._dir = solutions_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, solution: Solution) -> Path:
        filename = f"{solution.problem_id:04d}.py"
        filepath = self._dir / filename
        header = (
            f"# Problem #{solution.problem_id}\n"
            f"# Model: {solution.model_used}\n"
            f"# Attempt: {solution.attempt}\n\n"
        )
        try:
            filepath.write_text(header + solution.code + "\n")
        except OSError as e:
            raise StorageError(f"Failed to save solution to {filepath}: {e}") from e

        logger.info("Saved solution to %s", filepath)
        return filepath
