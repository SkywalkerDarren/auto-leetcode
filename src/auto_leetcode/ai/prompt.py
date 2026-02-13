import re

from auto_leetcode.models.problem import Problem
from auto_leetcode.models.submission import SubmissionResult

SYSTEM_PROMPT = (
    "You are a competitive programming expert. "
    "Given a LeetCode problem, first explain your thought process and approach, "
    "then write a correct Python solution.\n\n"
    "Format your response as:\n"
    "## Approach\n"
    "<your reasoning: algorithm choice, time/space complexity analysis, key insights>\n\n"
    "## Solution\n"
    "```python\n"
    "<your code>\n"
    "```\n\n"
    "The code must complete the given function signature. "
    "Do not include the class definition if it's already in the starter code."
)


def build_user_prompt(
    problem: Problem,
    previous_attempts: list[SubmissionResult],
) -> str:
    parts = [
        f"Problem #{problem.id}: {problem.title}",
        f"Difficulty: {problem.difficulty}\n",
        problem.description,
        f"\nStarter code:\n```python\n{problem.code_snippet}\n```",
    ]

    for attempt in previous_attempts:
        error_info = ""
        if attempt.error_message:
            error_info = f"\nError: {attempt.error_message}"
        parts.append(
            f"\nPrevious attempt failed with: {attempt.status.value}"
            f"{error_info}"
            f"\nCode:\n```python\n{attempt.solution.code}\n```"
        )

    if previous_attempts:
        parts.append("\nFix the issues and provide a corrected solution.")

    return "\n".join(parts)


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python3?|py)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def extract_reasoning(text: str) -> str:
    match = re.search(r"##\s*Approach\s*\n(.*?)(?=##\s*Solution|```)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: everything before the first code block
    match = re.search(r"^(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""
