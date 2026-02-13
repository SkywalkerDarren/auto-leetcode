from __future__ import annotations

import logging

from openai import APIError, AsyncOpenAI

from auto_leetcode.ai.prompt import SYSTEM_PROMPT, build_user_prompt, extract_code
from auto_leetcode.errors import AIGenerationError
from auto_leetcode.models.problem import Problem
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult

logger = logging.getLogger(__name__)


class OpenAIGenerator:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def generate(
        self,
        problem: Problem,
        previous_attempts: list[SubmissionResult],
    ) -> Solution:
        user_prompt = build_user_prompt(problem, previous_attempts)

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except APIError as e:
            raise AIGenerationError(
                f"OpenAI API call failed for problem #{problem.id}: {e}"
            ) from e

        if not response.choices:
            raise AIGenerationError(
                f"No choices returned for problem #{problem.id}"
            )

        content = response.choices[0].message.content or ""
        code = extract_code(content)

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
        )
