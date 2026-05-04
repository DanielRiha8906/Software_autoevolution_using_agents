# Task 10 Analysis: GUI Viewer for Workflow Runs

## Task Overview

Task 10 requires implementing a **GUI (Graphical User Interface) viewer** to display workflow runs in a structured format with scrollable display, filtering capabilities, and optional visual enhancements. The GUI must be launchable via `python -m src --gui` and display critical workflow metadata in a read-only interface.

## Current Architecture Understanding

### 1. Current State Assessment

**Entry Point Architecture** (`src/__main__.py`):
- Main function initializes storage, services, and GitHub integration
- Decision logic: if `len(sys.argv) == 1` → interactive menu, else → CLI parser
- **Problem**: No handling for `--gui` flag; decision assumes binary choice between interactive or CLI

**Current Interface Layers**:
- **CLI Layer** (`src/cli/workflow_cli.py`): argparse-based, command-driven, text output
- **Interactive Menu** (`src/cli/interactive_menu.py`): text-based prompting with stdin/stdout
- **No GUI layer exists**: No tkinter, PyQt, or equivalent

**Data Access Patterns**:
- `WorkflowRunService.list_runs()` → returns `List[WorkflowRun]`
- `WorkflowRunService.filter_*()` → returns filtered lists
- `WorkflowRunService.filter_runs()` → composite filter method
- `WorkflowAttemptService.filter_by_run_id(run_id)` → returns attempts for a run
- All services maintain in-memory lists (no lazy loading)

**WorkflowRun Model** (`src/models/workflow_run.py`):
```python
@dataclass
class WorkflowRun:
    id: str
    workflow_name: str
    branch: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: Optional[datetime]
    run_number: Optional[int]
    commit_sha: Optional[str]
    duration_seconds: float
    # Methods: is_terminal(), is_running(), is_successful(), is_failed(), is_cancelled()
```

**WorkflowRunAttempt Model** (`src/models/workflow_attempt.py`):
```python
@dataclass
class WorkflowRunAttempt:
    id: str
    run_id: str
    attempt_number: int
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    logs_url: Optional[str]
```

---

## Key Findings

### 1. Data Model is GUI-Ready

**Strengths**:
- All required fields for display are present in `WorkflowRun`:
  - `status` (enum with human-readable values)
  - `duration_seconds` (numeric, directly displayable)
  - `attempt_number` (can be derived from attempts list)
  - `created_at`, `updated_at` (timestamps)
  - `conclusion` (optional enum)

- `WorkflowRunAttempt` model includes all necessary metadata:
  - `attempt_number` (explicitly stored)
  - `status`, `conclusion` (state tracking)
  - `duration_seconds` (execution time)

**No structural changes needed to models.**

### 2. Service Layer Provides Necessary APIs

**Available for GUI Use**:
- `WorkflowRunService.list_runs()` → full list
- `WorkflowRunService.filter_by_status(status)` → filter by status
- `WorkflowRunService.filter_by_conclusion(conclusion)` → filter by conclusion
- `WorkflowRunService.filter_runs(...)` → composite filter with status, conclusion, duration, timestamps
- `WorkflowAttemptService.filter_by_run_id(run_id)` → attempts for a run

**No new service methods required.** GUI can use existing service APIs directly.

### 3. Current CLI Parsing Model Must Change

**Current Logic**:
```python
if len(sys.argv) == 1:
    run_interactive(...)  # Interactive menu
else:
    run_cli(...)  # Parse args
```

**Problem**: This binary decision cannot accommodate three modes (interactive/CLI/GUI).

**Required Change**:
- Move to explicit argument parsing that checks for `--gui` flag early
- If `--gui` is present → launch GUI
- If no args → launch interactive menu (unchanged)
- If other args → launch CLI (unchanged)

**Example logic**:
```python
if "--gui" in sys.argv:
    run_gui(...)
elif len(sys.argv) == 1:
    run_interactive(...)
else:
    run_cli(...)
```

---

## Requirements Mapping

### Must Have (Mandatory Features)

1. **Implement GUI Viewer**
   - Use tkinter (standard library, no dependencies)
   - Create a window-based interface

2. **Display Workflow Runs in Scrollable List or Table**
   - Options:
     - `tkinter.Treeview` widget (table-like with columns)
     - `tkinter.Listbox` with scrollbar (simple list)
     - Custom frame with Canvas + scrollbar (flexible layout)
   - **Recommendation**: Treeview offers best UX (columns, sorting, native appearance)

3. **Show Status, Duration, and Attempt Count per Run**
   - **Columns needed**:
     - Run ID (or first 8 chars for brevity)
     - Workflow Name
     - Branch
     - Status (enum value or icon)
     - Duration (seconds, formatted as "123.45s" or "1m 23s")
     - Attempt Count (count of attempts for this run)
     - Created At (ISO timestamp or formatted)

