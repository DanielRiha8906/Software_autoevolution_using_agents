import sys
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker


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


MENU = [
    ("Add workflow run", lambda s, a: _add_run(s)),
    ("List all runs", lambda s, a: _list_runs(s)),
    ("Get run detail", lambda s, a: _detail_run(s)),
    ("Filter runs", lambda s, a: _filter_menu(s)),
    ("Check run state", lambda s, a: _check_state(s)),
    ("Add workflow attempt", lambda s, a: _add_attempt(a)),
    ("List all attempts", lambda s, a: _list_attempts(a)),
    ("Get attempts for run", lambda s, a: _get_attempts_by_run(a)),
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
