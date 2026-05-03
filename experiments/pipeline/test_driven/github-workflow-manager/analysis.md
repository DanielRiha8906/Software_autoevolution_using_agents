# Analysis: Query Functionality for WorkflowRunService

## Task Summary

Implement query functionality in `WorkflowRunService` to filter workflow runs by:
1. **Duration range**: `min_duration` and `max_duration` filters on `duration_seconds` field
2. **Timestamp range**: `created_before` and `created_after` as timezone-aware datetimes
3. **Attempt presence**: `has_attempts=True` for runs with ≥1 attempts, `=False` for no attempts

The implementation must integrate with `AttemptService` to check attempt counts per run.

---

## Current State of WorkflowRunService

### Location
- **File**: `/src/services/workflow_run_service.py`
- **Lines of code**: 38 lines

### Existing Methods
| Method | Signature | Purpose |
|--------|-----------|---------|
| `__init__` | `(storage: WorkflowJsonStorage)` | Initialize with storage backend, load runs into memory |
| `_persist` | `() -> None` | Write current runs list to storage |
| `add_workflow_run` | `(run: WorkflowRun) -> WorkflowRun` | Add new run, raise ValueError if duplicate id |
| `list_runs` | `() -> List[WorkflowRun]` | Return all runs |
| `get_run_detail` | `(run_id: str) -> Optional[WorkflowRun]` | Fetch single run by id |
| `filter_by_branch` | `(branch: str) -> List[WorkflowRun]` | Filter by branch field |
| `filter_by_status` | `(status: WorkflowStatus) -> List[WorkflowRun]` | Filter by status enum |
| `filter_by_conclusion` | `(conclusion: WorkflowConclusion) -> List[WorkflowRun]` | Filter by conclusion enum |

### Architecture Pattern
- **In-memory storage**: Loads all runs into `self._runs: List[WorkflowRun]` at init
- **Lazy evaluation**: Each filter returns a new list (no query optimization)
- **Persistence**: All mutations call `self._persist()` to update storage
- **No transactions**: Single-threaded, no concurrency handling

### Data Available for Filtering
From `WorkflowRun` dataclass:
```
id: str
workflow_name: str
branch: str
status: WorkflowStatus
conclusion: Optional[WorkflowConclusion]
created_at: datetime               # <-- Available for timestamp filtering
updated_at: Optional[datetime]
run_number: Optional[int]
commit_sha: Optional[str]
duration_seconds: float = 0.0      # <-- Available for duration filtering
```

---

## What Query Method Signature Should Be

### Proposed Method: `query()`

A single composite query method that accepts optional filter parameters:

```python
def query(
    self,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    has_attempts: Optional[bool] = None,
    attempt_service: Optional[AttemptService] = None,
) -> List[WorkflowRun]:
    """
    Filter workflow runs by duration, timestamp, and attempt presence.
    
    Args:
        min_duration: Minimum duration_seconds (inclusive). None = no minimum.
        max_duration: Maximum duration_seconds (inclusive). None = no maximum.
        created_after: Runs created strictly after this datetime (exclusive).
                       Expected to be timezone-aware.
        created_before: Runs created strictly before this datetime (exclusive).
                        Expected to be timezone-aware.
        has_attempts: If True, return runs with ≥1 attempts.
                      If False, return runs with 0 attempts.
                      If None, ignore attempt count.
        attempt_service: Required if has_attempts is not None.
                         Provides access to attempt data.
    
    Returns:
        List of WorkflowRun objects matching all specified filters.
        Returns empty list if no matches found.
        Filters are combined with AND logic (all must match).
    
    Raises:
        ValueError: If has_attempts is not None but attempt_service is None.
        ValueError: If created_after >= created_before (both provided).
        TypeError: If datetime arguments are not timezone-aware.
    """
```

### Alternative: Multiple Specialized Methods

Instead of one composite method, could have separate methods:
- `filter_by_duration(min_duration, max_duration)`
- `filter_by_created_range(created_after, created_before)`
- `filter_by_attempt_presence(has_attempts, attempt_service)`

**Recommendation**: Single `query()` method is cleaner and follows principle of least API surface. Specialized methods can be added later if needed. The task doesn't specify which approach, so a single composite method is more pragmatic.

---

## How to Query Associated Attempts from AttemptService

