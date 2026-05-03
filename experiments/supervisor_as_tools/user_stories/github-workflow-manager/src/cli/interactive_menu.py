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


MENU = [
    ("Add workflow run", _add_run),
    ("List all runs", _list_runs),
    ("Get run detail", _detail_run),
    ("Check run status", _check_run_status),
    ("Filter runs", _filter_menu),
    ("Add attempt", _add_attempt),
    ("List attempts", _list_attempts),
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
