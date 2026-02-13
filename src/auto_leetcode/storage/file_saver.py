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
        parts = [
            f"# Problem #{solution.problem_id}",
            f"# Model: {solution.model_used}",
            f"# Attempt: {solution.attempt}",
        ]
        if solution.reasoning:
            reasoning_lines = solution.reasoning.split("\n")
            parts.append("#")
            parts.append("# Approach:")
            for line in reasoning_lines:
                parts.append(f"# {line}" if line.strip() else "#")
        parts.append("")
        parts.append(solution.code)
        parts.append("")

        try:
            filepath.write_text("\n".join(parts))
        except OSError as e:
            raise StorageError(f"Failed to save solution to {filepath}: {e}") from e

        logger.info("Saved solution to %s", filepath)
        return filepath
