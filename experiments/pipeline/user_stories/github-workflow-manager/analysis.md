# Task 02 Analysis: Add encapsulated state-checking methods to WorkflowRun

## What the Task Is Asking For

Add five mutually-exclusive state-checking methods to the `WorkflowRun` class that encapsulate business logic for querying workflow state:

- `is_terminal()` — Returns True if the run has finished (conclusion is set AND status is COMPLETED)
- `is_successful()` — Returns True if conclusion is SUCCESS and status is COMPLETED
- `is_failed()` — Returns True if conclusion is FAILURE and status is COMPLETED
- `is_running()` — Returns True if status is IN_PROGRESS or REQUESTED or PENDING (actively executing)
- `is_cancelled()` — Returns True if conclusion is CANCELLED and status is COMPLETED

All methods must:
- Derive state from `status` and `conclusion` fields only
- Be mutually exclusive where specified (clarification needed on which pairs conflict)
- Be accessible via `python -m src` menu and CLI flags (user can query state without external tools)
- Not modify existing enum definitions (only add methods to WorkflowRun class)

## Current WorkflowRun Structure

**Location:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`

**Current attributes:**
- `id: str` — unique identifier
- `workflow_name: str` — name of the workflow
- `branch: str` — git branch
- `status: WorkflowStatus` — current execution status (enum: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING)
- `conclusion: Optional[WorkflowConclusion]` — outcome (optional enum: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE)
- `created_at: datetime` — creation timestamp
- `updated_at: Optional[datetime]` — last update timestamp (optional)
- `run_number: Optional[int]` — GitHub run number (optional)
- `commit_sha: Optional[str]` — commit hash (optional)
- `duration_seconds: float` — execution duration (from Task 01, default 0.0)

**Current methods:**
- `__post_init__()` — validates duration_seconds >= 0
- `to_dict() -> dict` — serializes to JSON-compatible dict
- `from_dict(data: dict) -> WorkflowRun` — deserializes from dict (class method)

## Where State Logic Currently Lives

**No existing state-checking methods in the codebase.** Analysis of current code reveals:

1. **Service layer** (`src/services/workflow_run_service.py`):
   - `filter_by_status(status: WorkflowStatus)` — filters by exact status match only
   - `filter_by_conclusion(conclusion: WorkflowConclusion)` — filters by exact conclusion match only
   - No composite state logic (e.g., "is the run terminal?")

2. **CLI layer** (`src/cli/workflow_cli.py`, `src/cli/interactive_menu.py`):
   - `_fmt_run(run: WorkflowRun)` — displays status and conclusion as raw enum values
   - No state-based decision logic (e.g., showing different UI based on run state)

3. **Model layer:**
   - WorkflowRun is a simple dataclass with no business logic methods beyond serialization

**Implication:** State checking (e.g., "is this run done?") would currently require external callers to:
1. Check `run.status == WorkflowStatus.COMPLETED`
2. Check `run.conclusion is not None`
3. Check `run.conclusion == WorkflowConclusion.SUCCESS` (or similar)

This duplicates logic across potential callers. The new methods encapsulate this.

## What the New Methods Should Be

Add to `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`:

```python
def is_terminal(self) -> bool:
    """
    Returns True if the workflow run has reached a terminal state.
    Terminal = COMPLETED status AND conclusion is set (not None).
    Mutually exclusive with: is_running()
    """
    return self.status == WorkflowStatus.COMPLETED and self.conclusion is not None

def is_successful(self) -> bool:
    """
    Returns True if the workflow completed successfully.
    Success = COMPLETED status AND conclusion is SUCCESS.
    Mutually exclusive with: is_failed(), is_cancelled()
    """
    return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.SUCCESS

def is_failed(self) -> bool:
    """
    Returns True if the workflow completed with failure.
    Failure = COMPLETED status AND conclusion is FAILURE.
    Mutually exclusive with: is_successful(), is_cancelled()
    """
    return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.FAILURE

