from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from auto_leetcode.config import Config
from auto_leetcode.errors import AIGenerationError, LeetCodeClientError
from auto_leetcode.models.problem import Problem
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult, SubmissionStatus
from auto_leetcode.runner import _solve_problem


def _config(tmp_path: Path) -> Config:
    return Config(
        leetcode_session="s",
        csrf_token="c",
        ai_provider="openai",
        ai_api_key="k",
        ai_base_url="http://localhost",
        ai_model="gpt-4o",
        start_id=1,
        end_id=1,
        max_retries=2,
        retry_delay_seconds=0.0,
        submit_delay_seconds=0.0,
        solutions_dir=tmp_path / "solutions",
        results_path=tmp_path / "results.jsonl",
    )


def _problem() -> Problem:
    return Problem(
        id=1,
        title="Two Sum",
        slug="two-sum",
        difficulty="Easy",
        description="Given an array...",
        code_snippet="class Solution:\n    def twoSum(self):",
        paid_only=False,
    )


def _solution(attempt: int = 1) -> Solution:
    return Solution(
        problem_id=1,
        code="return [0, 1]",
        language="python3",
        model_used="gpt-4o",
        attempt=attempt,
    )


def _result(status: SubmissionStatus = SubmissionStatus.ACCEPTED) -> SubmissionResult:
    return SubmissionResult(
        problem_id=1,
        status=status,
        runtime_ms=40,
        memory_mb=16.5,
        error_message=None,
        solution=_solution(),
    )


class TestSolveProblem:
    @pytest.fixture()
    def deps(self, tmp_path: Path) -> dict:
        from auto_leetcode.storage.file_saver import FileSaver
        from auto_leetcode.storage.json_repository import JsonRepository

        client = AsyncMock()
        client._http = MagicMock()
        generator = AsyncMock()
        repository = JsonRepository(tmp_path / "results.jsonl")
        saver = FileSaver(tmp_path / "solutions")
        config = _config(tmp_path)
        return {
            "client": client,
            "generator": generator,
            "repository": repository,
            "saver": saver,
            "config": config,
        }

    @pytest.mark.asyncio
    async def test_skips_already_solved(self, deps: dict, tmp_path: Path) -> None:
        deps["repository"].save(_result())
        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )
        deps["client"].fetch_problem.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_paid_only(self, deps: dict) -> None:
        paid_problem = Problem(
            id=1, title="P", slug="p", difficulty="Easy",
            description="d", code_snippet="c", paid_only=True,
        )
        deps["client"].fetch_problem = AsyncMock(return_value=paid_problem)
        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )
        deps["generator"].generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_no_snippet(self, deps: dict) -> None:
        no_snippet = Problem(
            id=1, title="P", slug="p", difficulty="Easy",
            description="d", code_snippet="", paid_only=False,
        )
        deps["client"].fetch_problem = AsyncMock(return_value=no_snippet)
        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )
        deps["generator"].generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_accepted_on_first_try(self, deps: dict) -> None:
        deps["client"].fetch_problem = AsyncMock(return_value=_problem())
        deps["generator"].generate = AsyncMock(return_value=_solution())
        deps["client"].submit = AsyncMock(
            return_value=_result(SubmissionStatus.ACCEPTED),
        )

        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )

        assert deps["repository"].is_solved(1)

    @pytest.mark.asyncio
    async def test_retries_on_wrong_answer(self, deps: dict) -> None:
        deps["client"].fetch_problem = AsyncMock(return_value=_problem())
        deps["generator"].generate = AsyncMock(return_value=_solution())

        wrong = _result(SubmissionStatus.WRONG_ANSWER)
        accepted = _result(SubmissionStatus.ACCEPTED)
        deps["client"].submit = AsyncMock(side_effect=[wrong, accepted])

        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )

        assert deps["repository"].is_solved(1)
        assert deps["generator"].generate.call_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries(self, deps: dict) -> None:
        deps["client"].fetch_problem = AsyncMock(return_value=_problem())
        deps["generator"].generate = AsyncMock(return_value=_solution())

        wrong = _result(SubmissionStatus.WRONG_ANSWER)
        deps["client"].submit = AsyncMock(return_value=wrong)

        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )

        assert not deps["repository"].is_solved(1)

    @pytest.mark.asyncio
    async def test_handles_ai_generation_error(self, deps: dict) -> None:
        deps["client"].fetch_problem = AsyncMock(return_value=_problem())
        deps["generator"].generate = AsyncMock(
            side_effect=AIGenerationError("API down")
        )

        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )
        assert not deps["repository"].is_solved(1)

    @pytest.mark.asyncio
    async def test_handles_fetch_error(self, deps: dict) -> None:
        deps["client"].fetch_problem = AsyncMock(
            side_effect=LeetCodeClientError("Network error")
        )
        await _solve_problem(
            deps["client"], deps["generator"], deps["repository"],
            deps["saver"], deps["config"], 1,
        )
        deps["generator"].generate.assert_not_called()
