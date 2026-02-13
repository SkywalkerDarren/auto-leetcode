from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from auto_leetcode.errors import StorageError
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult, SubmissionStatus

logger = logging.getLogger(__name__)


class JsonRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._solved_ids: set[int] = set()
        self._load_solved_ids()

    def _load_solved_ids(self) -> None:
        if not self._path.exists():
            return
        try:
            with open(self._path) as f:
                for raw_line in f:
                    stripped = raw_line.strip()
                    if not stripped:
                        continue
                    record = json.loads(stripped)
                    if record.get("status") == "Accepted":
                        self._solved_ids.add(record["problem_id"])
        except (json.JSONDecodeError, OSError) as e:
            raise StorageError(f"Failed to load results from {self._path}: {e}") from e

    def save(self, result: SubmissionResult) -> None:
        record = {
            "problem_id": result.problem_id,
            "status": result.status.value,
            "runtime_ms": result.runtime_ms,
            "memory_mb": result.memory_mb,
            "model": result.solution.model_used,
            "attempt": result.solution.attempt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if result.error_message:
            record["error_message"] = result.error_message

        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as e:
            raise StorageError(f"Failed to write result: {e}") from e

        if result.status == SubmissionStatus.ACCEPTED:
            self._solved_ids = self._solved_ids | {result.problem_id}

    def find_by_problem_id(self, problem_id: int) -> list[SubmissionResult]:
        return self._read_all(lambda r: r["problem_id"] == problem_id)

    def find_all_accepted(self) -> list[SubmissionResult]:
        return self._read_all(lambda r: r["status"] == "Accepted")

    def is_solved(self, problem_id: int) -> bool:
        return problem_id in self._solved_ids

    def _read_all(
        self, predicate: Callable[[dict[str, Any]], bool] | None = None
    ) -> list[SubmissionResult]:
        if not self._path.exists():
            return []
        results: list[SubmissionResult] = []
        try:
            with open(self._path) as f:
                for raw_line in f:
                    stripped = raw_line.strip()
                    if not stripped:
                        continue
                    record = json.loads(stripped)
                    if predicate and not predicate(record):
                        continue
                    results.append(
                        SubmissionResult(
                            problem_id=record["problem_id"],
                            status=SubmissionStatus(record["status"]),
                            runtime_ms=record.get("runtime_ms"),
                            memory_mb=record.get("memory_mb"),
                            error_message=record.get("error_message"),
                            solution=Solution(
                                problem_id=record["problem_id"],
                                code="",
                                language="python3",
                                model_used=record.get("model", ""),
                                attempt=record.get("attempt", 0),
                            ),
                        )
                    )
        except (json.JSONDecodeError, OSError) as e:
            raise StorageError(f"Failed to read results: {e}") from e
        return results
