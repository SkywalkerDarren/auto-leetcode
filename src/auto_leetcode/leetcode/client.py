import logging
from typing import Any, Self

import httpx

from auto_leetcode.errors import (
    LeetCodeAuthError,
    LeetCodeClientError,
    LeetCodeRateLimitError,
)
from auto_leetcode.leetcode.parser import extract_code_snippet, strip_html
from auto_leetcode.models.problem import Problem
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://leetcode.com/graphql"

PROBLEM_QUERY = """
query questionData($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        difficulty
        content
        isPaidOnly
        codeSnippets {
            langSlug
            code
        }
    }
}
"""

PROBLEM_LIST_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int) {
    problemsetQuestionList: questionList(
        categorySlug: $categorySlug
        limit: $limit
        skip: $skip
        filters: {}
    ) {
        total
        questions {
            questionFrontendId
            titleSlug
            isPaidOnly
        }
    }
}
"""


class LeetCodeClient:
    def __init__(self, session: str, csrf_token: str) -> None:
        self._http = httpx.AsyncClient(
            base_url="https://leetcode.com",
            headers={
                "Cookie": f"LEETCODE_SESSION={session}; csrftoken={csrf_token}",
                "X-CSRFToken": csrf_token,
                "Referer": "https://leetcode.com",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        self._slug_map: dict[int, str] = {}

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.aclose()

    async def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._http.post(
                "/graphql",
                json={"query": query, "variables": variables},
            )
        except httpx.HTTPError as e:
            raise LeetCodeClientError(f"GraphQL request failed: {e}") from e

        if resp.status_code in (401, 403):
            raise LeetCodeAuthError("LeetCode session expired or invalid")
        if resp.status_code == 429:
            raise LeetCodeRateLimitError("Rate limited by LeetCode")
        if resp.status_code != 200:
            raise LeetCodeClientError(f"Unexpected status {resp.status_code}: {resp.text}")

        data = resp.json()
        if "errors" in data:
            raise LeetCodeClientError(f"GraphQL errors: {data['errors']}")
        return data.get("data", {})

    async def build_slug_map(self) -> None:
        all_questions: list[dict[str, Any]] = []
        skip = 0
        limit = 100
        while True:
            data = await self._graphql(
                PROBLEM_LIST_QUERY,
                {"categorySlug": "", "limit": limit, "skip": skip},
            )
            question_list = data.get("problemsetQuestionList", {})
            questions = question_list.get("questions", [])
            if not questions:
                break
            all_questions.extend(questions)
            total = question_list.get("total", 0)
            skip += limit
            if skip >= total:
                break

        self._slug_map = {
            int(q["questionFrontendId"]): q["titleSlug"]
            for q in all_questions
        }
        logger.info("Built slug map with %d problems", len(self._slug_map))

    async def fetch_problem(self, problem_id: int) -> Problem | None:
        if not self._slug_map:
            raise LeetCodeClientError("Slug map not built. Call build_slug_map() first.")

        slug = self._slug_map.get(problem_id)
        if slug is None:
            logger.warning("Problem #%d not found in slug map", problem_id)
            return None

        data = await self._graphql(PROBLEM_QUERY, {"titleSlug": slug})
        q = data.get("question")
        if q is None:
            return None

        return Problem(
            id=int(q["questionFrontendId"]),
            title=q["title"],
            slug=q["titleSlug"],
            difficulty=q["difficulty"],
            description=strip_html(q.get("content", "") or ""),
            code_snippet=extract_code_snippet(q.get("codeSnippets", []) or []),
            paid_only=bool(q.get("isPaidOnly", False)),
        )

    async def submit(self, solution: Solution) -> SubmissionResult:
        from auto_leetcode.leetcode.submitter import submit_solution

        slug = self._slug_map.get(solution.problem_id)
        if slug is None:
            raise LeetCodeClientError(
                f"No slug found for problem #{solution.problem_id}"
            )
        return await submit_solution(self._http, slug, solution)