### AttemptService Interface
```python
class AttemptService:
    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """
        Returns all attempts for a run_id, sorted by attempt_number ascending.
        Returns empty list if no attempts found.
        """
```

### Key Observations
1. **ID type mismatch**: `WorkflowRun.id` is `str`, but `AttemptService.get_by_run_id()` expects `int`
   - This is a **critical impedance mismatch** that needs resolution
   - Two options:
     - Convert `run.id` to int when querying (assumes id is numeric string)
     - Query by string id and have AttemptService handle conversion
     - Accept that some runs may have non-numeric ids and skip attempt filtering

2. **Semantic check for has_attempts**:
   ```python
   attempts = attempt_service.get_by_run_id(run_id)
   has_attempts = len(attempts) >= 1  # or: has_attempts = bool(attempts)
   ```

3. **No persistence**: AttemptService is in-memory only. At initialization of WorkflowRunService, attempts may not be loaded yet.

### Proposed Integration Code Pattern
```python
def query(
    self,
    ...,
    has_attempts: Optional[bool] = None,
    attempt_service: Optional[AttemptService] = None,
) -> List[WorkflowRun]:
    
    results = list(self._runs)  # Start with all runs
    
    # Apply filters...
    
    # Attempt presence filter (last, since it requires external service)
    if has_attempts is not None:
        if attempt_service is None:
            raise ValueError("attempt_service required when filtering by has_attempts")
        
        filtered = []
        for run in results:
            try:
                attempts = attempt_service.get_by_run_id(int(run.id))
                run_has_attempts = len(attempts) >= 1
                if run_has_attempts == has_attempts:
                    filtered.append(run)
            except (ValueError, TypeError):
                # If run.id cannot convert to int, skip this run
                # (or include/exclude based on interpretation of has_attempts)
                pass
        results = filtered
    
    return results
```

---

## Edge Cases and Considerations

### Timezone Handling
**Current state of created_at in WorkflowRun**:
- Type: `datetime` (may or may not be timezone-aware)
- Serialized: Via `.isoformat()` in `to_dict()` and `datetime.fromisoformat()` in `from_dict()`
- **Problem**: No guarantee that loaded datetimes are timezone-aware

**Issues**:
1. Comparisons with timezone-aware arguments will fail if `created_at` is naive (no tzinfo)
2. Test fixtures use `datetime.now(timezone.utc)` (aware), but JSON roundtrip may lose tzinfo

**Handling strategy**:
- Document requirement that `created_at` must be timezone-aware
- Validate input datetime arguments are timezone-aware
- If `created_at` is naive, either:
  - Raise `TypeError` (strict interpretation)
  - Assume UTC and proceed (lenient, may cause bugs)
  - Filter such runs out (conservative)

**Recommendation**: Raise `TypeError` if comparison is attempted with naive datetime.

### Duration Range Filtering
**Edge cases**:
- `min_duration=0, max_duration=0`: Should match runs with exactly 0 seconds
- `min_duration=10.5, max_duration=10.5`: Should match runs with exactly 10.5 seconds
- `min_duration=None, max_duration=5.0`: All runs with duration ≤ 5.0
- Negative durations: `WorkflowRun.__post_init__()` already rejects these, so not a concern

**Handling**:
```python
if min_duration is not None and run.duration_seconds < min_duration:
    continue
if max_duration is not None and run.duration_seconds > max_duration:
    continue
```

### Timestamp Range Filtering
**Edge cases**:
- Both `created_after` and `created_before` specified: Verify range is valid (after < before)
- `created_after` only: Match all runs created after this point
- `created_before` only: Match all runs created before this point
- `created_after == created_before`: Should match zero runs (exclusive bounds)

**Inclusive vs exclusive bounds**:
- Task says "timestamp range" but doesn't specify inclusive/exclusive
- Typical interpretation: `created_after < created_at < created_before` (exclusive on both ends)
- More intuitive for users: `created_after <= created_at <= created_before` (inclusive)
- **Assumption**: Use **exclusive bounds** (`<` and `>`) to align with common query patterns

**Validation**:
```python
if created_after is not None and created_before is not None:
    if created_after >= created_before:
        raise ValueError("created_after must be strictly before created_before")
```

### Attempt Presence with ID Conversion
**Problem**: `WorkflowRun.id` is `str`, `get_by_run_id()` expects `int`

