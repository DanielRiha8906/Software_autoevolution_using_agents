import sys
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_attempt_status import WorkflowAttemptStatus
from ..models.workflow_attempt_conclusion import WorkflowAttemptConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.attempt_service import AttemptService
from ..services.statistics_service import StatisticsService
from .workflow_cli import _parse_iso8601


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
        f"  duration_seconds : {run.duration_seconds}\n"
    )


def _fmt_attempt(attempt) -> str:
    """Format a single attempt for display."""
    conclusion = attempt.conclusion.value if attempt.conclusion else "—"
    return (
        f"  id               : {attempt.id}\n"
        f"  attempt_number   : {attempt.attempt_number}\n"
        f"  status           : {attempt.status.value}\n"
        f"  conclusion       : {conclusion}\n"
        f"  created_at       : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds : {attempt.duration_seconds or '—'}\n"
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

    # Prompt for duration with validation
    while True:
        duration_raw = _prompt("Duration in seconds (leave blank for 0)", "0")
        try:
            duration_seconds = float(duration_raw) if duration_raw else 0.0
            if duration_seconds < 0:
                print("Duration cannot be negative. Please try again.")
                continue
            break
        except ValueError:
            print("Invalid number. Please try again.")

    run_number = int(run_number_raw) if run_number_raw else None
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None

    run = tracker.track(
        workflow_name=name,
        branch=branch,
        status=WorkflowStatus(status_val),
        conclusion=conclusion,
        run_number=run_number,
        commit_sha=commit_sha,
        duration_seconds=duration_seconds,
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


def _check_run_status(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
    else:
        print(
            f"\nRun Status Report for {run.id}:\n"
            f"  is_terminal: {run.is_terminal()}\n"
            f"  is_running: {run.is_running()}\n"
            f"  is_successful: {run.is_successful()}\n"
            f"  is_failed: {run.is_failed()}\n"
            f"  is_cancelled: {run.is_cancelled()}\n"
        )


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


def _advanced_filter_menu(service: WorkflowRunService) -> None:
    """Multi-filter interactive menu for complex query scenarios."""
    filter_kwargs = {}

    while True:
        filter_choices = [
            "branch",
            "status",
            "conclusion",
            "duration",
            "created date range",
            "updated date range",
            "attempts",
            "Done filtering",
        ]
        filter_type = _choose("Select filter to add", filter_choices)

        if filter_type == "Done filtering":
            break

        if filter_type == "branch":
            branch = _prompt("Branch name")
            if branch:
                filter_kwargs["branch"] = branch

        elif filter_type == "status":
            status_val = _choose("Status", [s.value for s in WorkflowStatus])
            filter_kwargs["status"] = WorkflowStatus(status_val)

        elif filter_type == "conclusion":
            conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
            filter_kwargs["conclusion"] = WorkflowConclusion(conclusion_val)

        elif filter_type == "duration":
            while True:
                duration_min_str = _prompt("Minimum duration in seconds (leave blank for no minimum)", "")
                if not duration_min_str:
                    duration_min = None
                    break
                try:
                    duration_min = float(duration_min_str)
                    if duration_min < 0:
                        print("Duration cannot be negative. Please try again.")
                        continue
                    break
                except ValueError:
                    print("Invalid number. Please try again.")

            while True:
                duration_max_str = _prompt("Maximum duration in seconds (leave blank for no maximum)", "")
                if not duration_max_str:
                    duration_max = None
                    break
                try:
                    duration_max = float(duration_max_str)
                    if duration_max < 0:
                        print("Duration cannot be negative. Please try again.")
                        continue
                    if duration_min is not None and duration_max < duration_min:
                        print("Maximum must be >= minimum. Please try again.")
                        continue
                    break
                except ValueError:
                    print("Invalid number. Please try again.")

            if duration_min is not None:
                filter_kwargs["duration_min"] = duration_min
            if duration_max is not None:
                filter_kwargs["duration_max"] = duration_max

        elif filter_type == "created date range":
            while True:
                created_after_str = _prompt("Created after (ISO 8601, leave blank for no minimum)", "")
                if not created_after_str:
                    created_after = None
                    break
                try:
                    created_after = _parse_iso8601(created_after_str)
                    break
                except ValueError as e:
                    print(f"Invalid date: {e}. Please try again.")

            while True:
                created_before_str = _prompt("Created before (ISO 8601, leave blank for no maximum)", "")
                if not created_before_str:
                    created_before = None
                    break
                try:
                    created_before = _parse_iso8601(created_before_str)
                    if created_after is not None and created_before <= created_after:
                        print("Created before must be after created_after. Please try again.")
                        continue
                    break
                except ValueError as e:
                    print(f"Invalid date: {e}. Please try again.")

            if created_after is not None:
                filter_kwargs["created_after"] = created_after
            if created_before is not None:
                filter_kwargs["created_before"] = created_before

        elif filter_type == "updated date range":
            while True:
                updated_after_str = _prompt("Updated after (ISO 8601, leave blank for no minimum)", "")
                if not updated_after_str:
                    updated_after = None
                    break
                try:
                    updated_after = _parse_iso8601(updated_after_str)
                    break
                except ValueError as e:
                    print(f"Invalid date: {e}. Please try again.")

            while True:
                updated_before_str = _prompt("Updated before (ISO 8601, leave blank for no maximum)", "")
                if not updated_before_str:
                    updated_before = None
                    break
                try:
                    updated_before = _parse_iso8601(updated_before_str)
                    if updated_after is not None and updated_before <= updated_after:
                        print("Updated before must be after updated_after. Please try again.")
                        continue
                    break
                except ValueError as e:
                    print(f"Invalid date: {e}. Please try again.")

            if updated_after is not None:
                filter_kwargs["updated_after"] = updated_after
            if updated_before is not None:
                filter_kwargs["updated_before"] = updated_before

        elif filter_type == "attempts":
            has_attempts_choice = _choose("Show runs with attempts?", ["Yes", "No"])
            filter_kwargs["has_attempts"] = has_attempts_choice == "Yes"

    runs = service.filter_runs(**filter_kwargs)

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _add_attempt(service: WorkflowRunService) -> None:
    attempt_service = AttemptService(service)
    print("\n--- Add Workflow Attempt ---")
    run_id = _prompt("Run ID")

    # Validate that the run exists
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return

    attempt_number_raw = _prompt("Attempt number")
    try:
        attempt_number = int(attempt_number_raw)
    except ValueError:
        print("Invalid attempt number. Must be an integer.")
        return

    status_val = _choose("Status", [s.value for s in WorkflowAttemptStatus])
    conclusion_val = _choose("Conclusion (optional)", [c.value for c in WorkflowAttemptConclusion], allow_blank=True)

    # Prompt for duration with validation
    while True:
        duration_raw = _prompt("Duration in seconds (leave blank for no duration)", "")
        if not duration_raw:
            duration_seconds = None
            break
        try:
            duration_seconds = float(duration_raw)
            if duration_seconds < 0:
                print("Duration cannot be negative. Please try again.")
                continue
            break
        except ValueError:
            print("Invalid number. Please try again.")

    conclusion = WorkflowAttemptConclusion(conclusion_val) if conclusion_val else None

    attempt_data = {
        "id": len(run.attempts) + 1,  # Simple ID generation
        "run_id": run_id,
        "attempt_number": attempt_number,
        "status": status_val,
        "conclusion": conclusion_val,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration_seconds,
    }

    try:
        attempt = attempt_service.create_attempt(run_id, attempt_data)
        print(f"\nAdded attempt {attempt.attempt_number} to run {run_id}")
    except ValueError as e:
        print(f"Error: {e}")


def _list_attempts(service: WorkflowRunService) -> None:
    attempt_service = AttemptService(service)
    print("\n--- List Attempts ---")
    run_id = _prompt("Run ID")

    sort_option = _choose("Sort by attempt number?", ["Yes", "No"], allow_blank=False)
    sort_by_number = sort_option == "Yes"

    try:
        attempts = attempt_service.get_attempts_by_run(run_id, sort_by_number=sort_by_number)
        if not attempts:
            print(f"\nNo attempts found for run '{run_id}'.")
            return
        print(f"\n--- {len(attempts)} attempt(s) for run {run_id} ---")
        for attempt in attempts:
            print(_fmt_attempt(attempt))
    except ValueError as e:
        print(f"Error: {e}")


def _view_statistics(service: WorkflowRunService) -> None:
    """View workflow statistics with optional filtering."""
    print("\n--- View Workflow Statistics ---")

    # Prompt for optional filters
    filter_kwargs = {}

    apply_filters = _choose("Apply filters?", ["Yes", "No"], allow_blank=False)
    if apply_filters == "Yes":
        filter_type = _choose("Filter by", ["branch", "status", "conclusion", "None"], allow_blank=False)

        if filter_type == "branch":
            branch = _prompt("Branch name")
            if branch:
                filter_kwargs["branch"] = branch

        elif filter_type == "status":
            status_val = _choose("Status", [s.value for s in WorkflowStatus])
            filter_kwargs["status"] = WorkflowStatus(status_val)

        elif filter_type == "conclusion":
            conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
            filter_kwargs["conclusion"] = WorkflowConclusion(conclusion_val)

    # Get filtered runs
    filtered_runs = service.filter_runs(**filter_kwargs)

    # Compute and format statistics
    stats_service = StatisticsService()
    report = stats_service.compute_statistics(filtered_runs)
    formatted_report = stats_service.format_statistics_for_terminal(report)
    print(formatted_report)


MENU = [
    ("Add workflow run", _add_run),
    ("List all runs", _list_runs),
    ("Get run detail", _detail_run),
    ("Check run status", _check_run_status),
    ("Filter runs", _filter_menu),
    ("Advanced filter runs", _advanced_filter_menu),
    ("Add attempt", _add_attempt),
    ("List attempts", _list_attempts),
    ("View workflow statistics", _view_statistics),
    ("Exit", None),
]


def run_interactive(service: WorkflowRunService) -> None:
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
            handler(service)
        except KeyboardInterrupt:
            print()
