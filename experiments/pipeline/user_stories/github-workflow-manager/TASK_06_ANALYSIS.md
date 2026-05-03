# Task 06 Analysis: Aggregated Statistics Over Stored Workflow Runs

## What the Task Is Asking For

Create a statistics aggregation feature that computes metrics over stored workflow runs. The feature must provide:

**Required Statistics:**
1. Count by `conclusion` — number of runs for each WorkflowConclusion value (SUCCESS, FAILURE, CANCELLED, etc.)
2. Average `duration_seconds` — mean execution time across all runs
3. Average number of attempts per run — mean count of retry attempts across all runs
4. Min and max `duration_seconds` — minimum and maximum execution time observed

**Delivery Format:**
- Returned as a **structured dataclass** (not a plain dict)
- Accessible via `python -m src` both as:
  - Interactive menu option
  - One-shot CLI flag with optional filtering parameters

**Bonus Criteria:**
- Per-status breakdown of average duration — average duration grouped by WorkflowStatus (COMPLETED, IN_PROGRESS, etc.)

**Exclusions:**
- No visualisation layer (charts, graphs, or graphical output)

---

## Current State: Existing Architecture

### Data Models

**WorkflowRun** (`src/models/workflow_run.py`)
- `id: str` — unique identifier
- `workflow_name: str`
- `branch: str`
- `status: WorkflowStatus` (enum: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING)
- `conclusion: Optional[WorkflowConclusion]` (enum: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE)
- `created_at: datetime`
- `updated_at: Optional[datetime]`
- `run_number: Optional[int]`
- `commit_sha: Optional[str]`
- `duration_seconds: float = 0.0`

**WorkflowRunAttempt** (`src/models/workflow_run_attempt.py`)
- `id: int` — attempt identifier
- `run_id: int` — foreign key to parent run
- `attempt_number: int` — sequential attempt number (>= 1)
- `status: str`
- `conclusion: Optional[str]`
- `created_at: datetime`
- `duration_seconds: float = 0.0`

### Service Layer

**WorkflowRunService** (`src/services/workflow_run_service.py`)
- `__init__(storage)` — initializes with list of WorkflowRun objects
- `list_runs() -> List[WorkflowRun]` — returns all runs
- `get_run_detail(run_id: str) -> Optional[WorkflowRun]`
- `filter_by_*()` methods for branch, status, conclusion, date ranges, duration ranges, attempt presence
- `query(...) -> List[WorkflowRun]` — composite query supporting AND-combined filters

**WorkflowRunAttemptService** (`src/services/workflow_run_attempt_service.py`)
- `__init__(storage)` — initializes with list of WorkflowRunAttempt objects
- `list_attempts(sorted: bool = True) -> List[WorkflowRunAttempt]`
- `get_attempt(attempt_id: int) -> Optional[WorkflowRunAttempt]`
- `get_attempts_for_run(run_id: int, sorted: bool = True) -> List[WorkflowRunAttempt]`

**WorkflowRunTracker** (`src/services/workflow_run_tracker.py`)
- Wrapper around WorkflowRunService for creating new runs with auto-generated IDs

### Storage Layer

**WorkflowJsonStorage** (`src/storage/workflow_json_storage.py`)
- Loads/saves runs and attempts as JSON arrays in `artifacts/workflow_runs.json` and `artifacts/workflow_run_attempts.json`
- In-memory architecture: loads all data at startup, returns full lists

### CLI & Menu

**workflow_cli.py** — argparse-based one-shot command interface with subcommands:
- `add` — add new run
- `list` — list runs with optional filters
- `detail` — show run details
- `check` — check run state
- `attempt-*` — manage attempts

**interactive_menu.py** — menu-driven interface with 10 options:
1. Add workflow run
2. List all runs
3. Get run detail
4. Check run state
5. Filter runs
6. Advanced filter runs
7. Add workflow run attempt
8. List all attempts
9. Get attempt detail
10. List attempts for run
11. Exit

**__main__.py** — entry point routing to interactive or CLI mode

---

## Task Requirements: Statistics Feature

### 1. Dataclass for Statistics Report

**Not yet created.** Need a new dataclass to hold:
- `count_by_conclusion: dict[str, int]` — e.g., {"success": 42, "failure": 5, "cancelled": 3}
- `average_duration_seconds: float` — mean of all run durations
- `average_attempts_per_run: float` — mean attempts (total attempts / total runs)
- `min_duration_seconds: float` — minimum observed duration
- `max_duration_seconds: float` — maximum observed duration
- `duration_by_status: dict[str, float]` (bonus) — e.g., {"completed": 123.45, "in_progress": 0}

