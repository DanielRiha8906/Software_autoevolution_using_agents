import sys
from typing import Optional
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.workflow_query import DurationRange, TimestampRange
from ..services.workflow_statistics_service import WorkflowStatisticsService
from ..services.workflow_run_export_service import WorkflowRunExportService
from ..services.github_fetch_service import GitHubFetchService


def _prompt(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else (default or "")


def _choose(label: str, options: list, allow_blank: bool = False) -> Optional[str]:
    print(f"\n{label}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    if allow_blank:
        print("  0. (none)")
    while True:
        raw = input("Choice: ").strip()
        if allow_blank and raw in ("", "0"):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Invalid choice, try again.")


def _fmt_run(run: WorkflowRun) -> str:
    conclusion = run.conclusion.value if run.conclusion else "—"
    return (
        f"  id          : {run.id}\n"
        f"  workflow    : {run.workflow_name}\n"
        f"  branch      : {run.branch}\n"
        f"  status      : {run.status.value}\n"
        f"  conclusion  : {conclusion}\n"
        f"  run_number  : {run.run_number or '—'}\n"
        f"  commit_sha  : {run.commit_sha or '—'}\n"
        f"  created_at  : {run.created_at.isoformat()}\n"
        f"  updated_at  : {run.updated_at.isoformat() if run.updated_at else '—'}\n"
    )


def _fmt_attempt(attempt: WorkflowRunAttempt) -> str:
    conclusion = attempt.conclusion or "—"
    duration = f"{attempt.duration_seconds}s" if attempt.duration_seconds is not None else "—"
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status}\n"
        f"  conclusion      : {conclusion}\n"
        f"  created_at      : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds: {duration}\n"
    )


def _add_run(service: WorkflowRunService) -> None:
    tracker = WorkflowRunTracker(service)
    print("\n--- Add Workflow Run ---")
    name = _prompt("Workflow name")
    branch = _prompt("Branch")
    status_val = _choose("Status", [s.value for s in WorkflowStatus])
    conclusion_val = _choose("Conclusion (optional)", [c.value for c in WorkflowConclusion], allow_blank=True)
    run_number_raw = _prompt("Run number (leave blank to skip)", "")
    commit_sha = _prompt("Commit SHA (leave blank to skip)", "") or None

    run_number = int(run_number_raw) if run_number_raw else None
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None

    run = tracker.track(
        workflow_name=name,
        branch=branch,
        status=WorkflowStatus(status_val),
        conclusion=conclusion,
        run_number=run_number,
        commit_sha=commit_sha,
    )
    print(f"\nAdded run {run.id}")


