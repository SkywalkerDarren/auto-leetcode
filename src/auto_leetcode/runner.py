from __future__ import annotations

import asyncio
import logging

from auto_leetcode.ai.claude_generator import ClaudeGenerator
from auto_leetcode.ai.openai_generator import OpenAIGenerator
from auto_leetcode.ai.protocol import SolutionGenerator
from auto_leetcode.config import Config
from auto_leetcode.errors import (
    AIGenerationError,
    LeetCodeClientError,
    LeetCodeRateLimitError,
)
from auto_leetcode.leetcode.client import LeetCodeClient
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult, SubmissionStatus
from auto_leetcode.storage.file_saver import FileSaver
from auto_leetcode.storage.json_repository import JsonRepository

logger = logging.getLogger(__name__)

RATE_LIMIT_BACKOFF_SECONDS = 60
CLOUDFLARE_MAX_RETRIES = 3


def create_generator(config: Config) -> SolutionGenerator:
    if config.ai_provider == "claude":
        return ClaudeGenerator(
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
            model=config.ai_model,
        )
    return OpenAIGenerator(
        api_key=config.ai_api_key,
        base_url=config.ai_base_url,
        model=config.ai_model,
    )


async def run(config: Config) -> None:
    async with LeetCodeClient(config.leetcode_session, config.csrf_token) as client:
        generator = create_generator(config)
        repository = JsonRepository(config.results_path)
        saver = FileSaver(config.solutions_dir)

        logger.info("Building problem slug map...")
        await client.build_slug_map()

        remote_solved: set[int] = set()
        if config.skip_solved:
            logger.info("Fetching solved problems from LeetCode...")
            remote_solved = await client.fetch_solved_ids()

        for problem_id in range(config.start_id, config.end_id + 1):
            await _solve_problem(
                client, generator, repository, saver, config, problem_id, remote_solved
            )


async def _solve_problem(
    client: LeetCodeClient,
    generator: SolutionGenerator,
    repository: JsonRepository,
    saver: FileSaver,
    config: Config,
    problem_id: int,
    remote_solved: set[int],
) -> None:
    if repository.is_solved(problem_id) or problem_id in remote_solved:
        logger.info("Problem #%d already solved, skipping", problem_id)
        return

    try:
        problem = await client.fetch_problem(problem_id)
    except LeetCodeRateLimitError:
        logger.warning("Rate limited fetching #%d, waiting %ds", problem_id, RATE_LIMIT_BACKOFF_SECONDS)
        await asyncio.sleep(RATE_LIMIT_BACKOFF_SECONDS)
        return
    except LeetCodeClientError as e:
        logger.error("Failed to fetch #%d: %s", problem_id, e)
        return

    if problem is None or problem.paid_only:
        logger.info("Problem #%d not available or paid-only, skipping", problem_id)
        return

    if not problem.code_snippet:
        logger.warning("Problem #%d has no Python3 snippet, skipping", problem_id)
        return

    previous_attempts: list[SubmissionResult] = []

    for attempt in range(1, config.max_retries + 1):
        try:
            solution = await generator.generate(problem, previous_attempts)
        except AIGenerationError as e:
            logger.error("AI generation failed for #%d attempt %d: %s", problem_id, attempt, e)
            break

        saver.save(solution)

        result = await _submit_with_retry(client, solution, problem_id)
        if result is None:
            break

        repository.save(result)

        if result.status == SubmissionStatus.ACCEPTED:
            logger.info(
                "Problem #%d ACCEPTED on attempt %d (runtime: %s ms)",
                problem_id,
                attempt,
                result.runtime_ms,
            )
            break

        previous_attempts = [*previous_attempts, result]
        logger.warning(
            "Problem #%d attempt %d: %s",
            problem_id,
            attempt,
            result.status.value,
        )
        await asyncio.sleep(config.retry_delay_seconds)
    else:
        logger.error(
            "Problem #%d failed after %d attempts, skipping",
            problem_id,
            config.max_retries,
        )

    await asyncio.sleep(config.submit_delay_seconds)


async def _submit_with_retry(
    client: LeetCodeClient,
    solution: Solution,
    problem_id: int,
) -> SubmissionResult | None:
    for submit_try in range(1, CLOUDFLARE_MAX_RETRIES + 1):
        try:
            return await client.submit(solution)
        except LeetCodeRateLimitError:
            logger.warning(
                "Rate limited/blocked submitting #%d (attempt %d/%d), waiting %ds",
                problem_id, submit_try, CLOUDFLARE_MAX_RETRIES,
                RATE_LIMIT_BACKOFF_SECONDS,
            )
            await asyncio.sleep(RATE_LIMIT_BACKOFF_SECONDS)
        except LeetCodeClientError as e:
            logger.error("Submit failed for #%d: %s", problem_id, e)
            return None
    logger.error("Submit gave up for #%d after %d retries", problem_id, CLOUDFLARE_MAX_RETRIES)
    return None