**Expected location:** `src/models/statistics_report.py` (new file)

**Design decision:** Single dataclass, not a service. Immutable report object suitable for serialization/transport.

### 2. Calculation Service

**Not yet created.** Need a new service to compute statistics from runs and attempts.

**Responsibilities:**
- Accept a list of WorkflowRun objects (already filtered or entire set)
- Optionally accept a WorkflowRunAttemptService for attempt counts
- Calculate each statistic
- Return populated StatisticsReport dataclass

**Expected location:** `src/services/statistics_service.py` (new file)

**Method signature (estimated):**
```python
class StatisticsService:
    def calculate_statistics(
        self, 
        runs: List[WorkflowRun],
        attempt_service: Optional[WorkflowRunAttemptService] = None
    ) -> StatisticsReport:
        # Compute all stats
        pass
```

### 3. CLI Integration

**Not yet created.** Need to add a `stats` subcommand to workflow_cli.py that:
- Accepts optional filter parameters (matching `list` command filters)
- Calls service to compute statistics
- Prints formatted report

**Expected signature:**
```bash
python -m src stats [--branch BRANCH] [--status STATUS] [--conclusion CONCLUSION] \
  [--created-after DATE] [--created-before DATE] [--duration-min SECS] [--duration-max SECS] \
  [--has-attempts | --no-attempts]
```

### 4. Interactive Menu Integration

**Not yet created.** Need to add a new menu option that:
- Prompts user for optional filters (like advanced filter)
- Calls service to compute statistics
- Prints formatted report

**Expected location:** New function in `src/cli/interactive_menu.py` (e.g., `_get_statistics()`)

---

## Key Design Decisions

### 1. Statistics Dataclass Location
- **Option A:** New file `src/models/statistics_report.py`
- **Option B:** Inline in service file
- **Recommendation:** Option A — Models and services are separate concerns; dataclass is a model (domain object representing a report)

### 2. Calculation Service vs. Inline Logic
- **Option A:** New `StatisticsService` class
- **Option B:** Add method to `WorkflowRunService`
- **Recommendation:** Option A — Separate service allows reuse, testability, and single responsibility

### 3. Filtering Before or After Statistics?
- **Current pattern:** Task allows optional filter parameters → statistics computed on filtered subset
- **Implementation:** Reuse existing `service.query()` method to get filtered runs, then compute stats on that subset
- **Alternative:** Compute on all runs always → Less flexible, wastes computation

### 4. Attempt Counts: Total Attempts vs. Runs With Attempts?
- **Ambiguity:** "Average number of attempts per run" — do we count:
  - Total attempts across all runs / total runs? (gives fractional value per run)
  - Or average attempts count for runs that have attempts? (ignores runs with zero attempts)
- **Working assumption:** First interpretation (total / count) — includes runs with 0 attempts, making average realistic

### 5. Per-Status Breakdown Scope
- **Current requirement:** Per-status breakdown of average duration
- **Status values:** QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING
- **Design:** Dictionary mapping status.value (string) to average duration (float) for that status
- **Edge case:** What if no runs have a given status? Include in dict with 0 runs (or omit)?
- **Recommendation:** Include all statuses in dict, even if 0 runs match; set average to 0.0 or NaN for clarity

---

## Ambiguities & Working Assumptions

### 1. "Average attempts per run" — Two Interpretations

**Ambiguity:** How is this calculated?

**Interpretation A:** `total_attempts / total_runs`
- Example: 100 runs, 120 attempts total → average = 1.2 attempts/run
- Includes runs with zero attempts

**Interpretation B:** `total_attempts / runs_with_attempts`
- Example: 100 runs, 80 have attempts (120 total) → average = 1.5 attempts/run
- Ignores runs with no retries

**Working Assumption:** Interpretation A (include all runs in denominator). This reflects the realistic question: "On average, how many times does each run execute?" The answer includes single-attempt runs as 1.0.

### 2. Empty Dataset Handling

**Ambiguity:** What if no runs match the filter criteria?

**Working Assumption:** Return valid statistics with sensible defaults:
- `count_by_conclusion` = {} (empty dict)
- `average_duration_seconds` = 0.0 (or NaN to indicate no data)
- `average_attempts_per_run` = 0.0
- `min_duration_seconds` = float('inf') or 0.0 or None?
- `max_duration_seconds` = float('-inf') or 0.0 or None?