4. **Read-Only Interface**
   - Display only; no edit/delete operations
   - No modify buttons in GUI
   - Clicking rows may show detail view (optional enhancement)

5. **Launchable via `python -m src --gui`**
   - Add `--gui` flag detection in `src/__main__.py`
   - Create GUI module in `src/gui/` or `src/cli/gui_viewer.py`
   - Must not break existing `python -m src` (interactive) or CLI modes

### Should Have (High Priority)

1. **Filter Runs by Status or Conclusion**
   - Dropdown or input field for status filter
   - Dropdown or input field for conclusion filter
   - "Clear filters" button to reset
   - **Implementation**: Add dropdown widgets, re-query service on change

### Could Have (Nice-to-Have)

1. **Highlight Rows for Failed Runs**
   - Detect `run.is_failed()` or `conclusion == FAILURE`
   - Apply different background color (e.g., light red)
   - Treeview supports row tagging for styling

2. **Support Editing of Workflow Runs**
   - **Note**: This conflicts with "Read-Only Interface" in Must Have
   - **Interpretation**: "Could Have" suggests this is secondary; prioritize read-only

3. **Launchable via Interactive Menu**
   - Add menu option "View runs in GUI" in interactive menu
   - Call GUI module from menu handler

---

## Scope Signals

### In Scope

- Adding `--gui` flag and entry point logic
- Creating a tkinter-based GUI with Treeview or equivalent
- Displaying columns: ID, workflow name, branch, status, conclusion, duration, attempt count
- Status/conclusion filtering via dropdowns
- Row highlighting for failed runs
- Calling existing service methods (no service changes needed)

### Out of Scope

- Database visualization or advanced charting
- Network communication (data already loaded into memory)
- Real-time updates (static snapshot of current data)
- Multi-window workflows or complex navigation
- Authentication UI (GitHub token is handled at CLI/menu level)

### Borderline / Clarification Needed

1. **"Edit workflow runs" (Could Have)**
   - This contradicts "Read-Only Interface" (Must Have)
   - **Assumption**: Read-Only is mandatory; editing is explicitly out of scope for Task 10
   - Could be a future task

2. **Attempt Count Display**
   - Not explicitly mentioned in "Must Have" but implied by "Show ... attempt count per run"
   - Must have code to look up and count attempts for each run

---

## Design Constraints & Decisions

### 1. GUI Framework: tkinter

**Why tkinter**:
- Part of Python standard library (no external dependencies)
- Cross-platform (Windows, macOS, Linux)
- Simple widgets sufficient for tabular display
- Matches project's minimal-dependency philosophy

**Why not alternatives**:
- PyQt / PySide: require external package installation
- wxPython: requires external package
- Web UI (Flask/HTML): out of scope for desktop CLI tool

### 2. Widget Choice: Treeview

**Why Treeview**:
- Native table-like widget with columns and sorting
- Built-in scrollbar support
- Can apply tags for row styling (highlighting failed runs)
- Better UX than Listbox for multi-column data

**Alternative**: Custom Frame + Canvas + scrollbar (more work, less polished)

### 3. Data Flow for GUI

```
src/__main__.py (detect --gui flag)
  ↓
src/gui/gui_viewer.py (or src/cli/gui_viewer.py)
  ↓
WorkflowRunService.list_runs() / filter_runs()
  ↓
WorkflowAttemptService.filter_by_run_id(run_id) [for attempt counts]
  ↓
Treeview widget populated with rows
```

**Key design**: GUI reads services, never writes (read-only).

### 4. Filtering Implementation

**Status Options** (from `WorkflowStatus` enum):
- queued, in_progress, completed, waiting, requested, pending

**Conclusion Options** (from `WorkflowConclusion` enum):
- success, failure, cancelled, skipped, timed_out, action_required, neutral, stale

**Dropdown Behavior**:
- Initially show "All" (no filter applied)
- User selects a value → call `service.filter_by_status()` or `filter_by_conclusion()`
- Empty the Treeview and repopulate with filtered results

### 5. Attempt Count Retrieval

**Implementation Strategy**:
- For each run displayed, call `attempt_service.filter_by_run_id(run.id)`
- len(result) = attempt count
- Display in column

**Performance Note**: With small datasets (< 1000 runs), this is acceptable. For large datasets, could optimize with a pre-computed cache.

### 6. Module Structure

**Option A**: `src/gui/gui_viewer.py`
- Cleaner separation, mirrors `src/cli/` structure
- Requires creating `src/gui/__init__.py`