**Known scenarios**:
1. Run ID is numeric string (e.g., "123") → `int(run.id)` succeeds
2. Run ID is non-numeric (e.g., "abc") → `int(run.id)` raises `ValueError`
3. Attempting to match based on string vs int IDs

**Options for handling**:
1. **Strict**: Reject any non-numeric run IDs with clear error message
2. **Lenient**: Catch `ValueError` during conversion, exclude that run from attempt filtering
3. **Hybrid**: Log warning and exclude run

**Recommendation**: Option 2 (lenient with silent exclusion), because:
- Prevents task failure due to malformed data
- Run is still returned; just not filtered by attempt presence
- Aligns with defensive programming in service layer

### Empty Results
- If no runs match all criteria, return empty list `[]` (not an error)
- Callers must handle empty results naturally

### Parameter Validation

**Validation order** (fail fast):
1. Check that datetime arguments are timezone-aware (if provided)
2. Check that `created_after < created_before` (if both provided)
3. Check that `min_duration <= max_duration` (if both provided)
4. Check that `has_attempts` filter has required `attempt_service`
5. Apply filters

---

## Implementation Checklist

### Core Functionality
- [ ] Single `query()` method with all filter parameters
- [ ] Duration filtering: `min_duration` and `max_duration` (inclusive)
- [ ] Timestamp filtering: `created_after` and `created_before` (exclusive)
- [ ] Attempt presence filtering: `has_attempts` with `attempt_service` integration
- [ ] AND logic: All filters applied together

### Error Handling
- [ ] Raise `ValueError` if `has_attempts` is not None but `attempt_service` is None
- [ ] Raise `ValueError` if `created_after >= created_before`
- [ ] Raise `ValueError` if `min_duration > max_duration`
- [ ] Raise `TypeError` if datetime arguments are not timezone-aware
- [ ] Raise `TypeError` if `created_at` in WorkflowRun is naive and comparison is attempted

### Edge Cases
- [ ] Handle non-numeric run IDs gracefully (exclude from attempt filtering, don't crash)
- [ ] Return empty list if no matches found
- [ ] All filters optional (None = no filtering on that dimension)
- [ ] Duration range boundary cases (0.0, equal min/max)
- [ ] Timestamp boundary cases (exclusive bounds, equal timestamps)

### Integration
- [ ] No changes to existing filter methods
- [ ] No changes to storage or persistence layer
- [ ] Accepts `AttemptService` as optional parameter (dependency injection)
- [ ] Returns `List[WorkflowRun]` (consistent with existing methods)

### Testing (Assumed)
- Calls to `query()` with each filter individually
- Calls to `query()` with multiple filters combined
- Boundary conditions (min=max, exclusive bounds)
- Empty result sets
- Invalid parameter combinations (should raise)
- Non-numeric run IDs with attempt filtering
- Timezone-aware datetime requirement

---

## Related Code References

### WorkflowRun Model
**File**: `/src/models/workflow_run.py`

Key fields for filtering:
- `created_at: datetime` (line 16)
- `duration_seconds: float` (line 20)

### AttemptService Interface
**File**: `/src/services/attempt_service.py`

```python
def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
    """Returns all attempts for a run_id, sorted by attempt_number."""
```

### Existing Filter Pattern
**File**: `/src/services/workflow_run_service.py` (lines 30-37)

```python
def filter_by_branch(self, branch: str) -> List[WorkflowRun]:
    return [r for r in self._runs if r.branch == branch]
```

All existing filters use list comprehension; `query()` should follow similar pattern.

---

## Summary

**What needs to be added**:
- Single `query()` method in `WorkflowRunService` class
- Takes 6 optional parameters: `min_duration`, `max_duration`, `created_after`, `created_before`, `has_attempts`, `attempt_service`
- Returns filtered list of `WorkflowRun` objects
- Applies AND logic across all filters
- Validates inputs (datetime timezone-aware, date range validity, attempt_service presence)
- Handles edge cases gracefully (non-numeric IDs, naive datetimes, empty results)

**Critical integration points**:
- Must work with `AttemptService.get_by_run_id()` despite ID type mismatch
- Requires caller to pass `AttemptService` instance for attempt filtering
- Should not modify existing methods or storage layer

**Key ambiguity requiring assumption**:
- Timestamp range bounds: Using **exclusive bounds** (`created_after < created_at < created_before`)
- ID mismatch handling: Using **lenient exclusion** (skip non-numeric IDs from attempt filtering)
