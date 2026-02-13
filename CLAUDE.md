# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

auto-leetcode — Python CLI tool that automatically solves LeetCode problems using AI (OpenAI-compatible and Claude-compatible APIs, with proxy/relay support).

## Build & Test Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/unit/test_runner.py -v

# Coverage
pytest tests/ --cov=auto_leetcode --cov-report=term-missing

# Lint & format
ruff check src/ tests/
black src/ tests/
isort src/ tests/

# Type check
mypy src/
```

## Usage

```bash
# Solve problems 1-100 with 3 retries each
auto-leetcode solve --start 1 --end 100 --retries 3

# Check progress
auto-leetcode status
```

Requires `.env` file with `LEETCODE_SESSION`, `CSRF_TOKEN`, `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`, `AI_PROVIDER`.

## Architecture

Core loop: fetch problem → AI generates Python solution → submit to LeetCode → record result → next.

- `runner.py` — orchestration loop, calls all other modules
- `leetcode/client.py` — LeetCode GraphQL API client (async, uses `httpx`). Builds a slug map on startup, then fetches problems and submits solutions
- `leetcode/submitter.py` — POST solution + poll for result via REST
- `ai/protocol.py` — `SolutionGenerator` Protocol. Two implementations: `OpenAIGenerator` (openai SDK) and `ClaudeGenerator` (anthropic SDK)
- `ai/prompt.py` — system prompt, user prompt builder, code extraction from AI responses. Previous failed attempts are fed back for self-correction
- `storage/json_repository.py` — JSONL-based result persistence. Tracks solved problems in memory for fast skip checks
- `storage/file_saver.py` — saves solution `.py` files to `solutions/` directory
- `config.py` — frozen dataclass `Config`, loaded from `.env` via `python-dotenv`
- `models/` — frozen dataclasses: `Problem`, `Solution`, `SubmissionResult`
- `errors.py` — exception hierarchy rooted at `AutoLeetCodeError`

All data models are frozen dataclasses (immutable). Lists are updated via `[*old, new]` spread, never `.append()`.
