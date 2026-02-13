from __future__ import annotations

from typing import Protocol

from auto_leetcode.models.submission import SubmissionResult


class ResultRepository(Protocol):
    def save(self, result: SubmissionResult) -> None: ...

    def find_by_problem_id(self, problem_id: int) -> list[SubmissionResult]: ...

    def find_all_accepted(self) -> list[SubmissionResult]: ...

    def is_solved(self, problem_id: int) -> bool: ...
