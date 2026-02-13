#!/usr/bin/env python3
"""Download feedback rows from Tally API and merge into a local CSV.

Behavior:
- Reads submissions directly from Tally using TALLY_API_KEY.
- Pulls completed submissions for one form.
- If output CSV does not exist, creates it from submissions.
- If output CSV exists, appends only rows whose Submission ID is new.
- If form adds fields, extends CSV schema to include them.
- If CSV has columns missing from current form responses, keeps them and prints a warning.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import traceback
from typing import Any, Dict, List, Sequence
from urllib.error import URLError
from urllib.parse import urlencode
import requests

import click

REQUIRED_COLUMNS = ("Submission ID", "Respondent ID", "Submitted at")
BASE_URL = "https://api.tally.so"


@dataclass
class MergeResult:
    output_path: Path
    submissions_fetched: int
    existing_row_count: int
    appended_count: int
    duplicate_count: int
    columns_added: List[str]
    stale_columns: List[str]
    dry_run: bool


class FeedbackDownloadError(Exception):
    """Expected operational error with user-actionable messaging."""


def _log(verbose: bool, message: str) -> None:
    if verbose:
        click.echo(message)


def _http_get_json(
    *,
    path: str,
    api_key: str,
    params: dict[str, Any] | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE_URL}{path}{query}"
    headers={"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)

        return json.loads(response.text)
    except requests.HTTPError as err:
        details = ""
        try:
            details = err.read().decode("utf-8")
        except Exception:
            details = ""

        if err.code in (401, 403):
            raise FeedbackDownloadError(
                "Tally API authentication failed (401/403). "
                "Verify TALLY_API_KEY has access to this form."
            ) from err
        if err.code == 404:
            raise FeedbackDownloadError(
                "Tally resource not found (404). "
                "Verify the form ID and submission IDs are correct."
            ) from err

        raise FeedbackDownloadError(
            f"Tally API request failed with HTTP {err.code}: {details or err.reason}"
        ) from err
    except URLError as err:
        raise FeedbackDownloadError(f"Failed to reach Tally API: {err.reason}") from err
    except json.JSONDecodeError as err:
        raise FeedbackDownloadError(f"Invalid JSON from Tally API: {err}") from err


def _question_title_from_question(question: dict[str, Any]) -> str:
    title = question.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    fields = question.get("fields")
    if isinstance(fields, list):
        for field in fields:
            if not isinstance(field, dict):
                continue
            field_title = field.get("title")
            if isinstance(field_title, str) and field_title.strip():
                return field_title.strip()

    return ""


def _list_submissions(
    *,
    form_id: str,
    api_key: str,
    page_size: int,
    timeout_seconds: int,
    verbose: bool,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    submissions: list[dict[str, Any]] = []
    question_titles: dict[str, str] = {}
    page = 1

    while True:
        payload = _http_get_json(
            path=f"/forms/{form_id}/submissions",
            api_key=api_key,
            params={"page": page, "limit": page_size, "filter": "completed"},
            timeout_seconds=timeout_seconds,
        )

        batch = payload.get("submissions")
        if not isinstance(batch, list):
            raise FeedbackDownloadError(
                "Unexpected Tally list response: missing 'submissions' array."
            )

        questions = payload.get("questions")
        if isinstance(questions, list):
            for question in questions:
                if not isinstance(question, dict):
                    continue
                question_id = _normalize_value(question.get("id"))
                if question_id == "" or question_id in question_titles:
                    continue
                title = _question_title_from_question(question)
                if title:
                    question_titles[question_id] = title

        # Enforce completed-only behavior even if API filter semantics change.
        completed_batch = [s for s in batch if _is_completed_submission(s)]
        submissions.extend(completed_batch)

        _log(
            verbose,
            f"Fetched page {page}: {len(batch)} submissions ({len(completed_batch)} completed).",
        )

        if not payload.get("hasMore"):
            break

        page += 1

    return submissions, question_titles


def _get_submission(
    *,
    form_id: str,
    submission_id: str,
    api_key: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    payload = _http_get_json(
        path=f"/forms/{form_id}/submissions/{submission_id}",
        api_key=api_key,
        params=None,
        timeout_seconds=timeout_seconds,
    )

    submission = payload.get("submission")
    if not isinstance(submission, dict):
        raise FeedbackDownloadError(
            "Unexpected Tally submission response: missing 'submission' object."
        )
    return submission


def _is_completed_submission(submission: dict[str, Any]) -> bool:
    if submission.get("isCompleted") is True:
        return True

    status = submission.get("status")
    if isinstance(status, str) and status.strip().upper() == "COMPLETED":
        return True

    return False


def _to_utc_timestamp(value: Any) -> str:
    if not isinstance(value, str) or value.strip() == "":
        return ""

    raw = value.strip()
    iso = raw[:-1] + "+00:00" if raw.endswith("Z") else raw

    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _normalize_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (str, int, float)):
        return str(value).strip()

    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            return ", ".join(str(item).strip() for item in value if str(item).strip())
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))

    return str(value).strip()


def _column_name_for_response(
    response: dict[str, Any], index: int, question_titles: dict[str, str]
) -> str:
    question_id = _normalize_value(response.get("questionId"))
    if question_id and question_id in question_titles:
        return question_titles[question_id]

    label = response.get("label")
    if isinstance(label, str) and label.strip():
        return label.strip()

    key = response.get("key")
    if isinstance(key, str) and key.strip():
        return key.strip()

    return f"field_{index}"


def _row_from_submission(
    submission: dict[str, Any],
    question_titles: dict[str, str],
) -> dict[str, str]:
    row: dict[str, str] = {
        "Submission ID": _normalize_value(submission.get("id")),
        "Respondent ID": _normalize_value(submission.get("respondentId")),
        "Submitted at": _to_utc_timestamp(submission.get("createdAt")),
    }

    responses = submission.get("responses")
    if not isinstance(responses, list):
        return row

    for idx, response in enumerate(responses, start=1):
        if not isinstance(response, dict):
            continue

        column_name = _column_name_for_response(response, idx, question_titles)
        raw_answer = response.get("answer")
        if isinstance(raw_answer, dict):
            if column_name in raw_answer:
                raw_answer = raw_answer.get(column_name)
            else:
                lowered = {str(k).strip().lower(): v for k, v in raw_answer.items()}
                maybe = lowered.get(column_name.strip().lower())
                if maybe is not None:
                    raw_answer = maybe
        value = _normalize_value(
            raw_answer if raw_answer is not None else response.get("value")
        )
        row[column_name] = value

    return row


def _normalize_submissions(
    submissions: list[dict[str, Any]],
    question_titles: dict[str, str],
    *,
    form_id: str,
    api_key: str,
    timeout_seconds: int,
    verbose: bool,
) -> tuple[list[str], list[dict[str, str]]]:
    headers: list[str] = list(REQUIRED_COLUMNS)
    seen_headers = set(headers)
    rows: list[dict[str, str]] = []

    for submission in submissions:
        submission_id = _normalize_value(submission.get("id"))
        if submission_id == "":
            continue

        current = submission
        responses = current.get("responses")
        if not isinstance(responses, list) or len(responses) == 0:
            _log(verbose, f"Hydrating submission {submission_id} for full response payload.")
            current = _get_submission(
                form_id=form_id,
                submission_id=submission_id,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
            )

        row = _row_from_submission(current, question_titles)

        if not any(value != "" for value in row.values()):
            continue

        for column in row.keys():
            if column and column not in seen_headers:
                headers.append(column)
                seen_headers.add(column)

        rows.append(row)

    missing_required = [col for col in REQUIRED_COLUMNS if col not in headers]
    if missing_required:
        missing = ", ".join(missing_required)
        raise FeedbackDownloadError(
            f"Normalized submission data missing required columns: {missing}."
        )

    return headers, rows


def _read_existing_csv(path: Path) -> tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        return [], []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]

    return fieldnames, rows


def _ordered_union(primary: Sequence[str], secondary: Sequence[str]) -> List[str]:
    merged: List[str] = []
    seen = set()

    for item in list(primary) + list(secondary):
        if item and item not in seen:
            merged.append(item)
            seen.add(item)

    return merged


def _normalize_row_for_headers(row: Dict[str, str], headers: Sequence[str]) -> Dict[str, str]:
    return {h: row.get(h, "") for h in headers}


def _write_csv(path: Path, headers: Sequence[str], rows: Sequence[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_normalize_row_for_headers(row, headers))


def merge_feedback(
    form_id: str,
    output_csv: Path,
    api_key: str,
    dry_run: bool,
    verbose: bool,
    page_size: int,
    timeout_seconds: int,
) -> MergeResult:
    submissions, question_titles = _list_submissions(
        form_id=form_id,
        api_key=api_key,
        page_size=page_size,
        timeout_seconds=timeout_seconds,
        verbose=verbose,
    )

    source_headers, source_rows = _normalize_submissions(
        submissions,
        question_titles,
        form_id=form_id,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        verbose=verbose,
    )
    existing_headers, existing_rows = _read_existing_csv(output_csv)

    if existing_headers and "Submission ID" not in existing_headers:
        raise FeedbackDownloadError(
            f"Existing CSV at {output_csv} is missing 'Submission ID'. "
            "Cannot deduplicate safely. Add the column or start with a clean file."
        )

    existing_ids = {
        (row.get("Submission ID") or "").strip()
        for row in existing_rows
        if (row.get("Submission ID") or "").strip()
    }

    rows_to_append: List[Dict[str, str]] = []
    duplicate_count = 0

    for row in source_rows:
        submission_id = (row.get("Submission ID") or "").strip()
        if submission_id == "":
            continue

        if submission_id in existing_ids:
            duplicate_count += 1
            continue

        rows_to_append.append(row)
        existing_ids.add(submission_id)

    if not existing_headers:
        final_headers = list(source_headers)
        columns_added = list(source_headers)
        stale_columns: List[str] = []
    else:
        final_headers = _ordered_union(existing_headers, source_headers)
        columns_added = [h for h in source_headers if h not in existing_headers]
        stale_columns = [h for h in existing_headers if h not in source_headers]

    final_rows = [
        _normalize_row_for_headers(row, final_headers)
        for row in existing_rows + rows_to_append
    ]

    if not dry_run:
        _write_csv(output_csv, final_headers, final_rows)

    return MergeResult(
        output_path=output_csv,
        submissions_fetched=len(source_rows),
        existing_row_count=len(existing_rows),
        appended_count=len(rows_to_append),
        duplicate_count=duplicate_count,
        columns_added=columns_added,
        stale_columns=stale_columns,
        dry_run=dry_run,
    )


@click.command()
@click.option(
    "--form-id",
    envvar="TALLY_FORM_ID",
    required=True,
    help="Tally form ID containing feedback submissions.",
)
@click.option(
    "--api-key",
    envvar="TALLY_API_KEY",
    required=True,
    help="Tally API key with access to the target form.",
)
@click.option(
    "--output-csv",
    default="feedback.csv",
    show_default=True,
    type=click.Path(path_type=Path, dir_okay=False),
    help="Output CSV path to create/update.",
)
@click.option(
    "--page-size",
    default=100,
    show_default=True,
    type=click.IntRange(min=1, max=100),
    help="Tally submissions to fetch per page.",
)
@click.option(
    "--timeout-seconds",
    default=30,
    show_default=True,
    type=click.IntRange(min=1),
    help="HTTP timeout for each Tally API request.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate access and show changes without writing output CSV.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Print additional diagnostics.",
)
def cli(
    form_id: str,
    api_key: str,
    output_csv: Path,
    page_size: int,
    timeout_seconds: int,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Download feedback from Tally API into a deduplicated local CSV."""
    try:
        result = merge_feedback(
            form_id=form_id,
            output_csv=output_csv,
            api_key=api_key,
            dry_run=dry_run,
            verbose=verbose,
            page_size=page_size,
            timeout_seconds=timeout_seconds,
        )
    except FeedbackDownloadError as err:
        click.echo(f"ERROR: {err}", err=True)
        raise SystemExit(1)
    except Exception as err:  # pragma: no cover - defensive guard
        click.echo(traceback.format_exc())
        click.echo(f"ERROR: Unexpected failure: {err}", err=True)
        raise SystemExit(1)

    mode = "DRY RUN" if result.dry_run else "UPDATED"
    click.echo(f"[{mode}] CSV path: {result.output_path}")
    click.echo(f"Submissions fetched: {result.submissions_fetched}")
    click.echo(f"Existing CSV rows: {result.existing_row_count}")
    click.echo(f"New rows appended: {result.appended_count}")
    click.echo(f"Duplicate rows skipped (Submission ID): {result.duplicate_count}")

    if result.columns_added:
        click.echo(f"Columns added to CSV schema: {', '.join(result.columns_added)}")
    else:
        click.echo("Columns added to CSV schema: none")

    if result.stale_columns:
        click.echo(
            "WARNING: Columns present in CSV but missing from current submissions were kept: "
            f"{', '.join(result.stale_columns)}"
        )
        click.echo("WARNING: Remove stale columns manually if you want to prune schema.")


if __name__ == "__main__":
    cli()
