import sys
from datetime import datetime
from typing import Optional

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_attempt_service import WorkflowAttemptService
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
    conclusion = attempt.conclusion.value if attempt.conclusion else "—"
    completed = attempt.completed_at.isoformat() if attempt.completed_at else "—"
    logs_url = attempt.logs_url or "—"
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status.value}\n"
        f"  conclusion      : {conclusion}\n"
        f"  started_at      : {attempt.started_at.isoformat()}\n"
        f"  completed_at    : {completed}\n"
        f"  duration_seconds: {attempt.duration_seconds}\n"
        f"  logs_url        : {logs_url}\n"
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
    duration_raw = _prompt("Duration in seconds", "0.0")

    run_number = int(run_number_raw) if run_number_raw else None
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None
    duration_seconds = float(duration_raw) if duration_raw else 0.0

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


def _query_run_state(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return
    print(f"\n--- Run State ---")
    print(f"  ID        : {run.id}")
    print(f"  Terminal  : {'yes' if run.is_terminal() else 'no'}")
    print(f"  Running   : {'yes' if run.is_running() else 'no'}")
    print(f"  Successful: {'yes' if run.is_successful() else 'no'}")
    print(f"  Failed    : {'yes' if run.is_failed() else 'no'}")
    print(f"  Cancelled : {'yes' if run.is_cancelled() else 'no'}")


def _add_attempt(attempt_service: WorkflowAttemptService) -> None:
    from ..services.workflow_attempt_tracker import WorkflowAttemptTracker
    tracker = WorkflowAttemptTracker(attempt_service)
    print("\n--- Add Workflow Attempt ---")
    run_id = _prompt("Run ID")
    attempt_number_raw = _prompt("Attempt number")
    status_val = _choose("Status", [s.value for s in WorkflowStatus])
    conclusion_val = _choose("Conclusion (optional)", [c.value for c in WorkflowConclusion], allow_blank=True)
    completed_at_raw = _prompt("Completed at (ISO format, leave blank to skip)", "")
    duration_raw = _prompt("Duration in seconds", "0.0")
    logs_url = _prompt("Logs URL (leave blank to skip)", "") or None

    attempt_number = int(attempt_number_raw)
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None
    completed_at = None
    if completed_at_raw:
        completed_at = datetime.fromisoformat(completed_at_raw)
    duration_seconds = float(duration_raw) if duration_raw else 0.0

    attempt = tracker.create_attempt(
        run_id=run_id,
        attempt_number=attempt_number,
        status=WorkflowStatus(status_val),
        conclusion=conclusion,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        logs_url=logs_url,
    )
    print(f"\nAdded attempt {attempt.id}")


def _list_attempts(attempt_service: WorkflowAttemptService) -> None:
    attempts = attempt_service.list_attempts()
    if not attempts:
        print("\nNo attempts recorded.")
        return
    print(f"\n--- {len(attempts)} attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _detail_attempt(attempt_service: WorkflowAttemptService) -> None:
    attempt_id = _prompt("\nEnter attempt ID")
    attempt = attempt_service.get_attempt_detail(attempt_id)
    if attempt is None:
        print(f"No attempt found with id '{attempt_id}'.")
    else:
        print(_fmt_attempt(attempt))


def _filter_attempts_menu(attempt_service: WorkflowAttemptService) -> None:
    filter_by = _choose("Filter by", ["run_id", "status", "conclusion"])
    if filter_by == "run_id":
        run_id = _prompt("Run ID")
        attempts = attempt_service.filter_by_run_id(run_id)
    elif filter_by == "status":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        attempts = attempt_service.filter_by_status(WorkflowStatus(status_val))
    else:
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        attempts = attempt_service.filter_by_conclusion(WorkflowConclusion(conclusion_val))

    if not attempts:
        print("\nNo matching attempts.")
        return
    print(f"\n--- {len(attempts)} matching attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _query_attempt_state(attempt_service: WorkflowAttemptService) -> None:
    attempt_id = _prompt("\nEnter attempt ID")
    attempt = attempt_service.get_attempt_detail(attempt_id)
    if attempt is None:
        print(f"No attempt found with id '{attempt_id}'.")
        return
    print(f"\n--- Attempt State ---")
    print(f"  ID        : {attempt.id}")
    print(f"  Terminal  : {'yes' if attempt.is_terminal() else 'no'}")
    print(f"  Running   : {'yes' if attempt.is_running() else 'no'}")
    print(f"  Successful: {'yes' if attempt.is_successful() else 'no'}")
    print(f"  Failed    : {'yes' if attempt.is_failed() else 'no'}")
    print(f"  Cancelled : {'yes' if attempt.is_cancelled() else 'no'}")


def _run_menu(
    service: WorkflowRunService,
    attempt_service: Optional[WorkflowAttemptService] = None,
) -> None:
    run_menu = [
        ("Add workflow run", lambda s: _add_run(s)),
        ("List all runs", lambda s: _list_runs(s)),
        ("Get run detail", lambda s: _detail_run(s)),
        ("Filter runs", lambda s: _filter_menu(s)),
        ("Query workflow state", lambda s: _query_run_state(s)),
        ("Back", None),
    ]
    print("\n--- Workflow Runs ---")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(run_menu, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(run_menu)):
            print("Invalid selection.")
            continue
        label, handler = run_menu[int(raw) - 1]
        if handler is None:
            return
        try:
            handler(service)
        except KeyboardInterrupt:
            print()


def _attempt_menu(
    attempt_service: WorkflowAttemptService,
) -> None:
    attempt_menu = [
        ("Add workflow attempt", lambda s: _add_attempt(s)),
        ("List all attempts", lambda s: _list_attempts(s)),
        ("Get attempt detail", lambda s: _detail_attempt(s)),
        ("Filter attempts", lambda s: _filter_attempts_menu(s)),
        ("Query attempt state", lambda s: _query_attempt_state(s)),
        ("Back", None),
    ]
    print("\n--- Workflow Attempts ---")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(attempt_menu, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(attempt_menu)):
            print("Invalid selection.")
            continue
        label, handler = attempt_menu[int(raw) - 1]
        if handler is None:
            return
        try:
            handler(attempt_service)
        except KeyboardInterrupt:
            print()


MENU = [
    ("Workflow Runs", "runs"),
    ("Workflow Attempts", "attempts"),
    ("Exit", None),
]


def run_interactive(
    service: WorkflowRunService,
    attempt_service: Optional[WorkflowAttemptService] = None,
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
        label, submenu = MENU[int(raw) - 1]
        if submenu is None:
            print("Goodbye.")
            sys.exit(0)
        try:
            if submenu == "runs":
                _run_menu(service, attempt_service)
            elif submenu == "attempts":
                if attempt_service is None:
                    print("Attempt service not initialized.")
                    continue
                _attempt_menu(attempt_service)
        except KeyboardInterrupt:
            print()
