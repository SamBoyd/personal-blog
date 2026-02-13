#!/usr/bin/env python3
"""Download feedback rows from Google Sheets and merge into a local CSV.

Behavior:
- Uses service-account auth via GOOGLE_APPLICATION_CREDENTIALS.
- Reads one worksheet tab from a spreadsheet.
- If output CSV does not exist, creates it from sheet rows.
- If output CSV exists, appends only rows whose Submission ID is new.
- If sheet adds columns, extends CSV schema to include them.
- If CSV has columns missing from sheet, keeps them and prints a warning.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import click
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

REQUIRED_COLUMNS = ("Submission ID", "Respondent ID", "Submitted at")
SHEETS_READ_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


@dataclass
class MergeResult:
    output_path: Path
    sheet_row_count: int
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


def _load_sheet_values(
    spreadsheet_id: str,
    worksheet: str,
    credentials_path: Path,
    verbose: bool,
) -> List[List[str]]:
    if not credentials_path.exists():
        raise FeedbackDownloadError(
            f"Credentials file not found: {credentials_path}. "
            "Set GOOGLE_APPLICATION_CREDENTIALS to a valid service-account JSON file."
        )

    _log(verbose, f"Using credentials: {credentials_path}")
    creds = Credentials.from_service_account_file(
        str(credentials_path), scopes=[SHEETS_READ_SCOPE]
    )

    try:
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=worksheet)
            .execute()
        )
    except HttpError as err:
        raise FeedbackDownloadError(
            "Google Sheets API request failed. Check spreadsheet ID, worksheet name, "
            "and that the service account has access to the sheet. "
            f"API error: {err}"
        ) from err
    except Exception as err:  # pragma: no cover - defensive guard
        raise FeedbackDownloadError(f"Failed to read Google Sheet: {err}") from err

    values = response.get("values", [])
    if not values:
        raise FeedbackDownloadError(
            "The selected worksheet is empty. Expected a header row plus feedback rows."
        )

    return values


def _normalize_sheet_rows(values: List[List[str]]) -> tuple[List[str], List[Dict[str, str]]]:
    headers = [h.strip() for h in values[0]]
    if not headers or all(h == "" for h in headers):
        raise FeedbackDownloadError("Header row is empty in the selected worksheet.")

    missing_required = [col for col in REQUIRED_COLUMNS if col not in headers]
    if missing_required:
        missing = ", ".join(missing_required)
        raise FeedbackDownloadError(
            f"Worksheet missing required Tally columns: {missing}. "
            "Expected at least Submission ID, Respondent ID, and Submitted at."
        )

    rows: List[Dict[str, str]] = []
    for raw in values[1:]:
        row = {
            header: (raw[idx].strip() if idx < len(raw) else "")
            for idx, header in enumerate(headers)
        }

        # Skip fully empty rows to avoid meaningless appends.
        if any(value != "" for value in row.values()):
            rows.append(row)

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
    spreadsheet_id: str,
    worksheet: str,
    output_csv: Path,
    credentials_path: Path,
    dry_run: bool,
    verbose: bool,
) -> MergeResult:
    values = _load_sheet_values(
        spreadsheet_id=spreadsheet_id,
        worksheet=worksheet,
        credentials_path=credentials_path,
        verbose=verbose,
    )

    sheet_headers, sheet_rows = _normalize_sheet_rows(values)
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

    for row in sheet_rows:
        submission_id = (row.get("Submission ID") or "").strip()
        if submission_id == "":
            # Invalid source row; skip silently but keep behavior deterministic.
            continue

        if submission_id in existing_ids:
            duplicate_count += 1
            continue

        rows_to_append.append(row)
        existing_ids.add(submission_id)

    if not existing_headers:
        final_headers = list(sheet_headers)
        columns_added = list(sheet_headers)
        stale_columns: List[str] = []
    else:
        final_headers = _ordered_union(existing_headers, sheet_headers)
        columns_added = [h for h in sheet_headers if h not in existing_headers]
        stale_columns = [h for h in existing_headers if h not in sheet_headers]

    final_rows = [
        _normalize_row_for_headers(row, final_headers)
        for row in existing_rows + rows_to_append
    ]

    if not dry_run:
        _write_csv(output_csv, final_headers, final_rows)

    return MergeResult(
        output_path=output_csv,
        sheet_row_count=len(sheet_rows),
        existing_row_count=len(existing_rows),
        appended_count=len(rows_to_append),
        duplicate_count=duplicate_count,
        columns_added=columns_added,
        stale_columns=stale_columns,
        dry_run=dry_run,
    )


@click.command()
@click.option(
    "--spreadsheet-id",
    envvar="GOOGLE_SHEETS_SPREADSHEET_ID",
    required=True,
    help="Google Spreadsheet ID containing feedback responses.",
)
@click.option(
    "--worksheet",
    envvar="GOOGLE_SHEETS_WORKSHEET",
    default="Sheet1",
    show_default=True,
    help="Worksheet/tab name to read (e.g. 'Form Responses 1').",
)
@click.option(
    "--output-csv",
    default="feedback.csv",
    show_default=True,
    type=click.Path(path_type=Path, dir_okay=False),
    help="Output CSV path to create/update.",
)
@click.option(
    "--credentials-path",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
    required=True,
    type=click.Path(exists=False, path_type=Path, dir_okay=False),
    help="Path to Google service-account JSON credentials.",
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
    spreadsheet_id: str,
    worksheet: str,
    output_csv: Path,
    credentials_path: Path,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Download feedback from Google Sheets into a deduplicated local CSV."""
    try:
        result = merge_feedback(
            spreadsheet_id=spreadsheet_id,
            worksheet=worksheet,
            output_csv=output_csv,
            credentials_path=credentials_path,
            dry_run=dry_run,
            verbose=verbose,
        )
    except FeedbackDownloadError as err:
        click.echo(f"ERROR: {err}", err=True)
        raise SystemExit(1)
    except Exception as err:  # pragma: no cover - defensive guard
        click.echo(f"ERROR: Unexpected failure: {err}", err=True)
        raise SystemExit(1)

    mode = "DRY RUN" if result.dry_run else "UPDATED"
    click.echo(f"[{mode}] CSV path: {result.output_path}")
    click.echo(f"Rows fetched from sheet: {result.sheet_row_count}")
    click.echo(f"Existing CSV rows: {result.existing_row_count}")
    click.echo(f"New rows appended: {result.appended_count}")
    click.echo(f"Duplicate rows skipped (Submission ID): {result.duplicate_count}")

    if result.columns_added:
        click.echo(f"Columns added to CSV schema: {', '.join(result.columns_added)}")
    else:
        click.echo("Columns added to CSV schema: none")

    if result.stale_columns:
        click.echo(
            "WARNING: Columns present in CSV but missing from sheet were kept: "
            f"{', '.join(result.stale_columns)}"
        )
        click.echo("WARNING: Remove stale columns manually if you want to prune schema.")


if __name__ == "__main__":
    cli()
