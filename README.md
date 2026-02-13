# auto-leetcode

CLI tool that automatically solves all LeetCode problems using AI.

Supports OpenAI-compatible and Claude-compatible APIs (including proxy/relay services). For each problem, the AI generates a solution with reasoning, submits it to LeetCode, and retries on failure using error feedback for self-correction.

[中文文档](README.zh.md)

> If your company has absurd token usage quotas to hit, or you just want to benchmark how well a model handles algorithms (let's be honest, these problems are probably baked into the training data at this point lol), give this a spin.

## How It Works

```
Fetch problem → AI generates reasoning + code → Submit to LeetCode → Record result → Next
                                                      ↑                    |
                                                      |   Failed (≤ max retries)
                                                      └────────────────────┘
```

## Quick Start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
```

```env
# LeetCode auth (from browser cookies)
LEETCODE_SESSION=your_session_cookie
CSRF_TOKEN=your_csrf_token

# AI config
AI_PROVIDER=openai          # openai or claude
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o
```

**Getting LeetCode cookies:**
1. Log in to [leetcode.com](https://leetcode.com)
2. F12 → Application → Cookies → `https://leetcode.com`
3. Copy `LEETCODE_SESSION` and `csrftoken` values

### 3. Run

```bash
# Solve problems 1-100, up to 3 retries each
auto-leetcode solve --start 1 --end 100 --retries 3

# Check progress
auto-leetcode status
```

## Output

- `solutions/0001.py` — reasoning + code for each problem
- `results.jsonl` — submission log (problem ID, status, runtime, memory, model, timestamp)

Example solution file:

```python
# Problem #1
# Model: claude-opus-4-6
# Attempt: 1
#
# Approach:
# Use a hash map to store seen numbers. For each number,
# check if (target - num) exists in the map. O(n) time, O(n) space.

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
```

## Development

```bash
pip install -e ".[dev]"

pytest tests/ -v
pytest tests/ --cov=auto_leetcode --cov-report=term-missing

ruff check src/ tests/
black --check src/ tests/
mypy src/
```

## Project Structure

```
src/auto_leetcode/
├── cli.py              # CLI entry point (click)
├── config.py           # Config loader (.env)
├── runner.py           # Core orchestration loop
├── errors.py           # Exception hierarchy
├── models/             # Data models (frozen dataclasses)
├── leetcode/           # LeetCode GraphQL client + submission
├── ai/                 # AI generators (OpenAI / Claude) + prompts
└── storage/            # JSONL storage + file saver
```

## Notes

- LeetCode has rate limits — default 10s between problems, 5s between retries
- Paid-only problems and problems without a Python3 template are skipped
- Already-accepted problems are skipped automatically (resume-safe)
- Session cookies expire periodically and need to be refreshed
