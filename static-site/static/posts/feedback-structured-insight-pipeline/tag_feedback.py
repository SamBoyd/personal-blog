#!/usr/bin/env python3
"""Tag feedback rows in a CSV using Claude Code CLI.

Enriches each untagged row with theme, tags, sentiment, urgency, and
repeat_signal by invoking the `claude` CLI as a subprocess. Rows where
all five tagging fields are already populated are skipped.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import time
from pathlib import Path

import click

TAGGING_COLUMNS = ("theme", "tags", "sentiment", "urgency", "repeat_signal")

FEEDBACK_COLUMN = "feedback"

PROMPT_TEMPLATE = """\
Read the CSV file at {csv_path}.

For every row, populate the following columns using the value in the \
"{feedback_col}" column as the source text:

- theme: exactly one of ux, bug, feature-request, confusion, praise, other
- tags: up to 5 comma-separated lowercase tags that describe the feedback
- sentiment: exactly one of positive, neutral, negative
- urgency: exactly one of low, medium, high
- repeat_signal: exactly one of single, repeated (use "repeated" when \
similar feedback appears in other rows in the file, otherwise "single")

Rules:
- Skip any row where ALL five columns above already have a non-empty value.
- Do NOT modify any other columns or change existing values outside these five.
- Write the updated CSV back to {csv_path}, preserving the original column \
order and all existing data.
- Use the Edit tool to update the file in place.
"""


def _log(verbose: bool, message: str) -> None:
    if verbose:
        click.echo(message)


def _check_claude_cli() -> str:
    """Return the path to the claude binary, or exit with an error."""
    path = shutil.which("claude")
    if path is None:
        click.echo(
            "ERROR: 'claude' CLI not found on PATH. "
            "Install Claude Code first: https://docs.anthropic.com/en/docs/claude-code",
            err=True,
        )
        raise SystemExit(1)
    return path


def _validate_csv(csv_path: Path) -> list[str]:
    """Read the CSV header and return fieldnames. Exits on error."""
    if not csv_path.is_file():
        click.echo(f"ERROR: CSV file not found: {csv_path}", err=True)
        raise SystemExit(1)

    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        try:
            headers = next(reader)
        except StopIteration:
            click.echo(f"ERROR: CSV file is empty: {csv_path}", err=True)
            raise SystemExit(1)

    headers = [h.strip() for h in headers]

    if FEEDBACK_COLUMN not in headers:
        click.echo(
            f"ERROR: CSV is missing required column '{FEEDBACK_COLUMN}'.",
            err=True,
        )
        raise SystemExit(1)

    return headers


def _ensure_tagging_columns(csv_path: Path, headers: list[str]) -> list[str]:
    """Add missing tagging columns to the CSV. Returns final header list."""
    missing = [col for col in TAGGING_COLUMNS if col not in headers]
    if not missing:
        return headers

    click.echo(f"Adding missing tagging columns: {', '.join(missing)}")

    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    final_headers = headers + missing
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=final_headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in final_headers})

    return final_headers


def _count_untagged(csv_path: Path) -> tuple[int, int]:
    """Return (total_rows, already_tagged_rows)."""
    total = 0
    tagged = 0
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            if all((row.get(col) or "").strip() for col in TAGGING_COLUMNS):
                tagged += 1
    return total, tagged


def _build_prompt(csv_path: Path) -> str:
    return PROMPT_TEMPLATE.format(
        csv_path=csv_path.resolve(),
        feedback_col=FEEDBACK_COLUMN,
    )


@click.command()
@click.option(
    "--csv",
    "csv_path",
    required=True,
    type=click.Path(path_type=Path, dir_okay=False),
    help="Path to the feedback CSV to process.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print the prompt and command without executing.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Print diagnostics (command, timing, output).",
)
def cli(csv_path: Path, dry_run: bool, verbose: bool) -> None:
    """Tag feedback rows in a CSV using the Claude Code CLI."""

    # --- preflight ---
    claude_bin = _check_claude_cli()
    headers = _validate_csv(csv_path)
    headers = _ensure_tagging_columns(csv_path, headers)

    total_rows, already_tagged = _count_untagged(csv_path)
    click.echo(f"CSV: {csv_path.resolve()}")
    click.echo(f"Total rows: {total_rows}")
    click.echo(f"Already tagged: {already_tagged}")
    click.echo(f"Rows to tag: {total_rows - already_tagged}")

    if total_rows - already_tagged == 0:
        click.echo("Nothing to tag. All rows are already populated.")
        return

    # --- prompt ---
    prompt = _build_prompt(csv_path)

    cmd = [
        claude_bin,
        "-p",
        prompt,
        "--allowedTools",
        "Edit,Read",
    ]

    if dry_run:
        click.echo("\n--- DRY RUN ---")
        click.echo(f"Command: {' '.join(cmd[:1])} -p <prompt> {' '.join(cmd[3:])}")
        click.echo(f"\nPrompt:\n{prompt}")
        return

    # --- invoke claude ---
    _log(verbose, f"\nCommand: {' '.join(cmd[:1])} -p <prompt> {' '.join(cmd[3:])}")
    _log(verbose, "Invoking Claude Code...")

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start

    _log(verbose, f"Completed in {elapsed:.1f}s (exit code {result.returncode})")

    if verbose and result.stdout:
        click.echo(f"\n--- stdout ---\n{result.stdout}")
    if verbose and result.stderr:
        click.echo(f"\n--- stderr ---\n{result.stderr}")

    if result.returncode != 0:
        click.echo("ERROR: Claude Code exited with a non-zero status.", err=True)
        if result.stderr:
            click.echo(result.stderr, err=True)
        raise SystemExit(1)

    # --- summary ---
    total_after, tagged_after = _count_untagged(csv_path)
    click.echo(f"\nTagging complete.")
    click.echo(f"Rows tagged this run: {tagged_after - already_tagged}")
    click.echo(f"Total tagged: {tagged_after}/{total_after}")
    click.echo(f"Review the CSV at: {csv_path.resolve()}")


if __name__ == "__main__":
    cli()