**Decision:** Use 0.0 for averages, and for min/max with empty data: `min_duration_seconds = None, max_duration_seconds = None` (use Optional[float]). Alternatively, raise ValueError if dataset is empty. **Recommended:** Check if empty and return sensible defaults (0.0, empty dict); don't raise.

### 3. Duration by Status: Grouping Method

**Ambiguity:** Does "per-status breakdown of average duration" mean:
- Group runs by their `status` field and compute average duration per group?
- Or group by `conclusion` (terminal state)?

**Working Assumption:** Group by `status` field (COMPLETED, IN_PROGRESS, etc.). This separates running jobs from completed ones.

### 4. Data Type for conclusion counts

**Ambiguity:** `count_by_conclusion` dict keys — should they be:
- String (WorkflowConclusion.value) — "success", "failure", etc.?
- WorkflowConclusion enum instance?

**Working Assumption:** String keys (conclusion.value or conclusion.value if not None). More JSON-friendly and matches enum pattern used elsewhere.

### 5. Dataclass Mutability

**Ambiguity:** Should StatisticsReport be immutable (frozen)?

**Working Assumption:** Use `@dataclass(frozen=True)` to prevent accidental mutations after creation. Report is a value object, not a mutable entity.

---

## Scope Signals

### In Scope
- ✅ StatisticsReport dataclass with 5 required + 1 bonus field
- ✅ Calculation of count by conclusion
- ✅ Calculation of average duration
- ✅ Calculation of average attempts per run
- ✅ Min and max duration
- ✅ Bonus: Per-status average duration breakdown
- ✅ StatisticsService to compute reports
- ✅ `python -m src stats` CLI command with optional filters
- ✅ Interactive menu option for statistics
- ✅ Reuse existing filtering (WorkflowRunService.query())
- ✅ Integration with WorkflowRunAttemptService for attempt counts

### Out of Scope
- ❌ Visualisation/charting (explicitly excluded)
- ❌ Database queries or caching (in-memory only)
- ❌ Historical statistics (only current snapshot)
- ❌ Percentile calculations (not mentioned)
- ❌ Per-branch or per-workflow-name breakdowns (not required; only per-status bonus)
- ❌ Export to external formats (just text output)

### Borderline
- ✓ Statistics caching — Not mentioned; assume recompute each time (simple, no stale data risk)
- ✓ Update diagrams — Standard post-implementation task

---

## Existing Patterns to Follow

### 1. Service Pattern
```python
# Pattern from WorkflowRunService
class SomeService:
    def __init__(self, storage):
        self._storage = storage
        self._data = storage.load()
    
    def _persist(self):
        self._storage.save(self._data)
    
    def some_method(self):
        # Operate on self._data
        pass
```

**For StatisticsService:** No persistence needed (read-only calculation), so skip _persist(). Inject dependencies (service instances, not storage).

### 2. Dataclass Pattern
```python
# Pattern from WorkflowRun
@dataclass
class SomeModel:
    field1: str
    field2: float = 0.0
    
    def __post_init__(self):
        # Validation
        if self.field2 < 0:
            raise ValueError("field2 must be non-negative")
    
    def to_dict(self) -> dict:
        return {...}
    
    @classmethod
    def from_dict(cls, data: dict) -> "SomeModel":
        return cls(...)
```

**For StatisticsReport:** Simpler — no validation needed in __post_init__. No serialization required (read-only report). Consider frozen=True for immutability.

### 3. CLI Pattern
```python
# Pattern from workflow_cli.py
def build_parser():
    parser = argparse.ArgumentParser(...)
    sub = parser.add_subparsers(dest="command", required=True)
    
    stats_p = sub.add_parser("stats", help="...")
    stats_p.add_argument("--branch", ...)
    # ... more args ...
    
    return parser

def run_cli(service, attempt_service, args=None):
    parser = build_parser()
    ns = parser.parse_args(args)
    
    if ns.command == "stats":
        # Compute statistics
        # Print formatted report
        pass
```

**For Task 06:** Add `stats` subcommand similar to `list`; reuse filter argument parsing.

### 4. Interactive Menu Pattern
```python
# Pattern from interactive_menu.py
MENU = [
    ("Option 1", _handler_1),
    ("Option 2", _handler_2),
    ...
]

def run_interactive(service, attempt_service):
    while True:
        # Print menu, read choice
        # Call handler
        pass
```

