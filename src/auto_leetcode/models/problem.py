from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    id: int
    title: str
    slug: str
    difficulty: str
    description: str
    code_snippet: str
    paid_only: bool
