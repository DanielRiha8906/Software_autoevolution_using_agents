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


def _add_run(service: WorkflowRunService, attempt_service: AttemptService) -> None:
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


def _list_runs(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    runs = service.list_runs()
    if not runs:
        print("\nNo runs recorded.")
        return
    print(f"\n--- {len(runs)} run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _detail_run(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
    else:
        print(_fmt_run(run))


def _check_run_state(service: WorkflowRunService, attempt_service: AttemptService) -> None:
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


def _filter_menu(service: WorkflowRunService, attempt_service: AttemptService) -> None:
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


def _add_attempt(service: WorkflowRunService, attempt_service: AttemptService) -> None:
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


def _list_attempts_menu(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    attempts = attempt_service.list_attempts()
    if not attempts:
        print("\nNo attempts recorded.")
        return
    print(f"\n--- {len(attempts)} attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _detail_attempt(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    attempt_id = int(_prompt("\nEnter attempt ID"))
    attempt = attempt_service.get_attempt_detail(attempt_id)
    if attempt is None:
        print(f"No attempt found with id {attempt_id}.")
    else:
        print(_fmt_attempt(attempt))


MENU = [
    ("Add workflow run", _add_run),
    ("List all runs", _list_runs),
    ("Get run detail", _detail_run),
    ("Check run state", _check_run_state),
    ("Filter runs", _filter_menu),
    ("Add attempt", _add_attempt),
    ("List attempts", _list_attempts_menu),
    ("Get attempt detail", _detail_attempt),
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