**For Task 06:** Add new function `_get_statistics()` that prompts for optional filters, then displays report.

---

## Required Changes: Files to Create/Modify

### New Files

#### 1. `src/models/statistics_report.py`
- **Purpose:** Define StatisticsReport dataclass
- **Contents:**
  ```python
  @dataclass(frozen=True)
  class StatisticsReport:
      count_by_conclusion: dict[str, int]
      average_duration_seconds: float
      average_attempts_per_run: float
      min_duration_seconds: Optional[float]
      max_duration_seconds: Optional[float]
      duration_by_status: dict[str, float]  # Bonus field
  ```
- **Methods:** None required beyond dataclass defaults (no to_dict/from_dict; immutable value object)

#### 2. `src/services/statistics_service.py`
- **Purpose:** Compute statistics from runs and attempts
- **Contents:**
  ```python
  class StatisticsService:
      def calculate_statistics(
          self, 
          runs: List[WorkflowRun],
          attempt_service: Optional[WorkflowRunAttemptService] = None
      ) -> StatisticsReport:
          # Compute each statistic
          # Return populated report
          pass
  ```
- **Responsibilities:**
  - Count conclusions
  - Calculate average duration
  - Calculate average attempts
  - Find min/max duration
  - Calculate per-status breakdown (bonus)

### Modified Files

#### 1. `src/models/__init__.py`
- **Change:** Export StatisticsReport
- **Current exports:** WorkflowRun, WorkflowStatus, WorkflowConclusion, WorkflowRunAttempt
- **Addition:** Add StatisticsReport

#### 2. `src/cli/workflow_cli.py`
- **Changes:**
  1. Add `stats` subcommand to parser in `build_parser()`
  2. Add arguments: `--branch`, `--status`, `--conclusion`, `--created-after`, `--created-before`, `--duration-min`, `--duration-max`, `--has-attempts`, `--no-attempts` (same as `list` command)
  3. Add handler in `run_cli()` for `ns.command == "stats"`
  4. Handler logic:
     - Parse filter arguments (reuse existing _parse_datetime logic)
     - Call service.query() with filters
     - Instantiate StatisticsService
     - Call calculate_statistics(filtered_runs, attempt_service)
     - Format and print report
  5. Add formatting function `_fmt_statistics_report(report: StatisticsReport) -> str`

#### 3. `src/cli/interactive_menu.py`
- **Changes:**
  1. Add new function `_get_statistics(service, attempt_service)` that:
     - Prompts user for optional filters (reuse _advanced_filter_menu pattern)
     - Calls service.query() with filters
     - Instantiates StatisticsService
     - Calls calculate_statistics()
     - Prints formatted report
  2. Add menu option to MENU list (new item before "Exit")
  3. Update dispatcher logic to pass attempt_service to _get_statistics

#### 4. `src/__main__.py`
- **Change:** Import StatisticsService
- **Rationale:** Service is instantiated fresh per command (no persistent state), but needs to be available

#### 5. Test files (TBD by pytest-tester)
- **New file:** `tests/test_statistics_service.py` — unit tests for calculation logic
- **New file:** `tests/test_statistics_cli_integration.py` — CLI integration tests
- **New file:** `tests/test_statistics_interactive_menu.py` — interactive menu tests

#### 6. Diagram files (post-implementation by uml-designer)
- **artifacts/class_diagram.puml** — Add StatisticsReport class; add StatisticsService class
- **artifacts/component_diagram.puml** — Add StatisticsService component; show dependencies
- **artifacts/activity_diagram_main.puml** — Add `stats` command flow
- **artifacts/activity_diagram_interactive.puml** — Add new menu option

---

## Design Decisions Summary

### 1. Statistics Report Structure
- **Dataclass approach:** Simple, immutable, reusable
- **Frozen:** Yes, to prevent accidental mutations
- **Serialization:** Not required (read-only report); omit to_dict/from_dict
- **Fields:** 6 total (5 required + 1 bonus)

### 2. Calculation Service
- **Separate class:** Yes, for testability and reusability
- **Stateless:** Yes, immutable methods that take runs and return report
- **Dependency injection:** Accept services/lists as parameters, don't store state
- **Method name:** `calculate_statistics()` — clear, single responsibility

