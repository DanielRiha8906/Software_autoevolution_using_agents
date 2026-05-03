# Task 06 - Statistics Reporting: Analysis Report

## Task Summary

Implement a statistics computation module that generates structured reports about workflow runs and attempts. The system must:

**Must Have:**
- Compute count grouped by `conclusion` (e.g., 5 SUCCESS, 3 FAILURE, 2 CANCELLED)
- Compute average `duration_seconds` (overall and per-conclusion)
- Compute average number of attempts per run
- Return a structured report object (dataclass or named object, not plain dict)
- Expose all functionality via `python -m src` as both interactive menu option and one-shot CLI flag

**Should Have:**
- Use a dataclass or named object for the report structure
- Include min/max `duration_seconds` in the report

**Could Have:**
- Per-status breakdown of average duration (distinct from per-conclusion)

**Won't Have:**
- Visualization layer (graphs, charts)

---

## Current Architecture Overview

### Three-Tier Layered Architecture

```
Application Entrypoint (__main__.py)
    ↓
Interface Layer (workflow_cli.py, interactive_menu.py)
    ├── CLI: argparse-driven one-shot commands
    └── Interactive: multi-step menu-driven interface
    ↓
Service Layer (WorkflowRunService, WorkflowAttemptService, Trackers)
    ├── WorkflowRunService — CRUD + filtering
    ├── WorkflowAttemptService — CRUD + filtering
    ├── WorkflowRunTracker — run creation facade
    └── WorkflowAttemptTracker — attempt creation facade
    ↓
Storage Layer (WorkflowJsonStorage, WorkflowAttemptJsonStorage)
    ├── JSON file persistence
    └── Load/save operations
    ↓
Domain Models (WorkflowRun, WorkflowRunAttempt, enums)
    ├── Dataclasses with serialization
    ├── State query methods
    └── Type-safe enums
```

### Data Flow
1. Data is loaded from JSON files via storage layer into service layer
2. Services maintain in-memory lists and expose query/filter methods
3. CLI and interactive menu call service methods to retrieve/filter data
4. Statistics computation must operate on service-layer data

---

## Domain Model: Data Structures for Statistics

### WorkflowRun (src/models/workflow_run.py)

**Key Fields for Statistics:**
- `conclusion: Optional[WorkflowConclusion]` — Nullable enum (success, failure, cancelled, skipped, timed_out, action_required, neutral, stale)
- `duration_seconds: float` — Non-negative, default 0.0
- `id: str` — Unique identifier (needed to count runs)

**Important Constraint:**
- A run may have `conclusion = None` (non-terminal states: queued, in_progress, waiting, requested, pending)
- Statistics must handle None conclusions gracefully

### WorkflowRunAttempt (src/models/workflow_attempt.py)

**Key Fields for Statistics:**
- `run_id: str` — Foreign key to parent run
- `attempt_number: int` — Sequence number (1, 2, 3...)
- `duration_seconds: float` — Non-negative, default 0.0
- `conclusion: Optional[WorkflowConclusion]` — Same as WorkflowRun

**Important Relationship:**
- One-to-many: 1 WorkflowRun → N WorkflowRunAttempts
- Attempts are stored separately; must query attempt service to link to runs

### Enums

**WorkflowConclusion (workflow_conclusion.py):**
8 possible values: success, failure, cancelled, skipped, timed_out, action_required, neutral, stale (plus None)

**WorkflowStatus (workflow_status.py):**
6 possible values: queued, in_progress, completed, waiting, requested, pending
(Not used for statistics grouping in must-have, but available for could-have)

---

## Service Layer: Current Capabilities

### WorkflowRunService (src/services/workflow_run_service.py)

