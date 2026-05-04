# Task 10 Analysis: GUI for Displaying and Editing Workflow Runs with tkinter

## What the Task Is Asking For

Implement a graphical user interface (GUI) using tkinter that provides a visual alternative to the CLI and menu-driven interfaces for managing workflow runs. The GUI must:

**Core Requirements:**
1. Display workflow runs in a scrollable list or table showing:
   - Status (e.g., `queued`, `in_progress`, `completed`)
   - Duration (in seconds)
   - Attempt count (number of associated WorkflowRunAttempt records)
2. Support filtering by:
   - Status (enum: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING)
   - Conclusion (enum: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE)
3. Support editing workflow runs through the GUI (modify fields and persist changes)
4. Be launchable via `python -m src --gui` (CLI flag entry point)

**Bonus Requirement:**
- Highlight failed runs (runs with `conclusion == FAILURE`) in a distinct color (e.g., red background or red text)

**Exclusions:**
- No charting or graphical statistics visualization
- No real-time GitHub polling in the GUI
- GUI is not required to have a one-shot flag interface (menu-only or `--gui` flag is sufficient)

---

## Current Class Structure Relevant to Workflow Runs

### Domain Models (`src/models/`)

**WorkflowRun** (`workflow_run.py`)
- Dataclass fields:
  - `id: str` — unique identifier (UUID)
  - `workflow_name: str`
  - `branch: str`
  - `status: WorkflowStatus` — enum (QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING)
  - `conclusion: Optional[WorkflowConclusion]` — enum or None (SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE)
  - `created_at: datetime` — UTC timestamp
  - `updated_at: Optional[datetime]` — UTC timestamp
  - `run_number: Optional[int]`
  - `commit_sha: Optional[str]`
  - `duration_seconds: float` — execution time (default 0.0, validated >= 0)
- Methods:
  - `to_dict() -> dict` — serialization
  - `from_dict(data: dict) -> WorkflowRun` — deserialization
  - `is_terminal() -> bool` — terminal state check
  - `is_successful() -> bool`
  - `is_failed() -> bool`
  - `is_running() -> bool`
  - `is_cancelled() -> bool`

**WorkflowRunAttempt** (`workflow_run_attempt.py`)
- Dataclass fields:
  - `id: int` — attempt identifier
  - `run_id: int` — parent run ID (foreign key)
  - `attempt_number: int` — sequential attempt (>= 1)
  - `status: str`
  - `conclusion: Optional[str]`
  - `created_at: datetime`
  - `duration_seconds: float` (validated >= 0)
- Methods: `to_dict()`, `from_dict()`

**Enums** (`workflow_status.py`, `workflow_conclusion.py`)
- `WorkflowStatus`: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING
- `WorkflowConclusion`: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE

### Service Layer (`src/services/`)

**WorkflowRunService** (`workflow_run_service.py`)
- Constructor: `__init__(storage: WorkflowRunStorage)`
- Core methods:
  - `list_runs() -> List[WorkflowRun]` — all runs
  - `get_run_detail(run_id: str) -> Optional[WorkflowRun]`
  - `add_workflow_run(run: WorkflowRun) -> WorkflowRun`
  - `delete_run(run_id: str) -> bool`
  - `replace_run(run: WorkflowRun) -> None` — update existing run
  - `filter_by_branch(branch: str) -> List[WorkflowRun]`
  - `filter_by_status(status: WorkflowStatus) -> List[WorkflowRun]`
  - `filter_by_conclusion(conclusion: WorkflowConclusion) -> List[WorkflowRun]`
  - `query(...)` — composite filtering with AND logic
  - Persistence: `_persist()` (private, called after modifications)

**WorkflowRunAttemptService** (`workflow_run_attempt_service.py`)
- Constructor: `__init__(storage: WorkflowRunAttemptStorage)`
- Core methods:
  - `list_attempts(sorted: bool = True) -> List[WorkflowRunAttempt]`
  - `get_attempts_for_run(run_id: int, sorted: bool = True) -> List[WorkflowRunAttempt]`
  - `add_attempt(attempt: WorkflowRunAttempt) -> WorkflowRunAttempt`
  - `delete_attempt(attempt_id: int) -> bool`
  - `replace_attempt(attempt: WorkflowRunAttempt) -> None`