def _list_runs(service: WorkflowRunService) -> None:
    runs = service.list_runs()
    if not runs:
        print("\nNo runs recorded.")
        return
    print(f"\n--- {len(runs)} run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _detail_run(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
    else:
        print(_fmt_run(run))


def _check_state(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
    else:
        print(f"\n--- State Check for {run.id} ---")
        print(f"  is_running()   : {run.is_running()}")
        print(f"  is_terminal()  : {run.is_terminal()}")
        print(f"  is_successful(): {run.is_successful()}")
        print(f"  is_failed()    : {run.is_failed()}")
        print(f"  is_cancelled() : {run.is_cancelled()}")


def _filter_menu(service: WorkflowRunService) -> None:
    filter_by = _choose("Filter by", ["branch", "status", "conclusion"])
    if filter_by == "branch":
        branch = _prompt("Branch name")
        runs = service.filter_by_branch(branch)
    elif filter_by == "status":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        runs = service.filter_by_status(WorkflowStatus(status_val))
    else:
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        runs = service.filter_by_conclusion(WorkflowConclusion(conclusion_val))

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _create_attempt(attempt_service: AttemptService) -> None:
    print("\n--- Create Workflow Attempt ---")
    run_id_raw = _prompt("Run ID")
    attempt_id_raw = _prompt("Attempt ID")
    attempt_number_raw = _prompt("Attempt number")
    status = _prompt("Status")
    conclusion = _prompt("Conclusion (leave blank for none)", "")
    duration_raw = _prompt("Duration in seconds (leave blank for none)", "")

    try:
        run_id = int(run_id_raw)
        attempt_id = int(attempt_id_raw)
        attempt_number = int(attempt_number_raw)
        duration = float(duration_raw) if duration_raw else None
        conclusion_val = conclusion if conclusion else None

        attempt = WorkflowRunAttempt(
            id=attempt_id,
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion_val,
            created_at=datetime.now(timezone.utc),
            duration_seconds=duration,
        )
        created_attempt = attempt_service.create_attempt(attempt)
        print(f"\nCreated attempt {created_attempt.attempt_number} for run {created_attempt.run_id}")
    except ValueError as e:
        print(f"\nError: {e}")


def _list_attempts(attempt_service: AttemptService) -> None:
    print("\n--- List Attempts ---")
    run_id_raw = _prompt("Run ID")
    try:
        run_id = int(run_id_raw)
        attempts = attempt_service.get_attempts_for_run(run_id)
        if not attempts:
            print(f"\nNo attempts found for run {run_id}.")
            return
        print(f"\n--- {len(attempts)} attempt(s) for run {run_id} ---")
        for attempt in attempts:
            print(_fmt_attempt(attempt))
    except ValueError as e:
        print(f"\nError: {e}")


def _query_runs(workflow_service: WorkflowRunService, attempt_service: AttemptService) -> None:
    print("\n--- Query Workflow Runs ---")
    print("Enter filter criteria (leave blank to skip):")

    min_duration_raw = _prompt("Minimum duration in seconds", "")
    max_duration_raw = _prompt("Maximum duration in seconds", "")
    created_after_raw = _prompt("Created after (ISO datetime)", "")
    created_before_raw = _prompt("Created before (ISO datetime)", "")
    has_attempts_raw = _prompt("Has attempts (true/false)", "")

    min_duration = float(min_duration_raw) if min_duration_raw else None
    max_duration = float(max_duration_raw) if max_duration_raw else None

    created_after = None
    if created_after_raw:
        try:
            created_after = datetime.fromisoformat(created_after_raw)
        except ValueError:
            print(f"\nError: Invalid datetime format for created_after: {created_after_raw}")
            return

    created_before = None
    if created_before_raw:
        try:
            created_before = datetime.fromisoformat(created_before_raw)
        except ValueError:
            print(f"\nError: Invalid datetime format for created_before: {created_before_raw}")
            return

    has_attempts = None
    if has_attempts_raw:
        if has_attempts_raw.lower() == "true":
            has_attempts = True
        elif has_attempts_raw.lower() == "false":
            has_attempts = False
        else:
            print("\nError: has_attempts must be 'true' or 'false'")
            return

    query = workflow_service.create_query(attempt_service)

    duration_range = None
    if min_duration is not None or max_duration is not None:
        duration_range = DurationRange(
            min_seconds=min_duration,
            max_seconds=max_duration
        )

    timestamp_range = None
    if created_after is not None or created_before is not None:
        timestamp_range = TimestampRange(
            before=created_before,
            after=created_after
        )

    try:
        result = query.query(
            duration_range=duration_range,
            timestamp_range=timestamp_range,
            has_attempts=has_attempts
        )
    except ValueError as e:
        print(f"\nError: {e}")
        return

    if not result:
        print("\nNo runs match the query criteria.")
        return

    print(f"\n--- {len(result)} matching run(s) ---")
    for run in result:
        print(_fmt_run(run))


def _fmt_statistics(stats) -> str:
    """Format WorkflowRunStatistics for display.

    Args:
        stats: A WorkflowRunStatistics object.

    Returns:
        Formatted string representation.
    """
    lines = ["--- Workflow Run Statistics ---"]

    lines.append("\nCount by Conclusion:")
    if stats.count_by_conclusion:
        for conclusion, count in sorted(stats.count_by_conclusion.items()):
            lines.append(f"  {conclusion}: {count}")
    else:
        lines.append("  (no data)")

    lines.append(f"\nDuration Statistics:")
    lines.append(f"  Average: {stats.average_duration_seconds:.2f}s")
    lines.append(f"  Min: {stats.min_duration_seconds:.2f}s" if stats.min_duration_seconds is not None else f"  Min: —")
    lines.append(f"  Max: {stats.max_duration_seconds:.2f}s" if stats.max_duration_seconds is not None else f"  Max: —")

    lines.append(f"\nAverage Attempts per Run: {stats.average_attempts_per_run:.2f}")

    if stats.per_status_breakdown:
        lines.append("\nDuration Breakdown by Status:")
        for status, avg_duration in sorted(stats.per_status_breakdown.items()):
            lines.append(f"  {status}: {avg_duration:.2f}s")
    else:
        lines.append("\nDuration Breakdown by Status:")
        lines.append("  (no data)")

    return "\n".join(lines)


def _view_statistics(workflow_service: WorkflowRunService, attempt_service: AttemptService) -> None:
    """Display aggregated workflow statistics."""
    stats_service = WorkflowStatisticsService()
    runs = workflow_service.list_runs()
    attempts = attempt_service.list_all_attempts()
    stats = stats_service.compute_statistics(runs, attempts)
    print("\n" + _fmt_statistics(stats))


def _export_runs(workflow_service: WorkflowRunService) -> None:
    """Export all workflow runs to a JSON file."""
    print("\n--- Export Workflow Runs ---")
    filepath = _prompt("Output file path")
    try:
        count = WorkflowRunExportService.export_to_file(workflow_service, filepath)
        print(f"\nExported {count} workflow run(s) to {filepath}")
    except Exception as e:
        print(f"\nError exporting: {e}")


def _import_runs(workflow_service: WorkflowRunService) -> None:
    """Import workflow runs from a JSON file."""
    print("\n--- Import Workflow Runs ---")
    filepath = _prompt("Input file path")
    try:
        imported, skips = WorkflowRunExportService.import_from_file(workflow_service, filepath)
        print(f"\nImported {imported} workflow run(s) from {filepath}")
        if skips:
            print(f"\n{len(skips)} entries skipped:")
            for reason in skips:
                print(f"  - {reason}")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except ValueError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError importing: {e}")


def _fetch_from_github(workflow_service: WorkflowRunService) -> None:
    """Fetch workflow runs from GitHub API."""
    print("\n--- Fetch from GitHub ---")
    owner = _prompt("Repository owner (username or org)")
    repo = _prompt("Repository name")
    workflow = _prompt("Workflow ID or filename (leave blank to fetch all)", "")
    workflow = workflow if workflow else None

    incremental_raw = _prompt("Incremental fetch only? (yes/no)", "no")
    incremental = incremental_raw.lower() in ("yes", "y", "true")

    try:
        fetch_service = GitHubFetchService()

        if incremental:
            # Get the latest run timestamp from stored runs
            all_runs = workflow_service.list_runs()
            latest_timestamp = None
            if all_runs:
                latest_timestamp = max(run.created_at for run in all_runs)
            runs = fetch_service.fetch_incremental(
                owner=owner,
                repo=repo,
                latest_run_timestamp=latest_timestamp,
                workflow=workflow,
            )
        else:
            runs = fetch_service.fetch_workflow_runs(
                owner=owner,
                repo=repo,
                workflow=workflow,
            )

        if not runs:
            print("\nNo workflow runs fetched from GitHub.")
            return

        # Add fetched runs to storage (skip duplicates)
        added_count = 0
        skipped_count = 0
        for run in runs:
            try:
                workflow_service.add_workflow_run(run)
                added_count += 1
            except ValueError:
                # Run already exists
                skipped_count += 1

        print(f"\nFetched {len(runs)} workflow run(s) from GitHub.")
        print(f"Added {added_count} new run(s) to storage.")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} run(s) (already exist).")

    except ValueError as e:
        print(f"\nError: {e}")
    except RuntimeError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError fetching from GitHub: {e}")


MENU = [
    ("Add workflow run", lambda ws, as_: _add_run(ws)),
    ("List all runs", lambda ws, as_: _list_runs(ws)),
    ("Get run detail", lambda ws, as_: _detail_run(ws)),
    ("Filter runs", lambda ws, as_: _filter_menu(ws)),
    ("Check run state", lambda ws, as_: _check_state(ws)),
    ("Query runs (advanced)", lambda ws, as_: _query_runs(ws, as_)),
    ("Create attempt", lambda ws, as_: _create_attempt(as_)),
    ("List attempts for run", lambda ws, as_: _list_attempts(as_)),
    ("View statistics", lambda ws, as_: _view_statistics(ws, as_)),
    ("Export workflow runs", lambda ws, as_: _export_runs(ws)),
    ("Import workflow runs", lambda ws, as_: _import_runs(ws)),
    ("Fetch from GitHub", lambda ws, as_: _fetch_from_github(ws)),
    ("Exit", None),
]


def run_interactive(workflow_service: WorkflowRunService, attempt_service: AttemptService) -> None:
    print("\nGitHub Workflow Tracker — Interactive Menu")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(MENU)):
            print("Invalid selection.")
            continue
        label, handler = MENU[int(raw) - 1]
        if handler is None:
            print("Goodbye.")
            sys.exit(0)
        try:
            handler(workflow_service, attempt_service)
        except KeyboardInterrupt:
            print()