**Available Methods:**
- `list_runs() → List[WorkflowRun]` — Get all runs (needed for statistics)
- `filter_runs(...)` → List[WorkflowRun]` — Filter with multiple criteria
- Various filter_by_* methods

**Data Access Pattern:**
- Maintains in-memory `_runs: List[WorkflowRun]` (loaded from storage on init)
- All filtering returns new lists (no mutation)
- Direct access to runs list via `list_runs()`

### WorkflowAttemptService (src/services/workflow_attempt_service.py)

**Available Methods:**
- `list_attempts() → List[WorkflowRunAttempt]` — Get all attempts
- `filter_by_run_id(run_id: str) → List[WorkflowRunAttempt]` — Get attempts for a run (sorted by attempt_number ascending)

**Data Access Pattern:**
- Maintains in-memory `_attempts: List[WorkflowRunAttempt]` (loaded from storage on init)
- Can link attempts to runs via run_id foreign key

---

## Statistics Requirements Analysis

### Requirement 1: Count by Conclusion

**What to compute:**
- Group all runs by `conclusion` value
- Count runs in each group
- Handle None conclusions (non-terminal runs)

**Example output structure:**
```python
conclusion_counts = {
    'success': 5,
    'failure': 3,
    'cancelled': 2,
    'skipped': 1,
    None: 2  # or 'pending' if we treat non-terminal separately
}
```

**Implementation notes:**
- Must iterate all runs from WorkflowRunService.list_runs()
- Group by run.conclusion field (str Enum or None)
- Count occurrences

### Requirement 2: Average Duration Seconds

**What to compute:**
1. **Overall average** — mean of all run durations (or filtered subset)
2. **Per-conclusion average** — mean duration for each conclusion group

**Calculation:**
- Sum all duration_seconds values
- Divide by count of runs
- Handle edge case: empty list (0 runs) → return 0 or None

**Example output:**
```python
duration_stats = {
    'overall_average': 45.5,
    'by_conclusion': {
        'success': 40.2,
        'failure': 55.3,
        'cancelled': 30.0,
        ...
    },
    'min_seconds': 5.0,      # Should have (global min)
    'max_seconds': 120.0,    # Should have (global max)
}
```

### Requirement 3: Average Number of Attempts per Run

**What to compute:**
- For each run, count its associated attempts
- Calculate mean attempts across all runs
- Include runs with 0 attempts

**Calculation:**
1. Get all runs from WorkflowRunService
2. For each run.id, query WorkflowAttemptService.filter_by_run_id(run.id)
3. Count attempts for that run
4. Average the counts: sum / total_runs

**Example:**
```python
attempts_stats = {
    'total_attempts': 12,
    'total_runs': 5,
    'average_attempts_per_run': 2.4,  # 12 / 5
    'runs_with_no_attempts': 1,
    'runs_with_attempts': 4,
}
```

### Requirement 4: Structured Report Object

**What to design:**
- A dataclass (not plain dict) to hold all statistics
- Fields for all computed metrics
- Optional: serialization methods for JSON output

**Proposed structure:**
```python
@dataclass
class WorkflowStatisticsReport:
    # Counts
    total_runs: int
    conclusion_counts: Dict[Optional[str], int]  # {conclusion_value: count}
    
    # Duration stats (runs)
    average_duration_seconds: float
    min_duration_seconds: float
    max_duration_seconds: float
    duration_by_conclusion: Dict[Optional[str], float]  # {conclusion: avg_duration}
    
    # Attempt stats
    total_attempts: int
    average_attempts_per_run: float
    runs_with_no_attempts: int
    runs_with_attempts: int
    
    # Metadata
    generated_at: datetime
    
    def to_dict(self) -> dict:
        """Serialize for JSON output"""
    
    @classmethod
    def from_services(...) -> WorkflowStatisticsReport:
        """Factory method to compute from services"""
