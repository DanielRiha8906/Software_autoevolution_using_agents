# Task 10: GUI Implementation Analysis
**Date:** 2026-05-04  
**Objective:** Implement a tkinter-based GUI (WorkflowGUI) that displays workflow runs and allows filtering, delegating all logic to the existing service layer.

---

## Current Codebase Structure

### File Organization
```
src/
├── __main__.py                              # Entry point (671 bytes)
├── models/
│   ├── workflow_run.py                      # Domain model (79 lines, 10 fields)
│   ├── workflow_run_attempt.py              # Attempt model (50 lines, 7 fields)
│   ├── workflow_status.py                   # Enum (11 lines, 6 values)
│   ├── workflow_conclusion.py               # Enum (13 lines, 8 values)
│   └── workflow_statistics_report.py        # Data transfer object (14 lines)
├── services/
│   ├── workflow_run_service.py              # Core CRUD and queries (137 lines)
│   ├── attempt_service.py                   # In-memory attempt storage (63 lines)
│   ├── workflow_run_tracker.py              # Facade for run creation (39 lines)
│   ├── workflow_statistics_service.py       # Statistics aggregation (92 lines)
│   ├── github_fetch_service.py              # GitHub CLI integration (250 lines)
│   └── workflow_import_export_service.py    # Import/export with validation (252 lines)
├── storage/
│   └── workflow_json_storage.py             # JSON file persistence (22 lines)
└── cli/
    ├── workflow_cli.py                      # argparse CLI handler (174 lines)
    └── interactive_menu.py                  # Interactive prompt menu (187 lines)
```

### Service Layer API (What the GUI Must Delegate To)

#### WorkflowRunService
```python
__init__(storage: WorkflowJsonStorage) -> None
add_workflow_run(run: WorkflowRun) -> WorkflowRun
list_runs() -> List[WorkflowRun]
get_run_detail(run_id: str) -> Optional[WorkflowRun]
filter_by_branch(branch: str) -> List[WorkflowRun]
filter_by_status(status: WorkflowStatus) -> List[WorkflowRun]
filter_by_conclusion(conclusion: WorkflowConclusion) -> List[WorkflowRun]
query(
    min_duration: Optional[float],
    max_duration: Optional[float],
    created_after: Optional[datetime],
    created_before: Optional[datetime],
    has_attempts: Optional[bool],
    attempt_service: Optional[AttemptService]
) -> List[WorkflowRun]
```

#### AttemptService
```python
__init__() -> None
create(attempt: WorkflowRunAttempt) -> WorkflowRunAttempt
get_by_run_id(run_id: int) -> List[WorkflowRunAttempt]
get_all_attempts() -> List[WorkflowRunAttempt]
```

### WorkflowRun Data Model

**Fields:**
- `id: str` — Unique identifier (UUID)
- `workflow_name: str` — Name of the workflow
- `branch: str` — Git branch
- `status: WorkflowStatus` — Enum: queued, in_progress, completed, waiting, requested, pending
- `conclusion: Optional[WorkflowConclusion]` — Enum or None: success, failure, cancelled, skipped, timed_out, action_required, neutral, stale
- `created_at: datetime` — UTC timestamp
- `updated_at: Optional[datetime]` — UTC timestamp
- `run_number: Optional[int]` — GitHub run number
- `commit_sha: Optional[str]` — Commit SHA
- `duration_seconds: float` — Execution time in seconds (default 0.0)

**Helper Methods:**
- `is_running() -> bool` — Status is IN_PROGRESS
- `is_terminal() -> bool` — Status is COMPLETED
- `is_successful() -> bool` — Status is COMPLETED and conclusion is SUCCESS
- `is_failed() -> bool` — Status is COMPLETED and conclusion is FAILURE
- `is_cancelled() -> bool` — Status is COMPLETED and conclusion is CANCELLED

### WorkflowStatus Enum
```
QUEUED = "queued"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
WAITING = "waiting"
REQUESTED = "requested"
PENDING = "pending"
```

