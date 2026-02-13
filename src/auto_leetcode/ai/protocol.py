from __future__ import annotations

from typing import Protocol

from auto_leetcode.models.problem import Problem
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult


class SolutionGenerator(Protocol):
    async def generate(
        self,
        problem: Problem,
        previous_attempts: list[SubmissionResult],
    ) -> Solution: ...