```

### Requirement 5: CLI Exposure

**Current CLI structure (src/cli/workflow_cli.py):**
- Uses argparse with subcommands (add, list, detail, query-state, attempt)
- Each subcommand maps to a handler function in run_cli()

**What needs to be added:**
- New subcommand: `stats` or `report` or `statistics`
- Command-line flags: `--report` or `--stats` (alternate naming)
- Handler that calls statistics computation service
- Output formatting (human-readable or JSON)

**Example CLI usage:**
```bash
python -m src stats                    # Interactive: compute and display
python -m src --report                 # One-shot CLI: return JSON
python -m src report --format json     # JSON output
python -m src report --format text     # Human-readable output
```

### Requirement 6: Interactive Menu Exposure

**Current menu structure (src/cli/interactive_menu.py):**
- run_interactive() displays main menu
- _run_menu() shows options for runs
- _attempt_menu() shows options for attempts

**What needs to be added:**
- New main menu option: "View Statistics" or "Generate Report"
- Handler function that calls computation
- Display results in formatted output (table or summary)

**Example menu flow:**
```
Main Menu:
  1. Workflow Runs
  2. Workflow Attempts
  3. View Statistics      <- NEW
  4. Exit

Choice: 3
-> Computes stats for all runs/attempts
-> Displays summary in formatted output
-> Returns to main menu
```

---

## Key Findings

### 1. Data Is Available and Accessible

- WorkflowRunService.list_runs() provides all runs in memory
- WorkflowAttemptService.list_attempts() provides all attempts
- WorkflowAttemptService.filter_by_run_id(run_id) provides attempts per run
- No new data fetching mechanisms needed; use existing service methods

### 2. Duration and Attempt Data Is Already Stored

- Both WorkflowRun and WorkflowRunAttempt have `duration_seconds: float`
- WorkflowRunAttempt.run_id links to parent run
- No schema changes needed; statistics computation is pure calculation

### 3. Conclusion Field Handles Non-Terminal States

- WorkflowRun.conclusion is Optional[WorkflowConclusion]
- Can be None for non-terminal runs (status != COMPLETED)
- Statistics must handle None as a valid grouping key
- **Design choice:** Group None conclusions under "pending" or "incomplete" label for clarity

### 4. Service Layer Extension Location

- Create a new service or utility class for statistics computation
- Options:
  1. **New file:** `src/services/workflow_statistics_service.py` (follows pattern)
  2. **New file:** `src/utils/statistics_calculator.py` (lighter-weight utility)
  3. **Extend existing:** Add method to WorkflowRunService (not ideal; violates single responsibility)

**Recommendation:** Create `src/services/workflow_statistics_service.py` to keep architecture consistent.

### 5. CLI and Menu Need New Entry Points

**CLI changes (src/cli/workflow_cli.py):**
- Add new subparser in build_parser() for `stats` or `report` command
- Handle in run_cli() dispatch logic
- Output formatted results to stdout

**Menu changes (src/cli/interactive_menu.py):**
- Add new main menu option (after Runs/Attempts)
- Create handler function (e.g., _view_statistics())
- Format and display results

### 6. Report Object Should Be a Dataclass

- Matches existing pattern (WorkflowRun, WorkflowRunAttempt are dataclasses)
- Enables serialization/deserialization
- Type-safe fields
- Can add helper methods for formatting/display

---

## Ambiguities and Working Assumptions

### Ambiguity 1: How to Handle Non-Terminal Runs

**Ambiguity:** When grouping by conclusion, how should runs with `conclusion = None` (non-terminal) be displayed?
- Option A: Show as separate "None" group
- Option B: Label as "Incomplete" or "Pending"
- Option C: Include in statistics but note they are non-terminal

**Working Assumption:** 
- Include None conclusions in grouping with a label like "incomplete" or "pending" for clarity
- Keep internal representation as None for type safety
- Display formatting can show a human-readable label

### Ambiguity 2: Empty Runs Edge Case

**Ambiguity:** What should statistics return if there are zero runs?
- Option A: Return all zeros
- Option B: Return None or special "no data" object
- Option C: Return error

**Working Assumption:**
- Return report with count=0, average=0, min=None, max=None
- No error; graceful handling of empty data

### Ambiguity 3: Scope of "Per-Status" Statistics

**Task says "Could Have: Per-status breakdown"** — distinct from per-conclusion.
**Ambiguity:** What metrics per status?
- Option A: Count by status (similar to conclusion)
- Option B: Average duration by status
- Option C: Both

**Working Assumption:**
- This is "Could Have" so defer to later
- If implemented: parallel structure to per-conclusion stats
- Would require additional logic to group by both status and conclusion

### Ambiguity 4: Should Statistics Filter Incomplete Data?

**Ambiguity:** Should statistics include runs/attempts that are still in progress?
- Option A: Include all (regardless of status/conclusion)
- Option B: Exclude non-terminal (status != COMPLETED)
- Option C: Separate reports for complete vs. incomplete

**Working Assumption:**
- Include all runs and attempts (complete and incomplete)
- Non-terminal runs contribute to duration average and attempt counts
- Separation by completion status can be added as optional filter later

### Ambiguity 5: CLI Command Naming

**Task doesn't specify the exact command name.**
- Options: `stats`, `report`, `statistics`, `metrics`

**Working Assumption:**
- Use `report` as the subcommand name (shorter, clearer)
- Keep internal class name as WorkflowStatisticsReport or StatisticsReport

---

## Scope In/Out/Borderline

### IN: Must Implement

1. Count of runs grouped by conclusion value
2. Average duration_seconds (overall and per-conclusion)
3. Average number of attempts per run
4. Structured report object (dataclass)
5. Accessible via `python -m src` (both interactive menu and CLI)
6. Both interactive (menu) and one-shot (CLI flag) access modes

### IN: Should Have

1. Min/max duration_seconds in report
2. Dataclass structure (not plain dict)

### BORDERLINE: Could Have

1. Per-status breakdown of average duration
2. Additional metrics (stddev, percentiles, etc.)
3. Report export formats (JSON, CSV)
4. Ability to filter statistics (e.g., stats for branch=main only)

### OUT: Explicitly Excluded

1. Visualization (charts, graphs)
2. Database back-end (JSON storage only)
3. Real-time streaming statistics
4. Historical tracking (stats only for current data, not time-series)
5. External API integration

---

## Where Statistics Should Be Computed

### Option 1: Service Class (Recommended)

**File:** `src/services/workflow_statistics_service.py`

**Class:**
```python
class WorkflowStatisticsService:
    def __init__(
        self,
        workflow_run_service: WorkflowRunService,
        workflow_attempt_service: WorkflowAttemptService,
    ):
        self._run_service = workflow_run_service
        self._attempt_service = workflow_attempt_service
    
    def compute_report(self) -> WorkflowStatisticsReport:
        """Compute full statistics report from all runs/attempts"""
        ...
    
    def compute_report_for_runs(
        self,
        runs: List[WorkflowRun]
    ) -> WorkflowStatisticsReport:
        """Compute statistics for a filtered subset of runs"""
        ...
