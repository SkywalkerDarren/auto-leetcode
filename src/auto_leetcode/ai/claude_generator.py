from __future__ import annotations

import logging

from anthropic import APIError, AsyncAnthropic

from auto_leetcode.ai.prompt import (
    SYSTEM_PROMPT,
    build_user_prompt,
    extract_code,
    extract_reasoning,
)
from auto_leetcode.errors import AIGenerationError
from auto_leetcode.models.problem import Problem
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult

logger = logging.getLogger(__name__)


class ClaudeGenerator:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key, base_url=base_url)
        self._model = model

    async def generate(
        self,
        problem: Problem,
        previous_attempts: list[SubmissionResult],
    ) -> Solution:
        user_prompt = build_user_prompt(problem, previous_attempts)

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except APIError as e:
            raise AIGenerationError(
                f"Claude API call failed for problem #{problem.id}: {e}"
            ) from e

        text_blocks = [b.text for b in response.content if b.type == "text"]
        content = text_blocks[0] if text_blocks else ""
        code = extract_code(content)
        reasoning = extract_reasoning(content)

        if not code.strip():
            raise AIGenerationError(
                f"Empty code generated for problem #{problem.id}"
            )

        return Solution(
            problem_id=problem.id,
            code=code,
            language="python3",
            model_used=self._model,
            attempt=len(previous_attempts) + 1,
            reasoning=reasoning,
        )
