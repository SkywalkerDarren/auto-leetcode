from __future__ import annotations

import asyncio
import logging
import sys

import click

from auto_leetcode.config import load_config
from auto_leetcode.errors import AutoLeetCodeError, ConfigError
from auto_leetcode.runner import run
from auto_leetcode.storage.json_repository import JsonRepository


@click.group()
def main() -> None:
    """auto-leetcode: solve LeetCode problems with AI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@main.command()
@click.option("--start", default=1, help="Starting problem ID")
@click.option("--end", default=3000, help="Ending problem ID")
@click.option("--retries", default=3, help="Max retries per problem")
@click.option("--skip-solved/--no-skip-solved", default=True, help="Skip already solved problems")
def solve(start: int, end: int, retries: int, skip_solved: bool) -> None:
    """Solve problems sequentially."""
    try:
        config = load_config(start_id=start, end_id=end, max_retries=retries, skip_solved=skip_solved)
    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    try:
        asyncio.run(run(config))
    except AutoLeetCodeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user.")


@main.command()
def status() -> None:
    """Show progress summary."""
    try:
        config = load_config()
    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    repo = JsonRepository(config.results_path)
    accepted = repo.find_all_accepted()
    total_solved = len({r.problem_id for r in accepted})
    click.echo(f"Solved: {total_solved} problems")