```

**Advantages:**
- Consistent with existing architecture (follows service pattern)
- Dependency injection of services
- Testable in isolation
- Can add caching/optimization later

**Disadvantages:**
- Slightly more code structure

### Option 2: Utility Module

**File:** `src/utils/statistics_calculator.py`

**Functions:**
```python
def compute_statistics(
    runs: List[WorkflowRun],
    attempts: List[WorkflowRunAttempt],
) -> WorkflowStatisticsReport:
    ...
```

**Advantages:**
- Simpler, lightweight
- No class wrapping needed
- Easier for one-shot usage

**Disadvantages:**
- Mixes utilities and domain logic
- Less aligned with existing service architecture

**Recommendation:** Use Option 1 (Service Class) for architectural consistency.

---

## Report Object Design

### Recommended Dataclass Structure

**File:** `src/models/workflow_statistics_report.py` (new)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class WorkflowStatisticsReport:
    # Run counts
    total_runs: int
    conclusion_counts: Dict[Optional[str], int]
    
    # Duration statistics
    average_duration_seconds: float
    min_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]
    duration_by_conclusion: Dict[Optional[str], float]
    
    # Attempt statistics
    total_attempts: int
    average_attempts_per_run: float
    runs_with_no_attempts: int
    runs_with_attempts: int
    
    # Metadata
    generated_at: datetime
    
    def to_dict(self) -> dict:
        """Serialize for JSON output"""
        return {
            'total_runs': self.total_runs,
            'conclusion_counts': {
                str(k) if k is not None else 'incomplete': v
                for k, v in self.conclusion_counts.items()
            },
            'average_duration_seconds': self.average_duration_seconds,
            'min_duration_seconds': self.min_duration_seconds,
            'max_duration_seconds': self.max_duration_seconds,
            'duration_by_conclusion': {
                str(k) if k is not None else 'incomplete': v
                for k, v in self.duration_by_conclusion.items()
            },
            'total_attempts': self.total_attempts,
            'average_attempts_per_run': self.average_attempts_per_run,
            'runs_with_no_attempts': self.runs_with_no_attempts,
            'runs_with_attempts': self.runs_with_attempts,
            'generated_at': self.generated_at.isoformat(),
        }
```

