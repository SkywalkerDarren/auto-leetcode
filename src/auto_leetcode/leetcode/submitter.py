from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from auto_leetcode.errors import LeetCodeClientError, LeetCodeRateLimitError
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult, SubmissionStatus

logger = logging.getLogger(__name__)

STATUS_MAP: dict[int, SubmissionStatus] = {
    10: SubmissionStatus.ACCEPTED,
    11: SubmissionStatus.WRONG_ANSWER,
    12: SubmissionStatus.MEMORY_LIMIT,
    13: SubmissionStatus.COMPILE_ERROR,
    14: SubmissionStatus.RUNTIME_ERROR,
    15: SubmissionStatus.TIME_LIMIT,
}

POLL_INTERVAL = 2.0
MAX_POLL_ATTEMPTS = 30


async def submit_solution(
    http: httpx.AsyncClient,
    slug: str,
    solution: Solution,
) -> SubmissionResult:
    try:
        resp = await http.post(
            f"/problems/{slug}/submit/",
            json={
                "lang": solution.language,
                "question_id": str(solution.problem_id),
                "typed_code": solution.code,
            },
        )
    except httpx.HTTPError as e:
        raise LeetCodeClientError(f"Submit failed for problem #{solution.problem_id}: {e}") from e

    if resp.status_code == 429:
        raise LeetCodeRateLimitError("Rate limited during submission")
    if resp.status_code != 200:
        raise LeetCodeClientError(f"Submit returned status {resp.status_code}: {resp.text}")

    data: dict[str, Any] = resp.json()
    submission_id = data.get("submission_id")
    if not submission_id:
        raise LeetCodeClientError(f"No submission_id in response: {data}")

    return await _poll_result(http, submission_id, solution)


async def _poll_result(
    http: httpx.AsyncClient,
    submission_id: int,
    solution: Solution,
) -> SubmissionResult:
    for _ in range(MAX_POLL_ATTEMPTS):
        await asyncio.sleep(POLL_INTERVAL)

        try:
            resp = await http.get(f"/submissions/detail/{submission_id}/check/")
        except httpx.HTTPError as e:
            raise LeetCodeClientError(f"Poll failed for submission {submission_id}: {e}") from e

        if resp.status_code != 200:
            continue

        data: dict[str, Any] = resp.json()
        state = data.get("state")

        if state != "SUCCESS":
            continue

        status_code = data.get("status_code", -1)
        status = STATUS_MAP.get(status_code, SubmissionStatus.UNKNOWN)

        return SubmissionResult(
            problem_id=solution.problem_id,
            status=status,
            runtime_ms=_parse_int(data.get("status_runtime")),
            memory_mb=_parse_float(data.get("status_memory")),
            error_message=data.get("full_runtime_error") or data.get("compile_error"),
            solution=solution,
        )

    raise LeetCodeClientError(
        f"Submission {submission_id} did not complete after {MAX_POLL_ATTEMPTS} polls"
    )


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).replace(" ms", "").strip())
    except (ValueError, TypeError):
        return None


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(" MB", "").strip())
    except (ValueError, TypeError):
        return None