### WorkflowConclusion Enum
```
SUCCESS = "success"
FAILURE = "failure"
CANCELLED = "cancelled"
SKIPPED = "skipped"
TIMED_OUT = "timed_out"
ACTION_REQUIRED = "action_required"
NEUTRAL = "neutral"
STALE = "stale"
```

### Current Entry Point (__main__.py)
```python
def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    service = WorkflowRunService(storage)
    attempt_service = AttemptService()

    # No sub-command args → launch interactive menu
    if len(sys.argv) == 1:
        run_interactive(service, attempt_service)
    else:
        run_cli(service, attempt_service)
```

---

## Test Suite Requirements (Task 10)

The test suite defines the exact contract the GUI must satisfy:

### Test 1: Module Exists
```python
def test_workflow_gui_module_exists():
    from src.gui.workflow_gui import WorkflowGUI
    assert WorkflowGUI is not None
```
**Requirement:** Create `src/gui/workflow_gui.py` with class `WorkflowGUI`.

### Test 2: Service Constructor
```python
def test_workflow_gui_accepts_service():
    from src.gui.workflow_gui import WorkflowGUI
    gui = WorkflowGUI(MagicMock())
    assert gui is not None
```
**Requirement:** `WorkflowGUI.__init__(service)` accepts a service instance (duck-typed, not type-checked).

### Test 3: No Service Instantiation
```python
def test_gui_does_not_instantiate_services():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)
    assert "WorkflowRunService(" not in source
    assert "AttemptService(" not in source
```
**Requirement:** The GUI module source code must NOT contain literal strings "WorkflowRunService(" or "AttemptService(". This is a static code inspection test. The GUI accepts services via dependency injection, never creates them.

### Test 4: No Subprocess or GitHub CLI
```python
def test_gui_does_not_use_github_cli():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)
    assert "subprocess" not in source
    assert "gh " not in source
```
**Requirement:** The GUI source must NOT contain the words "subprocess" or "gh ". No subprocess calls, no GitHub CLI invocation.

### Test 5: References Service
```python
def test_gui_references_service():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)
    assert "service" in source.lower()
```
**Requirement:** The module source must contain the word "service" (case-insensitive). This confirms the service is being used (dependency injection).

### Test 6: Handles Failed Runs Visually
```python
def test_gui_handles_failed_runs_visually():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)
    assert "fail" in source.lower() or "error" in source.lower()
```
**Requirement:** The module source must contain either the word "fail" or "error" (case-insensitive). This confirms the GUI recognizes and displays failed workflow runs in some visual way.

---

## Implementation Rules (Constraints)

1. **Use tkinter from standard library** — No external GUI frameworks. Python's tkinter is built-in.

2. **Accept service instance via constructor** — `WorkflowGUI(service)` or similar, where service is already instantiated.

3. **No service instantiation internally** — All data access goes through the injected service instance.

4. **Delegate all logic to service layer** — No business logic in GUI. Filtering, querying, CRUD all via service methods.

5. **No subprocess or GitHub CLI** — All GitHub interactions already handled by services. GUI never calls subprocess.

6. **No business logic in GUI** — GUI is display and user interaction only. All state management, validation, persistence is in services.

7. **Do not start tkinter main loop during construction** — The GUI class should initialize its widgets but not call `root.mainloop()` in `__init__`. The main loop is typically started elsewhere (entry point or a separate method).

8. **Must be launchable via `python -m src --gui`** — The GUI needs a CLI entry point. This will require updating `src/__main__.py` to add a `--gui` flag.

---

## Data the GUI Needs from Services

### Display Requirements
1. **List all runs** — Call `service.list_runs()` → Display in table/list widget
2. **Filter by branch** — Call `service.filter_by_branch(branch)` → Display filtered results
3. **Filter by status** — Call `service.filter_by_status(status)` → Display filtered results
4. **Filter by conclusion** — Call `service.filter_by_conclusion(conclusion)` → Display filtered results
5. **Get run detail** — Call `service.get_run_detail(run_id)` → Display in detail view
6. **Query runs** — Call `service.query(...)` with optional duration, timestamp, attempt filters

