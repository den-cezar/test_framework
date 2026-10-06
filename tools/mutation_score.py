"""
Turn mutmut's CI stats into a mutation score, write it to the GitHub job summary and enforce a minimum.

Usage: python -m tools.mutation_score --min-score 80
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

STATS_FILE = Path("mutants/mutmut-cicd-stats.json")


def mutation_score(stats: dict[str, int]) -> float:
    """
    Percentage of mutants detected by the tests. Timeouts count as detected; skipped mutants are excluded.

    :param stats: Mandatory, mutmut CI stats.
    :return: Score in percent.
    """
    detected = stats["killed"] + stats["timeout"]
    considered = stats["total"] - stats["skipped"]
    return 100.0 * detected / considered if considered else 100.0


def render(stats: dict[str, int], score: float, min_score: float) -> str:
    """
    Render the score as Markdown.

    :param stats: Mandatory, mutmut CI stats.
    :param score: Mandatory, Computed score.
    :param min_score: Mandatory, Required minimum.
    :return: Markdown text.
    """
    status = "PASSED" if score >= min_score else "FAILED"
    return "\n".join(
        [
            f"### Mutation testing (core/): {status}",
            "",
            f"Score **{score:.1f}%** (minimum {min_score:.0f}%)",
            "",
            "| Killed | Survived | No tests | Timeout | Suspicious | Total |",
            "|---|---|---|---|---|---|",
            f"| {stats['killed']} | {stats['survived']} | {stats['no_tests']} | {stats['timeout']} "
            f"| {stats['suspicious']} | {stats['total']} |",
            "",
            "Survivors are code changes no test noticed. Inspect them with `poetry run mutmut browse`.",
            "",
        ]
    )


def main() -> int:
    """
    Entry point.

    :return: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-score", type=float, default=0.0)
    args = parser.parse_args()

    stats = json.loads(STATS_FILE.read_text(encoding="utf-8"))
    score = mutation_score(stats)
    markdown = render(stats, score, args.min_score)
    print(markdown)
    if summary_path := os.getenv("GITHUB_STEP_SUMMARY"):
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            summary_file.write(markdown)
    return 0 if score >= args.min_score else 1


if __name__ == "__main__":
    sys.exit(main())
