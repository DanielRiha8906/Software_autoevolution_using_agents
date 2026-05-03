import sys
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.attempt_service import AttemptService

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.statistics_service import StatisticsService
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
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status}\n"
        f"  conclusion      : {conclusion}\n"
        f"  created_at      : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds: {attempt.duration_seconds}\n"
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


def _filter_menu(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    filter_by = _choose("Filter by", ["branch", "status", "conclusion", "duration", "timestamp", "attempts"])
    if filter_by == "branch":
        branch = _prompt("Branch name")
        runs = service.filter_by_branch(branch)
    elif filter_by == "status":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        runs = service.filter_by_status(WorkflowStatus(status_val))
    elif filter_by == "conclusion":
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        runs = service.filter_by_conclusion(WorkflowConclusion(conclusion_val))
    elif filter_by == "duration":
        min_dur = _prompt("Min duration in seconds (leave blank for none)", "")
        max_dur = _prompt("Max duration in seconds (leave blank for none)", "")
        min_val = float(min_dur) if min_dur else None
        max_val = float(max_dur) if max_dur else None
        runs = service.filter_by_duration_range(min_val, max_val)
    elif filter_by == "timestamp":
        ts_type = _choose("Timestamp filter", ["created_before", "created_after", "updated_before", "updated_after"])
        ts_str = _prompt("Enter timestamp (ISO format, e.g., 2026-05-03T12:00:00)")
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            print("Invalid timestamp format.")
            return
        if ts_type == "created_before":
            runs = service.filter_by_created_before(ts)
        elif ts_type == "created_after":
            runs = service.filter_by_created_after(ts)
        elif ts_type == "updated_before":
            runs = service.filter_by_updated_before(ts)
        else:
            runs = service.filter_by_updated_after(ts)
    else:  # attempts
        attempt_type = _choose("Attempt filter", ["with_attempts", "without_attempts"])
        if attempt_type == "with_attempts":
            runs = service.filter_with_attempts(attempt_service)
        else:
            runs = service.filter_without_attempts(attempt_service)

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _check_state(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return

    print(f"\n--- Run State: {run_id} ---")
    print(f"  is_terminal   : {run.is_terminal()}")
    print(f"  is_running    : {run.is_running()}")
    print(f"  is_successful : {run.is_successful()}")
    print(f"  is_failed     : {run.is_failed()}")
    print(f"  is_cancelled  : {run.is_cancelled()}")


def _add_attempt(attempt_service: AttemptService) -> None:
    print("\n--- Add Workflow Attempt ---")
    run_id_raw = _prompt("Run ID")
    attempt_number_raw = _prompt("Attempt number")
    status = _prompt("Status")
    conclusion = _prompt("Conclusion (leave blank to skip)", "") or None
    duration_raw = _prompt("Duration in seconds (leave blank for 0.0)", "0.0")

    try:
        run_id = int(run_id_raw)
        attempt_number = int(attempt_number_raw)
        duration = float(duration_raw)
    except ValueError as e:
        print(f"Invalid input: {e}")
        return

    attempt = WorkflowRunAttempt(
        id=0,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration,
    )

    try:
        attempt_service.add_workflow_attempt(attempt)
        print(f"\nAdded attempt {attempt_number} for run {run_id}")
    except ValueError as e:
        print(f"Error: {e}")


def _list_attempts(attempt_service: AttemptService) -> None:
    attempts = attempt_service.list_attempts()
    if not attempts:
        print("\nNo attempts recorded.")
        return
    print(f"\n--- {len(attempts)} attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _get_attempts_by_run(attempt_service: AttemptService) -> None:
    run_id_raw = _prompt("\nEnter run ID")
    try:
        run_id = int(run_id_raw)
    except ValueError:
        print("Invalid run ID.")
        return
    attempts = attempt_service.get_attempts_by_run_id(run_id)
    if not attempts:
        print(f"\nNo attempts found for run {run_id}.")
        return
    print(f"\n--- {len(attempts)} attempt(s) for run {run_id} ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _statistics(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    """Display workflow statistics and report."""
    stats_service = StatisticsService(service, attempt_service)
    report = stats_service.compute_statistics()
    print("\n--- Workflow Statistics Report ---")
    print(f"Total Runs: {report.total_runs}")
    print(f"\nConclusions Count:")
    if report.conclusions_count:
        for conclusion, count in sorted(report.conclusions_count.items()):
            print(f"  {conclusion}: {count}")
    else:
        print("  (no conclusions recorded)")
    print(f"\nDuration Statistics (seconds):")
    print(f"  Average: {report.avg_duration_seconds:.2f}")
    min_val = f"{report.min_duration_seconds:.2f}" if report.min_duration_seconds is not None else "—"
    max_val = f"{report.max_duration_seconds:.2f}" if report.max_duration_seconds is not None else "—"
    print(f"  Minimum: {min_val}")
    print(f"  Maximum: {max_val}")
    print(f"\nAverage Attempts per Run: {report.avg_attempts_per_run:.2f}")


def _export_runs(service: WorkflowRunService) -> None:
    """Export all runs to a JSON file."""
    print("\n--- Export Workflow Runs ---")
    filepath = _prompt("Enter output file path")
    if not filepath:
        print("Export cancelled.")
        return
    try:
        count = service.export_runs(filepath)
        print(f"\nSuccessfully exported {count} runs to {filepath}")
    except Exception as e:
        print(f"Error during export: {e}")


def _import_runs(service: WorkflowRunService) -> None:
    """Import runs from a JSON file."""
    print("\n--- Import Workflow Runs ---")
    filepath = _prompt("Enter input file path")
    if not filepath:
        print("Import cancelled.")
        return
    skip_dup = _choose("Handle duplicates", ["fail on duplicate", "skip duplicate"], allow_blank=False)
    skip_duplicates = skip_dup == "skip duplicate"
    try:
        count, errors = service.import_runs(filepath, skip_duplicates=skip_duplicates)
        print(f"\nSuccessfully imported {count} runs from {filepath}")
        if errors:
            print(f"Warnings ({len(errors)} items):")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")


def _fetch_from_github(service: WorkflowRunService) -> None:
    """Fetch workflow runs from GitHub and import them."""
    print("\n--- Fetch from GitHub ---")
    owner = _prompt("GitHub repository owner")
    repo = _prompt("GitHub repository name")
    skip_dup = _choose("Handle duplicates", ["fail on duplicate", "skip duplicate"], allow_blank=False)
    skip_duplicates = skip_dup == "skip duplicate"

    try:
        github_service = GitHubFetchService()
        runs = github_service.fetch_workflow_runs(owner=owner, repo=repo)

        imported_count = 0
        skipped_count = 0
        errors = []

        for run in runs:
            if any(r.id == run.id for r in service.list_runs()):
                if skip_duplicates:
                    skipped_count += 1
                    continue
                else:
                    errors.append(f"Run {run.id} already exists")
                    continue

            try:
                service.add_workflow_run(run)
                imported_count += 1
            except ValueError as e:
                errors.append(str(e))

        print(f"\nSuccessfully imported {imported_count} runs from GitHub ({skipped_count} duplicates skipped)")
        if errors:
            print(f"Warnings ({len(errors)} items):")
            for error in errors[:5]:
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")

    except ValueError as e:
        print(f"Error: {e}")


MENU = [
    ("Add workflow run", lambda s, a: _add_run(s)),
    ("List all runs", lambda s, a: _list_runs(s)),
    ("Get run detail", lambda s, a: _detail_run(s)),
    ("Filter runs", lambda s, a: _filter_menu(s, a)),
    ("Check run state", lambda s, a: _check_state(s)),
    ("Add workflow attempt", lambda s, a: _add_attempt(a)),
    ("List all attempts", lambda s, a: _list_attempts(a)),
    ("Get attempts for run", lambda s, a: _get_attempts_by_run(a)),
    ("View statistics", lambda s, a: _statistics(s, a)),
    ("Export runs to JSON", lambda s, a: _export_runs(s)),
    ("Import runs from JSON", lambda s, a: _import_runs(s)),
    ("Fetch from GitHub", lambda s, a: _fetch_from_github(s)),
    ("Exit", None),
]


def run_interactive(service: WorkflowRunService, attempt_service: AttemptService) -> None:
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
            handler(service, attempt_service)
        except KeyboardInterrupt:
            print()