**WorkflowRunTracker** (`workflow_run_tracker.py`)
- High-level facade for creating runs with auto-generated UUIDs

### Storage Layer (`src/storage/`)

**WorkflowJsonStorage** (`workflow_json_storage.py`)
- Implements `WorkflowRunStorage` and `WorkflowRunAttemptStorage` protocols
- Constructor: `__init__(filepath: str, attempts_filepath: str)`
- Methods:
  - `load() -> List[WorkflowRun]`
  - `save(runs: List[WorkflowRun]) -> None`
  - `load_attempts() -> List[WorkflowRunAttempt]`
  - `save_attempts(attempts: List[WorkflowRunAttempt]) -> None`
- Persistence: JSON files in `artifacts/` directory

---

## Existing Entry Points and CLI Structure

### Entry Point (`src/__main__.py`)

```python
def main() -> None:
    storage = WorkflowJsonStorage(...)
    service = WorkflowRunService(storage)
    attempt_service = WorkflowRunAttemptService(storage)

    if len(sys.argv) == 1:
        run_interactive(service, attempt_service)  # No args → interactive menu
    else:
        run_cli(service, attempt_service)  # Args → CLI mode
```

**Current behavior:**
- `python -m src` with no args → launches interactive menu
- `python -m src <command> ...` → CLI mode with argparse subcommands

**Existing subcommands in CLI:** add, list, detail, check, attempt-add, attempt-list, attempt-detail, stats, export, import, fetch

### Interactive Menu (`src/cli/interactive_menu.py`)

- Menu-driven interface with numbered options
- Current options include: Add run, List runs, Detail, Check state, Filter, Advanced filter, Add attempt, List attempts, Get attempt, List attempts for run, Exit
- Uses `_prompt()` and `_choose()` helper functions for user input

### CLI Interface (`src/cli/workflow_cli.py`)

- Uses argparse with subparsers
- `build_parser()` function returns configured ArgumentParser
- `run_cli(service, attempt_service, args=None)` parses and executes commands

---

## Required GUI Components

### 1. Main Window
- Root tkinter window with title "GitHub Workflow Manager - GUI"
- Layout: Title/header, Filter section, List/Table section, Action buttons, Status bar

### 2. Filter Controls
- **Status dropdown** — ComboBox or OptionMenu with values: "(All)", "queued", "in_progress", "completed", "waiting", "requested", "pending"
- **Conclusion dropdown** — ComboBox or OptionMenu with values: "(All)", "success", "failure", "cancelled", "skipped", "timed_out", "action_required", "neutral", "stale"
- **Apply Filters button** — triggers list refresh with selected filters

### 3. Display List/Table
- **Primary option:** tkinter.ttk.Treeview (table widget)
  - Columns: ID, Workflow Name, Branch, Status, Conclusion, Duration (s), Attempts, Created At
  - Scrollable (vertical scrollbar)
  - Each row represents one WorkflowRun
- **Alternative:** Listbox with formatted text rows and manual scrolling
- **Bonus:** Visual distinction for failed runs (red background or red text in Status column)

### 4. Action Buttons
- **View Details** — shows full run info in a dialog or separate window
- **Edit** — opens dialog to modify selected run (status, conclusion, duration, etc.)
- **Delete** — removes selected run
- **Refresh** — reload runs from storage, apply current filters
- **Close/Exit** — closes GUI window

### 5. Edit Dialog
- Form fields for editable WorkflowRun properties:
  - workflow_name (text entry)
  - branch (text entry)
  - status (dropdown)
  - conclusion (dropdown, optional)
  - run_number (spin box or text entry, optional)
  - commit_sha (text entry, optional)
  - duration_seconds (spin box, numeric)
- Save/Cancel buttons

### 6. Details Dialog
- Read-only display of selected run:
  - All fields from WorkflowRun (including id, created_at, updated_at)
  - Associated attempts (if any) listed below
  - OK button to close

### 7. Status Bar
- Display row count: "Showing X of Y runs"
- Display filter status: "(Filtered by status=completed, conclusion=failure)"

---

## Existing Classes and Their Relationships

### Class Dependency Map for GUI