### Visual Handling of Run Status
- **Running** — Use `run.is_running()` → Display in running color/state
- **Successful** — Use `run.is_successful()` → Display in success color/state
- **Failed** — Use `run.is_failed()` → Display in failure color/state (test requirement)
- **Cancelled** — Use `run.is_cancelled()` → Display in cancelled color/state
- **Terminal** — Use `run.is_terminal()` → Display as complete

### Data Available per WorkflowRun
- `id`, `workflow_name`, `branch`, `status` (enum), `conclusion` (enum or None), `created_at`, `updated_at`, `run_number`, `commit_sha`, `duration_seconds`

---

## Architecture Constraints from Existing Code

### Enum Values Must Match
- **WorkflowStatus values:** "queued", "in_progress", "completed", "waiting", "requested", "pending"
- **WorkflowConclusion values:** "success", "failure", "cancelled", "skipped", "timed_out", "action_required", "neutral", "stale"

### Service Layer Guarantees
- **list_runs()** returns List[WorkflowRun] (empty list if no runs)
- **filter_by_*()** returns List[WorkflowRun] (empty list if no matches)
- **get_run_detail(run_id)** returns Optional[WorkflowRun] (None if not found)
- **query()** returns List[WorkflowRun] with complex filtering; raises ValueError or TypeError if params are invalid

### Storage Path
- Runs are persisted to `artifacts/workflow_runs.json` by default
- GUI does not access storage directly; all persistence is via WorkflowRunService

### No Data Modification
- The test suite and requirements do not mandate add/edit/delete functionality in the GUI
- GUI is read-only display and filtering interface
- (If modification is added later, it would call `service.add_workflow_run()` or similar)

---

## Directory Structure (What Needs to Be Created)

```
src/
├── gui/                             # NEW DIRECTORY
│   ├── __init__.py                 # NEW (can be empty)
│   └── workflow_gui.py             # NEW (contains WorkflowGUI class)
└── [existing files unchanged]
```

---

## Integration Point: __main__.py Update Required

The GUI must be launchable via `python -m src --gui`. This requires updating `src/__main__.py`:

**Current logic:**
```python
if len(sys.argv) == 1:
    run_interactive(service, attempt_service)
else:
    run_cli(service, attempt_service)
```

**After GUI addition:**
```python
# Parse --gui flag (or use argparse)
if "--gui" in sys.argv:
    # Import and launch GUI
    from .gui.workflow_gui import WorkflowGUI
    gui = WorkflowGUI(service, attempt_service)
    # OR call a method like gui.run() or root.mainloop()
elif len(sys.argv) == 1:
    run_interactive(service, attempt_service)
else:
    run_cli(service, attempt_service)
```

---

## Test Execution Model

All six tests use **static code inspection** (via `inspect.getsource()`) and **dynamic import** tests:

1. **Module import test** — Imports `src.gui.workflow_gui` and checks class exists
2. **Instantiation test** — Creates instance with MagicMock service
3. **Source code tests** (4 tests) — Parse module source code to verify:
   - No literal "WorkflowRunService(" or "AttemptService("
   - No "subprocess" or "gh " strings
   - Contains word "service"
   - Contains word "fail" or "error"

**Test execution:** `pytest tests/test_workflow_gui.py -v`

---

## Potential Issues and Considerations

### 1. Tkinter Availability
- tkinter is part of Python standard library on most systems
- On some Linux systems, it may need to be installed: `apt-get install python3-tk`
- The GUI should handle ImportError gracefully if tkinter is not available

### 2. Main Loop Timing
- Tkinter's `root.mainloop()` is blocking
- Must NOT be called in `__init__()`, only when GUI is explicitly launched
- Need a separate method or external caller to start the loop
- Options:
  - `gui = WorkflowGUI(service); gui.run()` (run() method calls mainloop)
  - `gui = WorkflowGUI(service); gui.root.mainloop()` (expose root window)
  - `gui = WorkflowGUI(service); start_gui(gui)` (external function)

