from dataclasses import dataclass


@dataclass(frozen=True)
class Solution:
    problem_id: int
    code: str
    language: str
    model_used: str
    attempt: int
    reasoning: str = ""
