# Analysis: WorkflowStatisticsService Implementation

## Task Summary

Implement `WorkflowStatisticsService` to compute aggregate statistics on workflow runs. The service must:

1. Accept `WorkflowRunService` in constructor
2. Provide a `compute()` method returning a structured report dataclass
3. Report must contain:
   - `count_by_conclusion: dict[WorkflowConclusion, int]` — Counts of runs grouped by conclusion type
   - `avg_duration_seconds: float` — Mean duration across all runs
   - `min_duration_seconds: float` — Minimum duration among all runs
   - `max_duration_seconds: float` — Maximum duration among all runs
   - `avg_attempts_per_run: float` — Mean attempts across all runs
4. Handle empty datasets with zeroed values
5. Include runs with zero attempts in `avg_attempts_per_run` calculation

---

## Current Architecture State

### Service Layer Pattern (Established)

The codebase establishes a clear service layer pattern for domain operations:

**WorkflowRunService** (`src/services/workflow_run_service.py`, 137 lines):
- Constructor: Takes `WorkflowJsonStorage` and loads runs into memory (`self._runs: List[WorkflowRun]`)
- Public methods: `add_workflow_run()`, `list_runs()`, `get_run_detail()`, `filter_by_*()`, `query()`
- Private method: `_persist()` to write changes back to storage
- No statistics/aggregation methods
- Uses in-memory data structures (List[WorkflowRun])

**AttemptService** (`src/services/attempt_service.py`, 53 lines):
- Constructor: Takes no arguments, initializes empty in-memory list (`self._attempts: List[WorkflowRunAttempt]`)
- Public methods: `create()` for storage, `get_by_run_id()` for retrieval
- Pure in-memory, no file I/O
- Provides sorted results (by attempt_number)

**WorkflowRunTracker** (`src/services/workflow_run_tracker.py`):
- Higher-level orchestration service
- Takes `WorkflowRunService` in constructor
- Provides convenience methods for tracking new runs

### Key Service Pattern Rules

1. **Constructor dependency injection** — Services receive dependencies (storage, other services) at init
2. **Lazy loading** — Data loaded once at init, kept in memory
3. **No external I/O** — Once loaded, all operations are in-memory
4. **Deterministic output** — Same inputs produce identical results
5. **Insertion-order preservation** — Lists maintain insertion order

---

## WorkflowRun Model

**File**: `src/models/workflow_run.py`

### Fields
```
id: str                                    # Unique identifier
workflow_name: str                         # Workflow name
branch: str                                # Git branch
status: WorkflowStatus                     # Enum: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING
conclusion: Optional[WorkflowConclusion]   # Enum: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE
created_at: datetime                       # When run was created (timezone-aware)
updated_at: Optional[datetime]             # When run was last updated
run_number: Optional[int]                  # GitHub run number
commit_sha: Optional[str]                  # Git commit SHA
duration_seconds: float = 0.0              # *** CRITICAL for statistics ***
```

### Critical Methods for Statistics
- `is_terminal()` — Returns True if status == COMPLETED
- `is_successful()`, `is_failed()`, `is_cancelled()` — Check conclusion against COMPLETED status

---

## WorkflowRunAttempt Model

**File**: `src/models/workflow_run_attempt.py`

### Fields
```
id: int                                    # Unique identifier
run_id: int                                # Foreign key to WorkflowRun
attempt_number: int                        # 1-based attempt count (1, 2, 3...)
status: str                                # Attempt status (string, not enum)
conclusion: str                            # Attempt conclusion (string, not enum)
created_at: datetime                       # When attempt was created (CEST timezone required)
duration_seconds: Optional[float] = None   # Optional attempt duration
```

### Key Constraints
- `attempt_number` must be > 0 (validated in `__post_init__`)
- `created_at` must use CEST timezone (UTC+2) only
- Supports round-trip serialization via `to_dict()` / `from_dict()`

---

## WorkflowConclusion Enum

**File**: `src/models/workflow_conclusion.py`

```
SUCCESS       = "success"
FAILURE       = "failure"
CANCELLED     = "cancelled"
SKIPPED       = "skipped"
TIMED_OUT     = "timed_out"
ACTION_REQUIRED = "action_required"
NEUTRAL       = "neutral"
STALE         = "stale"
```

**Significance**: `count_by_conclusion` must return counts keyed by these enum values. All 8 possible conclusions should be represented in any comprehensive report, but report only includes conclusions present in data.

---

## What WorkflowStatisticsService Must Implement

### 1. Report Dataclass (New)

**Name**: `WorkflowStatisticsReport` (or similar)  
**Location**: Either in `src/services/workflow_statistics_service.py` or new file `src/models/workflow_statistics_report.py`

**Fields**:
- `count_by_conclusion: dict[WorkflowConclusion, int]` — Maps conclusion enum to count
  - Example: `{WorkflowConclusion.SUCCESS: 5, WorkflowConclusion.FAILURE: 2}`
  - Only keys for conclusions present in data
  - Empty dict `{}` if no runs exist

- `avg_duration_seconds: float` — Mean of all runs' `duration_seconds`
  - Returns `0.0` if no runs or all have `duration_seconds = 0.0`
  - Precision: standard float (no rounding requirement)

- `min_duration_seconds: float` — Minimum of all runs' `duration_seconds`
  - Returns `0.0` if no runs exist
  - Could be `0.0` if all runs have that value

- `max_duration_seconds: float` — Maximum of all runs' `duration_seconds`
  - Returns `0.0` if no runs exist
  - Could be `0.0` if all runs have that value