### 3. Service Dependency
- Service passed to constructor must have `list_runs()`, `filter_by_status()`, etc.
- No type checking in constructor (tests use MagicMock)
- Service should already be initialized with storage

### 4. Visual Distinction of Failed Runs
- Test requires source code to contain "fail" or "error"
- Could be:
  - A color (red for failed)
  - An icon or label
  - A separate section
  - Code variable name like `failed_runs` or `error_indicator`
- Minimum requirement: any mention in the source code

### 5. Datetime Display
- WorkflowRun.created_at and updated_at are Python datetime objects
- Need to format them for display (ISO format is readable, or human-friendly format)
- Timezone handling: created_at is UTC, updated_at may be None

### 6. Optional Fields
- `conclusion` can be None
- `updated_at` can be None
- `run_number` can be None
- `commit_sha` can be None
- GUI must handle these gracefully (display "—" or similar)

### 7. Enum Display
- WorkflowStatus and WorkflowConclusion are string enums
- Can display `.value` (e.g., "in_progress") or human-friendly strings
- If filtering by enum in GUI dropdowns, need to populate from enum values

### 8. Large Datasets
- `list_runs()` may return hundreds of runs
- GUI should handle this gracefully (pagination, scrolling, search)
- Tkinter Treeview widget is good for large lists

---

## Key Findings Summary

### What Service Layer Provides
- Full CRUD and filtering API via WorkflowRunService
- AttemptService for attempt tracking (optional for GUI display)
- All business logic already implemented and tested
- No need for GUI to implement queries or validation

### What GUI Must Do
- Display workflow runs in a user-friendly interface (tkinter)
- Allow filtering by branch, status, conclusion
- Show run details with all available fields
- Visually distinguish failed runs (test requirement)
- Accept service via dependency injection
- Delegate all data access to services

### What GUI Must NOT Do
- Create service instances internally
- Call subprocess or GitHub CLI
- Implement business logic
- Start tkinter main loop in constructor
- Modify or persist data directly (all via service)

### Minimal GUI Scope
The test suite requires a GUI that:
1. Exists as a class in src/gui/workflow_gui.py
2. Accepts a service instance in constructor
3. Uses the service to display runs
4. Visually handles failed runs
5. Can be instantiated and run without errors

A minimal implementation could be a single window with:
- A list/table of runs (from service.list_runs())
- Filter dropdowns (status, branch, conclusion)
- Detail view for selected run
- Visual distinction for failed runs (e.g., red text or icon)

---

## Files to Create

1. **src/gui/__init__.py** — Empty or with imports
2. **src/gui/workflow_gui.py** — WorkflowGUI class implementation
3. **Update src/__main__.py** — Add --gui entry point

**Tests:** 
- Will be provided separately (pytest will search tests/ for test_*workflow_gui*.py)

---

## Next Steps for Implementation

1. **Understand tkinter fundamentals** — root window, frames, widgets (Label, Button, Listbox/Treeview, Combobox)
2. **Design layout** — Main window with filter controls and run display area
3. **Implement WorkflowGUI class** with:
   - `__init__(service, attempt_service=None)` — Initialize widgets, store service reference
   - Methods to fetch and display runs: `refresh()`, `filter_runs()`, `show_detail()`
   - Event handlers for button clicks and filter selections
   - Visual indication for failed runs (colors, icons, or labels)
4. **Update src/__main__.py** to add --gui flag
5. **Test** — Verify all six tests pass via pytest

---

## Summary

The GUI implementation is **well-defined by the test suite** and **architecturally straightforward** because the service layer is complete and well-tested. The GUI is a thin display layer that:
- Accepts a service instance
- Calls service methods to fetch data
- Displays results using tkinter
- Does not implement any business logic

**Key constraint:** Keep all logic in services; GUI is display-only.