```
GUI Layer (NEW)
├── WorkflowRunMainWindow (new)
│   ├── uses → WorkflowRunService
│   ├── uses → WorkflowRunAttemptService
│   └── uses → models (WorkflowRun, WorkflowStatus, WorkflowConclusion)
├── WorkflowRunEditDialog (new)
│   └── returns → WorkflowRun (modified)
├── WorkflowRunDetailsDialog (new)
│   └── displays → WorkflowRun + attempts
└── FilterPanel (new, optional)
    └── returns → filter criteria dict

CLI Layer (existing)
├── workflow_cli
├── interactive_menu
└── __main__ (entry point)

Service Layer (existing)
├── WorkflowRunService
├── WorkflowRunAttemptService
├── WorkflowRunTracker
├── StatisticsService
└── WorkflowRunExportImportService

Storage Layer (existing)
└── WorkflowJsonStorage (implements WorkflowRunStorage, WorkflowRunAttemptStorage)

Models (existing)
├── WorkflowRun
├── WorkflowRunAttempt
├── WorkflowStatus
└── WorkflowConclusion
```

---

## What Exists vs. What Needs to Be Created

### Exists (No modification needed)
- ✅ `WorkflowRunService` — CRUD, filtering, querying
- ✅ `WorkflowRunAttemptService` — attempt management
- ✅ `WorkflowRun` dataclass — domain model with all required fields
- ✅ `WorkflowRunAttempt` dataclass — attempt model
- ✅ `WorkflowStatus`, `WorkflowConclusion` enums
- ✅ `WorkflowJsonStorage` — persistence
- ✅ `__main__.py` — entry point dispatcher

### Needs to be created
1. **`src/gui/workflow_gui.py`** (new file)
   - `WorkflowRunMainWindow` class — main GUI window
   - Treeview setup with columns and sorting
   - Filter panel creation and event handling
   - Button handlers (refresh, edit, delete, view details)

2. **`src/gui/dialogs.py`** (new file)
   - `WorkflowRunDetailsDialog` class — read-only details view
   - `WorkflowRunEditDialog` class — edit form with validation
   - Helper functions for formatting display values

3. **`src/gui/__init__.py`** (new file)
   - Public API exports (main window class)

### Needs to be modified
1. **`src/__main__.py`**
   - Add `--gui` flag to argparse (or check sys.argv for `--gui`)
   - If `--gui` flag present, launch GUI instead of CLI/interactive menu
   - Import and instantiate `WorkflowRunMainWindow` from new gui module

### Optional new components
- **`src/gui/utils.py`** — helper functions for formatting, color schemes, validation
- **`tests/test_gui_*.py`** — unit tests for GUI components (may not be required for Tkinter)

---

## Dependencies and Imports Already Present

### Standard Library Modules Used in Codebase
- `argparse` — CLI argument parsing
- `datetime` — timestamps
- `json` — file persistence
- `uuid` — unique ID generation
- `typing` — type hints (List, Optional, etc.)
- `enum` — status/conclusion enums
- `abc` — abstract base classes (protocols)

### New Imports Required for GUI
- `tkinter` — core GUI framework (stdlib, already verified available)
- `tkinter.ttk` — themed widgets (Treeview)
- `tkinter.messagebox` — dialogs for confirmations/errors
- `tkinter.simpledialog` — simple input dialogs (if needed)

### Third-Party Dependencies
- **None currently required** — tkinter is part of Python stdlib
- No additional packages needed for Task 10

---

## Key Ambiguities and Working Assumptions

### Ambiguity 1: Run ID Type Mismatch
**Problem:** `WorkflowRun.id` is `str` (UUID), but `WorkflowRunAttempt.run_id` is `int`.

**Evidence:** 
- `workflow_run.py`: `id: str`
- `workflow_run_attempt.py`: `run_id: int`

**Impact:** Cannot directly join runs with attempts without type conversion.

**Working Assumption:** 
- GUI will display attempt count by counting `attempts where run_id == int(run.id)` (attempt will fail for UUID-string IDs)
- Numeric run IDs will show correct attempt counts
- UUID-string run IDs will show 0 attempts in the GUI
- This matches the existing behavior in `WorkflowRunService.filter_by_attempt_presence()`

### Ambiguity 2: Edit Validation Rules
**Problem:** Not specified which fields are editable, which are read-only, or what validation applies.