- `avg_attempts_per_run: float` — Mean attempt count per run
  - **CRITICAL**: Includes runs with 0 attempts in denominator
  - If 3 runs have [1, 2, 0] attempts: average = (1+2+0)/3 = 1.0
  - Returns `0.0` if no runs exist
  - Requires `AttemptService` to query attempt counts

### 2. WorkflowStatisticsService Class

**Location**: `src/services/workflow_statistics_service.py`

**Constructor**:
```python
def __init__(self, workflow_run_service: WorkflowRunService) -> None:
    # Store the service reference
```

**Public Method**:
```python
def compute(self, attempt_service: Optional[AttemptService] = None) -> WorkflowStatisticsReport:
    # Get all runs from workflow_run_service
    # Compute statistics
    # Return populated report dataclass
```

**Method Design Notes**:
- `compute()` may optionally accept `attempt_service` for computing `avg_attempts_per_run`
- If `attempt_service` is None, `avg_attempts_per_run` should be `0.0` (or require it)
- Must handle empty datasets gracefully (no division by zero errors)
- Must handle runs with `conclusion = None` (only count terminal runs or skip)

---

## Integration Points

### WorkflowRunService Dependency
- Service holds internal `List[WorkflowRun]` (loaded from storage)
- No public method to get raw list, but `list_runs()` exists to get all
- Query method exists for filtering by duration, timestamp, attempts

### AttemptService Dependency
- Service holds internal `List[WorkflowRunAttempt]`
- `get_by_run_id(run_id: int)` returns sorted attempts for a run
- No single method to get all attempts; must iterate over all run IDs

### Timezone Awareness
- `WorkflowRun.created_at` is timezone-aware (variable timezones)
- `WorkflowRunAttempt.created_at` is CEST only (UTC+2)
- Statistics don't need timezone conversion, just duration metrics

---

## Design Patterns to Follow

### 1. In-Memory Computing
- No database queries or file I/O
- All computation happens on data already in service memory
- Single pass or light iteration over runs acceptable

### 2. Dataclass Report
- Use `@dataclass` decorator for report return type
- Makes report serializable and type-safe
- Pattern matches existing models (WorkflowRun, WorkflowRunAttempt)

### 3. Optional Dependencies
- `AttemptService` should be optional parameter to `compute()`
- If not provided, `avg_attempts_per_run` defaults to `0.0`
- No hard requirement for two services to be tightly coupled

### 4. Empty Dataset Handling
- No exceptions for empty data
- Return zeroed/default values
- Exception only if invalid parameters passed

---

## Edge Cases & Assumptions

### Edge Case: Runs with `conclusion = None`
- **Current state**: `WorkflowRun.conclusion` is `Optional[WorkflowConclusion]`
- **Behavior needed**: How to count partial/running workflows?
- **Assumption**: Only count COMPLETED runs in `count_by_conclusion`; running workflows excluded
- **Alternative**: Count by checking `is_terminal()` method first

### Edge Case: Zero Attempts
- **Behavior**: Runs with no attempts should count as 0 in `avg_attempts_per_run` calculation
- **Example**: 3 runs with [1, 2, 0] attempts → average = (1+2+0)/3 = 1.0
- **Requires**: Query all attempts, not just runs with attempts

### Edge Case: All Runs Have duration_seconds = 0.0
- **Behavior**: `min_duration_seconds = 0.0`, `max_duration_seconds = 0.0`, `avg_duration_seconds = 0.0`
- **Distinction**: Different from "no runs" case which also returns 0.0
- **Implication**: Cannot detect "missing data" vs "real zero" without extra field

### Naming Convention
- Model: `WorkflowStatisticsReport` (noun, what it is)
- Service: `WorkflowStatisticsService` (noun + Service, what role it plays)
- Method: `compute()` (verb, action it performs)

---

## File Structure Plan

### New Files Required
1. **`src/services/workflow_statistics_service.py`**
   - Contains `WorkflowStatisticsService` class
   - Contains `WorkflowStatisticsReport` dataclass (or import from models)

2. **`tests/services/test_workflow_statistics_service.py`** (optional but expected)
   - Test class initialization
   - Test `compute()` with empty data
   - Test `compute()` with mixed conclusions
   - Test duration calculations
   - Test attempts calculations

### Modified Files
1. **`src/services/__init__.py`**
   - Add import/export: `from .workflow_statistics_service import WorkflowStatisticsService`

2. **`artifacts/class_diagram.puml`**
   - Add `WorkflowStatisticsService` class box
   - Add `WorkflowStatisticsReport` dataclass box
   - Show relationships: `WorkflowStatisticsService → WorkflowRunService` (dependency)
   - Show relationships: `WorkflowStatisticsService → AttemptService` (optional)

---

## Summary of Key Findings

### Architecture
- **Pattern established**: Services with in-memory data, optional persistence
- **Dependency injection**: Services receive other services/storage in constructor
- **No file I/O**: All operations in-memory; no I/O except via passed-in storage

### Data Models
- **WorkflowRun**: Contains 10 fields; `duration_seconds` is critical
- **WorkflowRunAttempt**: Contains 7 fields; supports 1-N relationship with runs
- **WorkflowConclusion**: 8-value enum; must be key type for count_by_conclusion

### Service Requirements
1. Accept `WorkflowRunService` in constructor
2. Implement `compute(attempt_service: Optional[AttemptService]) -> WorkflowStatisticsReport`
3. Return populated dataclass with 5 aggregated fields
4. Handle empty datasets (return 0.0 values, empty dict)
5. Include zero-attempt runs in `avg_attempts_per_run` denominator

### No External Dependencies
- No new packages required
- No database calls
- No file I/O
- Uses only existing models and services