---

## Files That Need to Be Modified/Created

### New Files to Create

1. **src/models/workflow_statistics_report.py** (NEW)
   - Define WorkflowStatisticsReport dataclass
   - Add to_dict(), from_dict() methods

2. **src/services/workflow_statistics_service.py** (NEW)
   - Define WorkflowStatisticsService class
   - Implement compute_report() method
   - Use WorkflowRunService and WorkflowAttemptService

### Files to Modify

1. **src/cli/workflow_cli.py**
   - Add `report` subparser in build_parser()
   - Add handler in run_cli() for report command
   - Format and print results

2. **src/cli/interactive_menu.py**
   - Add _view_statistics() handler function
   - Add menu option to main menu or submenu
   - Format and display results

3. **src/__main__.py**
   - Initialize WorkflowStatisticsService
   - Pass to both CLI and interactive menu interfaces

4. **src/models/__init__.py**
   - Export WorkflowStatisticsReport

5. **src/services/__init__.py**
   - Export WorkflowStatisticsService

6. **tests/** (multiple new test files)
   - test_workflow_statistics_service.py
   - test_workflow_statistics_report.py

7. **artifacts/class_diagram.puml**
   - Add WorkflowStatisticsReport class
   - Add WorkflowStatisticsService class
   - Show relationships to other classes

---

## Entry Points to Modify

### src/__main__.py

**Current code:**
```python
def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    service = WorkflowRunService(storage)
    attempt_storage = WorkflowAttemptJsonStorage("artifacts/workflow_attempts.json")
    attempt_service = WorkflowAttemptService(attempt_storage)
    
    if len(sys.argv) == 1:
        run_interactive(service, attempt_service)
    else:
        run_cli(service, attempt_service)
```

**Changes needed:**
```python
def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    service = WorkflowRunService(storage)
    attempt_storage = WorkflowAttemptJsonStorage("artifacts/workflow_attempts.json")
    attempt_service = WorkflowAttemptService(attempt_storage)
    
    # NEW: Initialize statistics service
    stats_service = WorkflowStatisticsService(service, attempt_service)
    
    if len(sys.argv) == 1:
        run_interactive(service, attempt_service, stats_service)
    else:
        run_cli(service, attempt_service, stats_service)
```

### src/cli/workflow_cli.py

**Changes needed:**
1. Import WorkflowStatisticsService
2. Add `report` subparser in build_parser()
3. Add handler in run_cli() dispatch (elif ns.command == "report")
4. Format output (text or JSON)

**Example CLI command to support:**
```bash
python -m src report                      # Compute and display
python -m src report --format json        # JSON output
python -m src report --format text        # Human-readable output
```

### src/cli/interactive_menu.py

**Changes needed:**
1. Import WorkflowStatisticsService
2. Add _view_statistics() function
3. Add menu option in main menu or runs submenu
4. Format and display results

**Example menu option:**
```
Main Menu:
  1. Workflow Runs
  2. Workflow Attempts
  3. View Statistics        <- NEW
  4. Exit
```

---

## Calculation Details

### Conclusion Counts

**Algorithm:**
```python
def compute_conclusion_counts(runs: List[WorkflowRun]) -> Dict[Optional[str], int]:
    counts = {}
    for run in runs:
        conclusion_key = run.conclusion.value if run.conclusion else None
        counts[conclusion_key] = counts.get(conclusion_key, 0) + 1
    return counts
```

### Average Duration

**Algorithm:**
```python
def compute_average_duration(runs: List[WorkflowRun]) -> float:
    if not runs:
        return 0.0
    return sum(r.duration_seconds for r in runs) / len(runs)

def compute_duration_by_conclusion(runs: List[WorkflowRun]) -> Dict[Optional[str], float]:
    by_conclusion = {}
    for run in runs:
        conclusion_key = run.conclusion.value if run.conclusion else None
        if conclusion_key not in by_conclusion:
            by_conclusion[conclusion_key] = []
        by_conclusion[conclusion_key].append(run.duration_seconds)
    
    averages = {}
    for conclusion_key, durations in by_conclusion.items():
        averages[conclusion_key] = sum(durations) / len(durations) if durations else 0.0
    return averages
```

### Min/Max Duration

**Algorithm:**
```python
def compute_min_max_duration(runs: List[WorkflowRun]) -> (Optional[float], Optional[float]):
    if not runs:
        return None, None
    durations = [r.duration_seconds for r in runs]
    return min(durations), max(durations)
```

### Average Attempts per Run

**Algorithm:**
```python
def compute_average_attempts_per_run(
    runs: List[WorkflowRun],
    attempt_service: WorkflowAttemptService
) -> float:
    if not runs:
        return 0.0
    
    total_attempts = 0
    runs_with_attempts = 0
    
    for run in runs:
        attempts = attempt_service.filter_by_run_id(run.id)
        total_attempts += len(attempts)
        if attempts:
            runs_with_attempts += 1
    
    return total_attempts / len(runs) if runs else 0.0
```

---

## Summary of Changes

| Component | File | Type | Description |
|-----------|------|------|-------------|
| **Models** | src/models/workflow_statistics_report.py | NEW | Dataclass for report structure |
| **Services** | src/services/workflow_statistics_service.py | NEW | Computation logic |
| **CLI** | src/cli/workflow_cli.py | MODIFY | Add `report` subcommand |
| **Menu** | src/cli/interactive_menu.py | MODIFY | Add statistics menu option |
| **Entry** | src/__main__.py | MODIFY | Initialize statistics service |
| **Models Init** | src/models/__init__.py | MODIFY | Export WorkflowStatisticsReport |
| **Services Init** | src/services/__init__.py | MODIFY | Export WorkflowStatisticsService |
| **Tests** | tests/test_workflow_statistics_service.py | NEW | Unit tests for service |
| **Tests** | tests/test_workflow_statistics_report.py | NEW | Unit tests for dataclass |
| **Diagrams** | artifacts/class_diagram.puml | MODIFY | Add new classes |
| **Diagrams** | artifacts/use_case_diagram.puml | MODIFY | Add statistics use case |

---

## Current Data Model and How Runs/Attempts Are Stored

### WorkflowRun Storage Pattern

**Memory:**
- WorkflowRunService maintains `_runs: List[WorkflowRun]`
- Loaded from JSON storage on service initialization
- All modifications persisted via _persist() → storage.save()

**JSON Format (artifacts/workflow_runs.json):**
```json
[
  {
    "id": "run-123",
    "workflow_name": "CI",
    "branch": "main",
    "status": "completed",
    "conclusion": "success",
    "created_at": "2026-05-03T10:00:00",
    "updated_at": "2026-05-03T10:05:00",
    "run_number": 42,
    "commit_sha": "abc123...",
    "duration_seconds": 300.5
  }
]
```

### WorkflowRunAttempt Storage Pattern

**Memory:**
- WorkflowAttemptService maintains `_attempts: List[WorkflowRunAttempt]`
- Loaded from JSON storage on service initialization
- All modifications persisted via _persist() → storage.save()

**JSON Format (artifacts/workflow_attempts.json):**
```json
[
  {
    "id": "attempt-456",
    "run_id": "run-123",
    "attempt_number": 1,
    "status": "completed",
    "conclusion": "failure",
    "started_at": "2026-05-03T10:00:00",
    "completed_at": "2026-05-03T10:02:30",
    "duration_seconds": 150.0,
    "logs_url": "https://..."
  }
]
```

---

## Current CLI/Menu Structure

### CLI Command Structure (src/cli/workflow_cli.py)

**Subcommands:**
- `add` — Add new run (required flags: --name, --branch, --status; optional: --conclusion, --id, etc.)
- `list` — List runs with optional filters (--branch, --status, --conclusion, --duration-min, --duration-max, etc.)
- `detail <run_id>` — Get single run
- `query-state <run_id>` — Query terminal/running/successful/failed/cancelled flags
- `attempt add/list/detail/query-state` — Attempt management subcommands

**Entry:**
- Parser built in build_parser()
- Dispatch in run_cli() with ns.command if/elif chain
- No subcommand required yet; args must start with command name

### Interactive Menu Structure (src/cli/interactive_menu.py)

**Main Menu Options:**
1. Workflow Runs — submenu
2. Workflow Attempts — submenu
3. Exit

**Runs Submenu:**
1. Add workflow run
2. List all runs
3. Get run detail
4. Advanced filter runs
5. Query workflow state
6. Back

**Attempts Submenu:**
1. Add workflow attempt
2. List all attempts
3. Get attempt detail
4. Advanced filter attempts
5. Query attempt state
6. Back

**Control Flow:**
- run_interactive() loop displays menu
- User selects option (numeric input)
- Handler function called with service instances
- Returns to menu after handler completes

---

## Implementation Notes and Edge Cases

### Edge Case 1: Zero Runs

**Scenario:** No runs exist in the system
**Expected:** Report with:
- total_runs = 0
- All averages = 0.0
- Min/max = None
- conclusion_counts = {} (empty)

### Edge Case 2: All Runs Have None Conclusion

**Scenario:** All runs are non-terminal (in progress, queued, etc.)
**Expected:**
- conclusion_counts = {None: <count>}
- duration_by_conclusion = {None: <avg>}

### Edge Case 3: Runs Without Attempts

**Scenario:** Some runs have no associated attempts
**Expected:**
- total_attempts counted correctly
- average_attempts_per_run includes runs with 0 attempts
- runs_with_no_attempts > 0

### Edge Case 4: Runs With Different Attempt Counts

**Scenario:**
- Run A: 3 attempts
- Run B: 1 attempt
- Run C: 0 attempts
- Total: 4 runs, 4 attempts

**Expected:**
- average_attempts_per_run = 4 / 4 = 1.0
- runs_with_attempts = 2
- runs_with_no_attempts = 1

### Edge Case 5: Duration Edge Values

**Scenario:** Some durations are 0.0, some are very large
**Expected:**
- min_duration_seconds = 0.0
- max_duration_seconds = <max_value>
- average includes all values fairly

---

## Next Steps for Implementation

1. **Create WorkflowStatisticsReport dataclass** (src/models/)
2. **Create WorkflowStatisticsService class** (src/services/)
3. **Implement compute_report() with all calculations**
4. **Add CLI subcommand** (workflow_cli.py)
5. **Add interactive menu option** (interactive_menu.py)
6. **Wire services in __main__.py**
7. **Write comprehensive unit tests**
8. **Update class diagram**
9. **Test end-to-end via `python -m src`**