**Evidence:** None in requirements.

**Working Assumption:**
- Editable fields: workflow_name, branch, status, conclusion, run_number, commit_sha, duration_seconds
- Read-only fields: id, created_at, updated_at
- Validation: reuse existing `WorkflowRun.__post_init__()` validation (duration_seconds >= 0)
- For conclusion: allow setting to None (optional)

### Ambiguity 3: Bulk Operations
**Problem:** Requirements don't specify if GUI supports bulk edit/delete (multi-select).

**Evidence:** None in requirements.

**Working Assumption:**
- Single-select only: select one row, then click Edit or Delete
- Multi-select not implemented unless explicitly required later

### Ambiguity 4: Color Scheme for "Failed" Highlight
**Problem:** "Distinct color" not specified (red text? red background? both?).

**Evidence:** Requirement says "Highlight failed runs in distinct color (bonus)".

**Working Assumption:**
- Use red text in the Status/Conclusion column for rows where `conclusion == FAILURE`
- Apply to Treeview tag with `foreground='red'`
- Not changing background to avoid readability issues

### Ambiguity 5: Filtering Behavior
**Problem:** "Filter by status or conclusion" — does this mean AND or OR logic?

**Evidence:** Existing `WorkflowRunService.query()` uses AND logic for combined filters.

**Working Assumption:**
- GUI filters will also use AND logic
- If status is "completed" AND conclusion is "failure", show only completed failures
- If conclusion is "(All)" or None, ignore conclusion filter in query

### Ambiguity 6: Launch Behavior
**Problem:** `python -m src --gui` can be a flag in __main__.py or a subcommand in argparse.

**Evidence:** Requirement says "`python -m src --gui`" (suggests flag, not subcommand).

**Working Assumption:**
- Add `--gui` as a top-level flag before subcommands, checked in __main__.py
- If `--gui` present, launch GUI and ignore any subcommand
- Modify __main__.py to check for `--gui` before calling build_parser()

---

## Scope In, Out, and Borderline

### Explicitly In
- ✅ Scrollable list/table display of workflow runs
- ✅ Show status, duration, attempt count columns
- ✅ Filter by status and conclusion
- ✅ Edit dialog to modify run fields
- ✅ Persist changes to storage
- ✅ Highlight failed runs (bonus)
- ✅ Launchable via `python -m src --gui`

### Explicitly Out
- ❌ Real-time GitHub polling in GUI
- ❌ Charts, graphs, or graphical statistics
- ❌ One-shot CLI flags for GUI operations (GUI-only interface)
- ❌ Dark mode/light mode themes
- ❌ Keyboard shortcuts (nice-to-have, not required)
- ❌ Export/Import in GUI (use CLI for these)

### Borderline (Not Required Unless Specified)
- ? Multi-select and bulk operations
- ? Details pane vs. separate dialog
- ? Auto-refresh timer
- ? Search/filter by workflow name
- ? Sorting by column click
- ? Status/attempt count badge icons

---

## Priority and Implementation Order

### Must Do (Core Requirement)
1. **Entry point wiring** — modify `__main__.py` to accept `--gui` flag
2. **Main window** — `WorkflowRunMainWindow` with Treeview display
3. **Service integration** — populate Treeview from `WorkflowRunService.list_runs()`
4. **Filtering UI** — status and conclusion dropdowns + apply button
5. **Edit dialog** — form to modify selected run and persist via service
6. **Attempt counting** — query `WorkflowRunAttemptService` to show count per run
7. **View Details** — dialog or popup showing full run info

### Should Do (Bonus/High-Value)
8. **Red highlighting for failed runs** — tag failed rows in red
9. **Delete button** — remove runs via `service.delete_run()`
10. **Refresh button** — reload from storage and reapply filters

### Nice to Have (Not Required)
- Sorting by column click
- Multi-select bulk delete
- Search by workflow name
- Auto-refresh timer

---

## File Paths Summary

**New files to create:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/gui/__init__.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/gui/workflow_gui.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/gui/dialogs.py`

**Files to modify:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/__main__.py`

**Files to reference (no changes):**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run_attempt.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/services/workflow_run_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/services/workflow_run_attempt_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/storage/workflow_json_storage.py`
