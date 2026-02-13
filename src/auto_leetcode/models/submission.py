from dataclasses import dataclass
from enum import Enum

from auto_leetcode.models.solution import Solution


class SubmissionStatus(Enum):
    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT = "Time Limit Exceeded"
    MEMORY_LIMIT = "Memory Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILE_ERROR = "Compile Error"
    UNKNOWN = "Unknown"


@dataclass(frozen=True)
class SubmissionResult:
    problem_id: int
    status: SubmissionStatus
    runtime_ms: int | None
    memory_mb: float | None
    error_message: str | None
    solution: Solution