**Option B**: `src/cli/gui_viewer.py`
- Simpler (no new folder)
- Slightly inconsistent with "GUI is a different interface layer"

**Recommendation**: Option A (separate folder) for clarity, but either works.

---

## Ambiguities & Working Assumptions

### 1. "Attempt Count" Calculation

**Question**: Should attempt count include failed/retried attempts only, or all attempts?

**Assumption**: Include all attempts for a run. The `WorkflowRunAttempt.attempt_number` field tracks retry sequence; we display the count.

**Evidence**: Class diagram notes "filter_by_run_id() returns all attempts for given run_id, sorted by attempt_number".

### 2. Row Detail on Click

**Question**: Should clicking a row show full details (modal dialog or right panel)?

**Assumption**: Not required for Task 10. Must Have specifies "display workflow runs in scrollable list or table" but doesn't mandate detail view. Could be a Could Have.

### 3. Sort Order

**Question**: What is the default sort order for rows?

**Assumption**: Most recent first (by `created_at` descending). Treeview allows user to click columns to re-sort.

### 4. Duration Formatting

**Question**: Display as raw seconds (123.45) or formatted (1m 23.45s)?

**Assumption**: Display as raw seconds with 2 decimal places for consistency with CLI output format.

### 5. Read-Only Constraint with Editing (Could Have)

**Contradiction Identified**: 
- Must Have: "Read-only interface"
- Could Have: "Support editing of workflow runs"

**Assumption for Task 10**: 
- **Must Have dominates**: Implement read-only GUI
- **Could Have (Editing) is deferred**: Out of scope for this task, would be a separate enhancement
- GUI will have no edit/delete buttons

---

## Required Files to Create/Modify

### New Files

1. **`src/gui/` (new folder)**
   - `src/gui/__init__.py` (empty or import gui_viewer)
   - `src/gui/gui_viewer.py` (main GUI implementation)

**Responsibilities**:
- `WorkflowRunsGUIViewer` class (or similar)
- Methods: `__init__(service, attempt_service)`, `run()`, `_populate_table()`, `_apply_filter()`, `_highlight_failed_rows()`
- tkinter widget setup (Treeview, dropdowns, buttons)

### Modified Files

1. **`src/__main__.py`**
   - Add early check for `--gui` flag
   - Import and call GUI runner
   - Update conditional logic to handle three modes

2. **`src/cli/interactive_menu.py`** (Optional for Should Have)
   - Add menu option "View runs in GUI" (if including interactive menu launcher)
   - Call GUI runner from menu handler

### Test Files

1. **`tests/test_gui_viewer.py`** (new)
   - Unit tests for GUI logic (without actually launching windows)
   - Mock tkinter widgets or test data population logic
   - Test filter application, attempt count retrieval

---

## Implementation Priorities

### Phase 1 (Must Have)

1. Create `src/gui/gui_viewer.py` with basic Treeview table
2. Modify `src/__main__.py` to detect and launch `--gui`
3. Populate table with: ID, workflow_name, branch, status, conclusion, duration_seconds, attempt_count
4. Ensure read-only interface (no edit controls)

### Phase 2 (Should Have)

1. Add status dropdown filter
2. Add conclusion dropdown filter
3. Implement filter apply logic (re-query service, refresh table)

### Phase 3 (Could Have)

1. Row highlighting for failed runs (use Treeview tagging)
2. Interactive menu option to launch GUI

### Phase 4 (Test & Polish)

1. Write unit tests for GUI data logic
2. Ensure `python -m src --gui` works end-to-end
3. Verify scrolling, filtering, and display accuracy

---

## Summary

The task requires adding a tkinter-based GUI viewer for workflow runs. The existing service layer provides all necessary data access methods; no changes to models or services are needed. The main work is:

1. **Architecture change**: Modify `src/__main__.py` to handle `--gui` flag alongside existing interactive and CLI modes
2. **New GUI module**: Create tkinter interface with Treeview for tabular display
3. **Filtering**: Wire status/conclusion dropdowns to service filter methods
4. **Styling**: Highlight failed runs with distinct colors
5. **Testing**: Unit and manual tests to verify functionality

The read-only constraint is explicit in Must Have; editing is deferred to potential future work. Tkinter is chosen for simplicity and zero external dependencies.

---

## Key File Paths

Relevant source files to understand:
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/__main__.py` — Entry point
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/cli/workflow_cli.py` — CLI implementation (reference for structure)
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/cli/interactive_menu.py` — Interactive menu (reference for structure)
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/services/workflow_run_service.py` — Service APIs
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/services/workflow_attempt_service.py` — Attempt service for counting
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/models/workflow_run.py` — Data model
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/artifacts/class_diagram.puml` — Architecture diagram

