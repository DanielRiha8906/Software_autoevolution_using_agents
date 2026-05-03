import json
import sys
from typing import Optional
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.attempt_service import AttemptService
from ..services.statistics_service import StatisticsService


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


def _prompt_float(label: str, default: float = 0.0) -> float:
    """Prompt for a float value with non-negative validation."""
    suffix = f" [{default}]"
    while True:
        value_str = input(f"{label}{suffix}: ").strip()
        if not value_str:
            return default
        try:
            value = float(value_str)
            if value < 0.0:
                print("Value must be non-negative, try again.")
                continue
            return value
        except ValueError:
            print("Invalid float value, try again.")


def _fmt_run(run: WorkflowRun) -> str:
    conclusion = run.conclusion.value if run.conclusion else "—"
    return (
        f"  id              : {run.id}\n"
        f"  workflow        : {run.workflow_name}\n"
        f"  branch          : {run.branch}\n"
        f"  status          : {run.status.value}\n"
        f"  conclusion      : {conclusion}\n"
        f"  run_number      : {run.run_number or '—'}\n"
        f"  commit_sha      : {run.commit_sha or '—'}\n"
        f"  created_at      : {run.created_at.isoformat()}\n"
        f"  updated_at      : {run.updated_at.isoformat() if run.updated_at else '—'}\n"
        f"  duration_seconds: {run.duration_seconds}\n"
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


def _fmt_statistics(statistics) -> str:
    """Format WorkflowStatistics for text output."""
    lines = [
        "Workflow Statistics:",
        f"  total_runs                 : {statistics.total_runs}",
        "  count_by_conclusion        :",
    ]
    for conclusion, count in sorted(statistics.count_by_conclusion.items()):
        lines.append(f"    {conclusion}: {count}")
    lines.extend([
        f"  average_duration_seconds   : {statistics.average_duration_seconds:.2f}",
        f"  min_duration_seconds       : {statistics.min_duration_seconds or '—'}",
        f"  max_duration_seconds       : {statistics.max_duration_seconds or '—'}",
        f"  average_attempts_per_run   : {statistics.average_attempts_per_run:.2f}",
    ])
    return "\n".join(lines)


def _add_run(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    tracker = WorkflowRunTracker(service)
    print("\n--- Add Workflow Run ---")
    name = _prompt("Workflow name")
    branch = _prompt("Branch")
    status_val = _choose("Status", [s.value for s in WorkflowStatus])
    conclusion_val = _choose("Conclusion (optional)", [c.value for c in WorkflowConclusion], allow_blank=True)
    run_number_raw = _prompt("Run number (leave blank to skip)", "")
    commit_sha = _prompt("Commit SHA (leave blank to skip)", "") or None
    duration_seconds = _prompt_float("Duration (seconds)", 0.0)

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


def _list_runs(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    runs = service.list_runs()
    if not runs:
        print("\nNo runs recorded.")
        return
    print(f"\n--- {len(runs)} run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _detail_run(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
    else:
        print(_fmt_run(run))


def _check_run_state(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return
    print(_fmt_run(run))
    print("  State flags:")
    print(f"    is_running  : {run.is_running()}")
    print(f"    is_terminal : {run.is_terminal()}")
    print(f"    is_successful: {run.is_successful()}")
    print(f"    is_failed   : {run.is_failed()}")
    print(f"    is_cancelled: {run.is_cancelled()}")


def _prompt_datetime(label: str, default: Optional[str] = None) -> Optional[datetime]:
    """Prompt for datetime in ISO 8601 format.

    Args:
        label: Prompt label.
        default: Default value string (not used if user presses enter).

    Returns:
        Parsed datetime object, or None if user enters blank.

    Raises:
        ValueError: If format is invalid (will be caught and re-prompted).
    """
    suffix = f" [{default}]" if default is not None else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            print("Invalid format. Use ISO 8601 format (e.g., 2026-05-03T12:00:00 or 2026-05-03).")


def _filter_menu(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
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


def _filter_by_duration_interactive(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Interactive duration range filter."""
    print("\n--- Filter by Duration Range ---")
    min_duration = _prompt_float("Minimum duration (seconds)", 0.0)
    max_duration_raw = input("Maximum duration (seconds, leave blank for unlimited): ").strip()
    max_duration = None
    if max_duration_raw:
        try:
            max_duration = float(max_duration_raw)
            if max_duration < 0:
                print("Value must be non-negative.")
                return
        except ValueError:
            print("Invalid float value.")
            return

    try:
        runs = service.filter_by_duration_range(min_duration, max_duration)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _filter_by_created_interactive(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Interactive created date range filter."""
    print("\n--- Filter by Created Date Range ---")
    created_after = _prompt_datetime("Created after (ISO 8601, leave blank to skip)")
    created_before = _prompt_datetime("Created before (ISO 8601, leave blank to skip)")

    try:
        runs = service.filter_runs(
            created_after=created_after,
            created_before=created_before,
        )
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _filter_by_updated_interactive(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Interactive updated date range filter."""
    print("\n--- Filter by Updated Date Range ---")
    updated_after = _prompt_datetime("Updated after (ISO 8601, leave blank to skip)")
    updated_before = _prompt_datetime("Updated before (ISO 8601, leave blank to skip)")

    try:
        runs = service.filter_runs(
            updated_after=updated_after,
            updated_before=updated_before,
        )
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _filter_by_attempts_interactive(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Interactive filter by attempt presence."""
    choice = _choose("Show runs with attempts?", ["Yes", "No"])
    has_attempts = choice == "Yes"

    try:
        runs = service.filter_by_has_attempts(attempt_service, has_attempts)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _filter_compound_interactive(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Interactive compound filter builder."""
    print("\n--- Combine Filters ---")
    filters = {}

    # Ask which filters to apply
    apply_duration = input("Apply duration range filter? (y/n): ").strip().lower() == "y"
    if apply_duration:
        min_dur = _prompt_float("Minimum duration (seconds)", 0.0)
        max_dur_raw = input("Maximum duration (seconds, leave blank for unlimited): ").strip()
        max_dur = None
        if max_dur_raw:
            try:
                max_dur = float(max_dur_raw)
            except ValueError:
                print("Invalid float value.")
                return
        filters["min_duration_seconds"] = min_dur
        filters["max_duration_seconds"] = max_dur

    apply_branch = input("Apply branch filter? (y/n): ").strip().lower() == "y"
    if apply_branch:
        branch = _prompt("Branch name")
        filters["branch"] = branch

    apply_status = input("Apply status filter? (y/n): ").strip().lower() == "y"
    if apply_status:
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        filters["status"] = WorkflowStatus(status_val)

    apply_created = input("Apply created date filter? (y/n): ").strip().lower() == "y"
    if apply_created:
        created_after = _prompt_datetime("Created after (ISO 8601, leave blank to skip)")
        created_before = _prompt_datetime("Created before (ISO 8601, leave blank to skip)")
        filters["created_after"] = created_after
        filters["created_before"] = created_before

    apply_attempts = input("Apply attempts filter? (y/n): ").strip().lower() == "y"
    if apply_attempts:
        has_attempts_choice = _choose("Show runs with attempts?", ["Yes", "No"])
        filters["has_attempts"] = has_attempts_choice == "Yes"
        filters["attempt_service"] = attempt_service

    try:
        runs = service.filter_runs(**filters)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _advanced_filter_menu(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Advanced filter sub-menu."""
    while True:
        print("\n" + "=" * 44)
        choice = _choose(
            "Advanced Filters",
            [
                "Duration range",
                "Created date range",
                "Updated date range",
                "Has attempts",
                "Combine filters",
                "Back to main menu",
            ],
        )

        if choice == "Duration range":
            _filter_by_duration_interactive(service, attempt_service)
        elif choice == "Created date range":
            _filter_by_created_interactive(service, attempt_service)
        elif choice == "Updated date range":
            _filter_by_updated_interactive(service, attempt_service)
        elif choice == "Has attempts":
            _filter_by_attempts_interactive(service, attempt_service)
        elif choice == "Combine filters":
            _filter_compound_interactive(service, attempt_service)
        elif choice == "Back to main menu":
            return


def _add_attempt(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    print("\n--- Add Workflow Attempt ---")
    run_id = int(_prompt("Run ID"))
    attempt_number = int(_prompt("Attempt number"))
    status = _prompt("Status")
    conclusion = _prompt("Conclusion (leave blank for none)", "") or None
    duration_seconds = _prompt_float("Duration (seconds)", 0.0)

    attempt = attempt_service.create_attempt(
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )
    print(f"\nAdded attempt {attempt.id}")


def _list_attempts_menu(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    attempts = attempt_service.list_attempts()
    if not attempts:
        print("\nNo attempts recorded.")
        return
    print(f"\n--- {len(attempts)} attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _detail_attempt(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    attempt_id = int(_prompt("\nEnter attempt ID"))
    attempt = attempt_service.get_attempt_detail(attempt_id)
    if attempt is None:
        print(f"No attempt found with id {attempt_id}.")
    else:
        print(_fmt_attempt(attempt))


def _view_statistics(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Display workflow statistics."""
    print("\n--- Workflow Statistics ---")
    statistics = statistics_service.compute_statistics()

    # Ask for output format
    format_choice = _choose("Output format", ["text", "json"])

    if format_choice == "json":
        print(json.dumps(statistics.to_dict(), indent=2))
    else:
        print(_fmt_statistics(statistics))


MENU = [
    ("Add workflow run", _add_run),
    ("List all runs", _list_runs),
    ("Get run detail", _detail_run),
    ("Check run state", _check_run_state),
    ("Filter runs", _filter_menu),
    ("Advanced Filter", _advanced_filter_menu),
    ("Add attempt", _add_attempt),
    ("List attempts", _list_attempts_menu),
    ("Get attempt detail", _detail_attempt),
    ("View Statistics", _view_statistics),
    ("Exit", None),
]


def run_interactive(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
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
            handler(service, attempt_service, statistics_service)
        except KeyboardInterrupt:
            print()