### 3. CLI Integration
- **Subcommand approach:** Separate `stats` command (not a `list` variant)
- **Filter reuse:** Inherit same filter arguments as `list` for consistency
- **Output format:** Formatted text (no JSON unless specified)

### 4. Interactive Menu Integration
- **New menu option:** Added to MENU list before "Exit"
- **Helper function:** `_get_statistics()` following existing pattern
- **Filter prompts:** Reuse advanced filter prompts (or simplified version)

### 5. Attempt Counting
- **Dependency:** Requires WorkflowRunAttemptService instance
- **Handling:** Pass as optional parameter; compute average only if service provided
- **Edge case:** If service is None, set average_attempts_per_run to 0.0 or handle gracefully

### 6. Empty Dataset Behavior
- **No error:** Return valid report with 0s/empty dicts
- **Min/max:** Use None (Optional[float]) to indicate no data; alternative: 0.0
- **Average:** 0.0 for empty sets
- **Count dict:** Empty dict {}

---

## Calculation Logic Detail

### count_by_conclusion
```
For each run in runs:
    conclusion_str = run.conclusion.value if run.conclusion else None
    if conclusion_str:
        count_by_conclusion[conclusion_str] += 1
```

### average_duration_seconds
```
if len(runs) == 0:
    return 0.0
total_duration = sum(run.duration_seconds for run in runs)
return total_duration / len(runs)
```

### average_attempts_per_run
```
if len(runs) == 0:
    return 0.0
if attempt_service is None:
    return 0.0  # Or raise ValueError?
total_attempts = len(attempt_service.list_attempts())
return total_attempts / len(runs)
```

### min_duration_seconds
```
if len(runs) == 0:
    return None
return min(run.duration_seconds for run in runs)
```

### max_duration_seconds
```
if len(runs) == 0:
    return None
return max(run.duration_seconds for run in runs)
```

### duration_by_status (Bonus)
```
by_status = {}
for status in WorkflowStatus:
    matching = [r for r in runs if r.status == status]
    if matching:
        avg = sum(r.duration_seconds for r in matching) / len(matching)
        by_status[status.value] = avg
    else:
        by_status[status.value] = 0.0  # Or omit if not found
return by_status
```

---

## Expected CLI Usage

```bash
# Get statistics for all runs
python -m src stats

# Get statistics for completed runs only
python -m src stats --status completed

# Get statistics for runs with attempts
python -m src stats --has-attempts

# Get statistics for runs in specific date range
python -m src stats --created-after 2025-05-01 --created-before 2025-05-03

# Combine filters
python -m src stats --status completed --conclusion success --duration-min 10.0
```

## Expected Menu Usage

```
Interactive Menu

1. Add workflow run
2. List all runs
3. Get run detail
4. Check run state
5. Filter runs
6. Advanced filter runs
7. Get Statistics  # NEW
8. Add workflow run attempt
9. List all attempts
10. Get attempt detail
11. List attempts for run
12. Exit

Select option: 7

--- Get Statistics ---
Filter by branch? [Yes/No]: No
Filter by status? [Yes/No]: Yes
Status: [List options]
... (continue with filter prompts) ...

--- Statistics Report ---
Count by Conclusion:
  success: 42
  failure: 5
  cancelled: 2
  skipped: 1

Average Duration: 123.45 seconds
Average Attempts per Run: 1.2
Min Duration: 12.34 seconds
Max Duration: 456.78 seconds

Duration by Status:
  completed: 145.67 seconds
  in_progress: 0.0 seconds
  queued: 0.0 seconds
  ...
```

---

## Summary

Task 06 requires:

1. **New Model:** StatisticsReport dataclass in `src/models/statistics_report.py`
2. **New Service:** StatisticsService in `src/services/statistics_service.py` with `calculate_statistics()` method
3. **CLI Command:** `stats` subcommand in workflow_cli.py with same filters as `list`
4. **Menu Option:** New interactive menu entry in interactive_menu.py
5. **Integration:** Wire services in __main__.py; update __init__.py exports
6. **Testing:** Comprehensive tests for all calculation logic, CLI integration, and menu
7. **Diagrams:** Update class/component/activity diagrams

**Key design choices:**
- Immutable frozen dataclass for report
- Separate stateless service for calculation
- Reuse existing filter infrastructure from WorkflowRunService.query()
- Empty dataset returns valid report with 0/empty values (no exceptions)
- Average attempts uses total/count (includes runs with 0 attempts)
- Per-status breakdown included as bonus field
