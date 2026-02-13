import json
from pathlib import Path

import pytest

from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult, SubmissionStatus
from auto_leetcode.storage.file_saver import FileSaver
from auto_leetcode.storage.json_repository import JsonRepository


def _make_result(
    problem_id: int = 1,
    status: SubmissionStatus = SubmissionStatus.ACCEPTED,
) -> SubmissionResult:
    return SubmissionResult(
        problem_id=problem_id,
        status=status,
        runtime_ms=40,
        memory_mb=16.5,
        error_message=None,
        solution=Solution(
            problem_id=problem_id,
            code="return [0, 1]",
            language="python3",
            model_used="gpt-4o",
            attempt=1,
        ),
    )


class TestJsonRepository:
    def test_save_and_is_solved(self, tmp_path: Path) -> None:
        repo = JsonRepository(tmp_path / "results.jsonl")
        result = _make_result(problem_id=1)
        repo.save(result)
        assert repo.is_solved(1)
        assert not repo.is_solved(2)

    def test_find_all_accepted(self, tmp_path: Path) -> None:
        repo = JsonRepository(tmp_path / "results.jsonl")
        repo.save(_make_result(problem_id=1, status=SubmissionStatus.ACCEPTED))
        repo.save(_make_result(problem_id=2, status=SubmissionStatus.WRONG_ANSWER))
        repo.save(_make_result(problem_id=3, status=SubmissionStatus.ACCEPTED))
        accepted = repo.find_all_accepted()
        assert len(accepted) == 2

    def test_find_by_problem_id(self, tmp_path: Path) -> None:
        repo = JsonRepository(tmp_path / "results.jsonl")
        repo.save(_make_result(problem_id=5))
        repo.save(_make_result(problem_id=10))
        results = repo.find_by_problem_id(5)
        assert len(results) == 1
        assert results[0].problem_id == 5

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "results.jsonl"
        record = {
            "problem_id": 42,
            "status": "Accepted",
            "runtime_ms": 30,
            "memory_mb": 15.0,
            "model": "gpt-4o",
            "attempt": 1,
            "timestamp": "2026-01-01T00:00:00Z",
        }
        path.write_text(json.dumps(record) + "\n")
        repo = JsonRepository(path)
        assert repo.is_solved(42)

    def test_empty_file(self, tmp_path: Path) -> None:
        repo = JsonRepository(tmp_path / "nonexistent.jsonl")
        assert not repo.is_solved(1)
        assert repo.find_all_accepted() == []


class TestFileSaver:
    def test_saves_solution_file(self, tmp_path: Path) -> None:
        saver = FileSaver(tmp_path / "solutions")
        solution = Solution(
            problem_id=1,
            code="class Solution:\n    def twoSum(self): pass",
            language="python3",
            model_used="gpt-4o",
            attempt=1,
        )
        path = saver.save(solution)
        assert path.exists()
        assert path.name == "0001.py"
        content = path.read_text()
        assert "Problem #1" in content
        assert "def twoSum" in content

    def test_creates_directory(self, tmp_path: Path) -> None:
        saver = FileSaver(tmp_path / "nested" / "solutions")
        solution = Solution(
            problem_id=99,
            code="pass",
            language="python3",
            model_used="gpt-4o",
            attempt=1,
        )
        path = saver.save(solution)
        assert path.exists()