def is_running(self) -> bool:
    """
    Returns True if the workflow is actively executing.
    Running = status is IN_PROGRESS, REQUESTED, or PENDING.
    Mutually exclusive with: is_terminal()
    """
    return self.status in (
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING
    )

def is_cancelled(self) -> bool:
    """
    Returns True if the workflow was cancelled.
    Cancelled = COMPLETED status AND conclusion is CANCELLED.
    Mutually exclusive with: is_successful(), is_failed()
    """
    return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.CANCELLED
```

**Logic model:**
- `is_terminal()` and `is_running()` are mutually exclusive (terminal ↔ not running)
- `is_successful()`, `is_failed()`, `is_cancelled()` are all subsets of `is_terminal()` and mutually exclusive with each other
- A run can be terminal without being any of those three (e.g., COMPLETED + SKIPPED)

## Dependencies and Constraints

### Enum Values Available

**WorkflowStatus** (6 values):
- QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING

**WorkflowConclusion** (8 values, optional):
- SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE

### State Machine Reality (inferred from GitHub Actions)

- **Active states:** `status` is IN_PROGRESS, REQUESTED, PENDING, or QUEUED
- **Terminal states:** `status` is COMPLETED with `conclusion` set
- **Indeterminate:** Other status values (WAITING) may occur in edge cases
- **Conclusion necessity:** A COMPLETED run must have a conclusion; a running run must not

**No external constraints:** These methods derive state from fields already present in the model.

### No Modification to Enums

- Task explicitly forbids modifying `WorkflowStatus` or `WorkflowConclusion` definitions
- This is correct; the enums represent GitHub's state space, not ours

## Entry Point Modifications Needed for CLI/Menu Access

### 1. CLI Layer (`src/cli/workflow_cli.py`)

**Problem:** Users can run `python -m src add ... --status completed --conclusion success`, but there's no way to query state via CLI flags (e.g., `python -m src check --run-id <id> --is-terminal`).

**Solution:** Add a new `check` subcommand to `build_parser()`:

```python
# check
check_p = sub.add_parser("check", help="Check run state")
check_p.add_argument("run_id", help="Run ID")
check_p.add_argument("--is-terminal", action="store_true", help="Check if run is terminal")
check_p.add_argument("--is-successful", action="store_true", help="Check if run succeeded")
check_p.add_argument("--is-failed", action="store_true", help="Check if run failed")
check_p.add_argument("--is-running", action="store_true", help="Check if run is active")
check_p.add_argument("--is-cancelled", action="store_true", help="Check if run was cancelled")
```

Then in `run_cli()`:

```python
elif ns.command == "check":
    run = service.get_run_detail(ns.run_id)
    if run is None:
        print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
        sys.exit(1)
    
    # If no flag specified, show all states
    if not any([ns.is_terminal, ns.is_successful, ns.is_failed, ns.is_running, ns.is_cancelled]):
        print(f"id               : {run.id}")
        print(f"is_terminal      : {run.is_terminal()}")
        print(f"is_successful    : {run.is_successful()}")
        print(f"is_failed        : {run.is_failed()}")
        print(f"is_running       : {run.is_running()}")
        print(f"is_cancelled     : {run.is_cancelled()}")
    else:
        # Check only requested flags
        if ns.is_terminal:
            print(f"{run.id}: is_terminal = {run.is_terminal()}")
        if ns.is_successful:
            print(f"{run.id}: is_successful = {run.is_successful()}")
        if ns.is_failed:
            print(f"{run.id}: is_failed = {run.is_failed()}")
        if ns.is_running:
            print(f"{run.id}: is_running = {run.is_running()}")
        if ns.is_cancelled:
            print(f"{run.id}: is_cancelled = {run.is_cancelled()}")
