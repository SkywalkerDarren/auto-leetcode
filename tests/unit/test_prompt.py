from auto_leetcode.ai.prompt import SYSTEM_PROMPT, build_user_prompt, extract_code
from auto_leetcode.models.problem import Problem
from auto_leetcode.models.solution import Solution
from auto_leetcode.models.submission import SubmissionResult, SubmissionStatus


def _make_problem(**kwargs: object) -> Problem:
    defaults = {
        "id": 1,
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "Easy",
        "description": "Given an array of integers nums...",
        "code_snippet": "class Solution:\n    def twoSum(self):",
        "paid_only": False,
    }
    defaults.update(kwargs)
    return Problem(**defaults)  # type: ignore[arg-type]


class TestBuildUserPrompt:
    def test_basic_prompt(self) -> None:
        problem = _make_problem()
        result = build_user_prompt(problem, [])
        assert "Two Sum" in result
        assert "Easy" in result
        assert "def twoSum" in result
        assert "Previous attempt" not in result

    def test_with_previous_attempts(self) -> None:
        problem = _make_problem()
        attempt = SubmissionResult(
            problem_id=1,
            status=SubmissionStatus.WRONG_ANSWER,
            runtime_ms=None,
            memory_mb=None,
            error_message="Expected [0,1] but got [1,0]",
            solution=Solution(
                problem_id=1,
                code="return [0, 0]",
                language="python3",
                model_used="gpt-4o",
                attempt=1,
            ),
        )
        result = build_user_prompt(problem, [attempt])
        assert "Wrong Answer" in result
        assert "Expected [0,1]" in result
        assert "Fix the issues" in result

    def test_system_prompt_not_empty(self) -> None:
        assert len(SYSTEM_PROMPT) > 0
        assert "Python" in SYSTEM_PROMPT


class TestExtractCode:
    def test_extracts_from_python_block(self) -> None:
        text = "Here's the solution:\n```python\ndef solve(): pass\n```"
        assert extract_code(text) == "def solve(): pass"

    def test_extracts_from_python3_block(self) -> None:
        text = "```python3\ndef solve(): pass\n```"
        assert extract_code(text) == "def solve(): pass"

    def test_extracts_from_bare_block(self) -> None:
        text = "```\ndef solve(): pass\n```"
        assert extract_code(text) == "def solve(): pass"

    def test_returns_raw_text_without_block(self) -> None:
        text = "def solve(): pass"
        assert extract_code(text) == "def solve(): pass"

    def test_empty_string(self) -> None:
        assert extract_code("") == ""