```

### 2. Interactive Menu (`src/cli/interactive_menu.py`)

Add a new menu option to the `MENU` list:

```python
def _check_run_state(service: WorkflowRunService) -> None:
    """Check state of a run."""
    run_id = _prompt("Enter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return
    
    print(f"\n--- Run State: {run.id} ---")
    print(f"  is_terminal      : {run.is_terminal()}")
    print(f"  is_successful    : {run.is_successful()}")
    print(f"  is_failed        : {run.is_failed()}")
    print(f"  is_running       : {run.is_running()}")
    print(f"  is_cancelled     : {run.is_cancelled()}")

MENU = [
    ("Add workflow run", _add_run),
    ("List all runs", _list_runs),
    ("Get run detail", _detail_run),
    ("Check run state", _check_run_state),  # NEW
    ("Filter runs", _filter_menu),
    ("Exit", None),
]
```

### 3. No Changes Needed to:

- `src/models/workflow_run.py` — Only add methods; no attribute or serialization changes
- `src/services/workflow_run_service.py` — No changes; state methods are on the model
- `src/storage/workflow_json_storage.py` — No changes; state methods are not persisted
- `src/__main__.py` — No changes; router already delegates to CLI or menu based on args

## Testing Patterns (for implementation)

Existing tests (from Task 01) use:
- `_make_run_with_duration()` helper to create test instances with realistic data
- `MagicMock` for service/storage layer mocking in integration tests
- Direct instantiation of `WorkflowRun` for unit tests

**New tests needed:**
- Unit tests on `WorkflowRun` model directly (no mocks):
  - `is_terminal()` returns True when status=COMPLETED and conclusion is set
  - `is_terminal()` returns False when status≠COMPLETED or conclusion is None
  - `is_successful()` returns True only when status=COMPLETED and conclusion=SUCCESS
  - `is_failed()` returns True only when status=COMPLETED and conclusion=FAILURE
  - `is_running()` returns True when status is IN_PROGRESS, REQUESTED, or PENDING
  - `is_running()` returns False when status is QUEUED, WAITING, or COMPLETED
  - `is_cancelled()` returns True only when status=COMPLETED and conclusion=CANCELLED
  - Mutually exclusive pairs (e.g., `is_terminal()` and `is_running()` cannot both be True)
  - Edge cases: All status/conclusion combinations

- CLI/integration tests (with service):
  - `python -m src check <run-id>` returns all state flags
  - `python -m src check <run-id> --is-terminal` returns single state check
  - Non-existent run ID exits with error code 1
  - Multiple flags (e.g., `--is-terminal --is-running`) all print correctly

- Interactive menu tests:
  - Menu option "Check run state" launches `_check_run_state()`
  - Prompts for run ID and displays all state flags
  - Non-existent run ID shows error and returns to menu

## Files That Will Need Changes

1. **Model class:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`
     - Add `is_terminal()` method
     - Add `is_successful()` method
     - Add `is_failed()` method
     - Add `is_running()` method
     - Add `is_cancelled()` method
     - No attribute or serialization changes needed

2. **CLI layer:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/workflow_cli.py`
     - Add `check` subcommand to `build_parser()`
     - Add handler in `run_cli()` for `ns.command == "check"`
     - Output all state flags or query-specific flags based on user input

3. **Interactive menu:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/interactive_menu.py`
     - Add `_check_run_state()` function
     - Add menu entry to `MENU` list

4. **Test files:**
   - Create or update `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/tests/test_state_checking_methods.py`
     - 40+ unit tests for all combinations of status/conclusion
     - Mutually exclusive pair tests
     - Integration tests for CLI `check` subcommand
     - Interactive menu tests

5. **Diagrams:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/artifacts/class_diagram.puml`
     - Add five new methods to WorkflowRun class box
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/artifacts/activity_diagram_main.puml`
     - Add `check` subcommand flow
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/artifacts/activity_diagram_interactive.puml`
     - Add "Check run state" menu option flow

## Ambiguities and Working Assumptions

### 1. Mutually Exclusive Definition

**Ambiguity:** Task says "Methods must be mutually exclusive where specified" but doesn't list which pairs.

**Working assumption:** 
- `is_terminal()` and `is_running()` are mutually exclusive by definition (opposite states)
- `is_successful()`, `is_failed()`, `is_cancelled()` are mutually exclusive with each other (all are terminal conclusions)
- The implementation enforces these via logic, not a guard clause

### 2. Incomplete Conclusion Coverage

**Ambiguity:** Only 3 of 8 conclusion values are covered (SUCCESS, FAILURE, CANCELLED). What about SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE?

**Working assumption:** 
- The task specifies only 5 methods; the other 5 conclusion types don't need dedicated checkers
- A run can be `is_terminal()` without being any of the 5 specific types (e.g., SKIPPED is terminal but has no `is_skipped()` method)
- This is intentional; the 5 methods cover the most common/critical outcomes

### 3. CLI Flag Design

**Ambiguity:** Should `check` command require a single flag or allow multiple?

**Working assumption:**
- Allow multiple flags to query multiple states in one call
- If no flag is provided, show all states (useful for debugging)
- Exit code 0 if run found; 1 if not found

### 4. Return Value Meaning

**Ambiguity:** Should methods return boolean or string representation?

**Working assumption:**
- Methods return strict boolean (True/False)
- CLI layer formats output (e.g., prints "is_terminal = True")
- This keeps the model clean and allows callers to choose how to display

## Scope Signals

### In Scope

- ✅ Five state-checking methods on WorkflowRun class
- ✅ Methods derive state from `status` and `conclusion` only
- ✅ No modification to enum definitions
- ✅ CLI `check` subcommand with optional flags
- ✅ Interactive menu option to check run state
- ✅ Comprehensive unit and integration tests
- ✅ Update class diagram to show new methods

### Out of Scope

- ❌ Modifying WorkflowStatus or WorkflowConclusion enums
- ❌ Adding new fields to WorkflowRun (use existing fields only)
- ❌ Persisting state check results (state is computed, not stored)
- ❌ Creating a new service class for state logic (keep it on the model)
- ❌ Filtering methods in service layer (focus on per-run checks, not bulk queries)

### Borderline

- ✓ Service layer filtering methods — Out of scope; task focuses on per-run checks, not bulk filtering
- ✓ State machine validation — Out of scope; task is to expose existing state, not validate transitions
- ✓ GUI/graphical features — Out of scope; keep as CLI/menu, not windowed interface

## Suggested Priorities

### 1. **HIGH**: Implement state-checking methods in WorkflowRun (highest value, lowest complexity)
   - These are the core requirement
   - Unit tests are straightforward (test all status/conclusion combinations)
   - No architectural changes needed

### 2. **HIGH**: CLI `check` subcommand (full CLI accessibility requirement)
   - Task requires "accessible via `python -m src` menu and CLI flags"
   - Relatively simple to add (follow existing `detail` subcommand pattern)
   - Enables headless/automation use cases

### 3. **MEDIUM**: Interactive menu `_check_run_state()` option (full menu accessibility requirement)
   - Completes the "accessible via `python -m src` menu" requirement
   - Low complexity (reuse existing prompt patterns)
   - Adds UI consistency

### 4. **MEDIUM**: Comprehensive state-checking tests (correctness assurance)
   - 40+ test cases covering all status/conclusion combinations
   - Mutually exclusive pair assertions
   - CLI integration tests

### 5. **LOW**: Diagram updates (documentation)
   - Update class diagram to reflect new methods
   - Update activity diagrams to show `check` flow
   - Happens last and doesn't block functionality

---

**Summary:** The task is well-scoped and localized to the WorkflowRun model and CLI/menu layers. No storage or service logic changes needed. The five methods are simple state queries that encapsulate existing field access patterns. Primary complexity is comprehensive testing and ensuring all combinations are covered. CLI and menu integration follow established patterns in the codebase.
