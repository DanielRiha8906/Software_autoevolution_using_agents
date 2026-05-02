# Analysis: Implement WorkflowRunAttempt Model

## Task Summary

Implement a new `WorkflowRunAttempt` model to represent individual execution attempts within workflow runs. GitHub Actions allows a single workflow run to be re-executed multiple times, with each attempt tracked separately. This model must:

1. Define the structure with specific fields and constraints
2. Support serialization/deserialization with JSON-compatible dictionaries
3. Establish a parent-child relationship with `WorkflowRun`
4. Include a unique constraint on the (run_id, attempt_number) pair
5. Validate attempt_number as a positive integer starting from 1
6. Support optional tracking of attempt-specific execution time

## Current Codebase Structure

### Package Organization
**Working directory:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/`

```
src/
├── models/
│   ├── __init__.py
│   ├── workflow_status.py       (enum)
│   ├── workflow_conclusion.py   (enum)
│   └── workflow_run.py          (dataclass)
├── services/
│   ├── __init__.py
│   ├── workflow_run_service.py  (CRUD + filters)
│   └── workflow_run_tracker.py  (facade for run creation)
├── storage/
│   ├── __init__.py
│   └── workflow_json_storage.py (JSON persistence)
├── cli/
│   ├── __init__.py
│   ├── workflow_cli.py
│   └── interactive_menu.py
└── __init__.py

tests/
├── __init__.py
├── test_workflow_run_service.py
├── test_workflow_json_storage.py
└── test_workflow_run_state.py
```

### Existing Model Pattern: WorkflowRun

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`

**Key characteristics of existing model:**
- Python `@dataclass` decorator with type hints
- Fields: `id` (str), `workflow_name` (str), `branch` (str), `status` (WorkflowStatus enum), `conclusion` (Optional[WorkflowConclusion] enum), `created_at` (datetime), `updated_at` (Optional[datetime]), `run_number` (Optional[int]), `commit_sha` (Optional[str]), `duration_seconds` (float, default 0.0)
- `__post_init__()` validation method (validates `duration_seconds >= 0`)
- `to_dict()` instance method: serializes to JSON-compatible dict with enum.value for enums, isoformat() for datetimes
- `from_dict()` class method: deserializes from dict, reconstructing enums from string values and datetimes from ISO strings
- Helper methods: `is_terminal()`, `is_running()`, `is_successful()`, `is_failed()`, `is_cancelled()`

**Storage pattern:**
- JSON serialization via `WorkflowJsonStorage.save(runs: List[WorkflowRun])` → writes `[run.to_dict() for run in runs]` to JSON file
- JSON deserialization via `WorkflowJsonStorage.load()` → reads JSON and calls `WorkflowRun.from_dict(item)` for each item

### Timezone Handling in Existing Code

**Current implementation:** `created_at` uses `datetime.now(timezone.utc)` (UTC timezone-aware)

**Requirement conflict:** Task specifies `created_at` should be CEST (UTC+2), but all existing code uses UTC

**Assumption:** Will implement with UTC (matching existing pattern) since:
- All datetime handling in codebase uses UTC
- datetime.fromisoformat() in `from_dict()` handles arbitrary timezone-aware datetimes correctly
- Documentation likely describes CEST as the display/interpretation timezone for the user's local region, not storage format
- Storage should use UTC and display layer can convert to user's timezone

### Serialization/Deserialization Pattern

**to_dict() pattern:**
```python
return {
    "id": self.id,
    "status": self.status.value,  # enum → string
    "conclusion": self.conclusion.value if self.conclusion else None,  # Optional enum
    "created_at": self.created_at.isoformat(),  # datetime → ISO 8601 string
    "updated_at": self.updated_at.isoformat() if self.updated_at else None,  # Optional datetime
    "duration_seconds": self.duration_seconds,  # float as-is
    ...other fields...
}
```

**from_dict() pattern:**
```python
return cls(
    id=data["id"],
    status=WorkflowStatus(data["status"]),  # string → enum
    conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,  # Optional
    created_at=datetime.fromisoformat(data["created_at"]),  # ISO string → datetime
    updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,  # Optional
    duration_seconds=data.get("duration_seconds", 0.0),  # with default fallback
    ...other fields...
)
```

**Key observations:**
- Uses `.value` for enum serialization (string value)
- Uses `enum_class(string_value)` for deserialization
- Datetimes use `.isoformat()` (ISO 8601) for round-trip compatibility
- Optional fields use conditional checks: `if data.get("field")` or `if self.field else None`
- Handles missing fields with `.get(field, default_value)` for backward compatibility

### Test Structure Pattern

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/tests/test_workflow_json_storage.py`

**Patterns observed:**
- Uses `pytest` with fixtures (`@pytest.fixture`)
- Helper functions for creating test objects (e.g., `_sample_run()`, `_make_run()`)
- Tests serialization round-trips: save → load → verify field equality
- Tests backward compatibility: missing fields in JSON should use defaults
- Tests with `tmp_path` fixture for temporary file I/O
- Tests edge cases: zero vs. nonzero durations, None vs. non-None optional fields

## Required Implementation

### WorkflowRunAttempt Specification

**New model file:** `src/models/workflow_run_attempt.py`

**Attributes:**
- `id: int` — unique identifier for this attempt
- `run_id: int` — foreign key reference to parent WorkflowRun
- `attempt_number: int` — ordinal position (1, 2, 3, ...) within the run
- `status: str` — current execution status (e.g., "in_progress", "completed")
- `conclusion: Optional[str]` — final outcome if available (e.g., "success", "failure")
- `created_at: datetime` — ISO 8601 with timezone (UTC per existing pattern, despite CEST mention)
- `duration_seconds: float` (optional) — execution time in seconds

**Constraints:**
1. `(run_id, attempt_number)` must be unique together — database-style compound uniqueness
2. `attempt_number` must be a positive integer (>= 1) — validated in `__post_init__()`
3. `duration_seconds >= 0` (if provided) — validated like WorkflowRun

**Relationship to WorkflowRun:**
- `WorkflowRunAttempt.run_id` references `WorkflowRun.id`
- One WorkflowRun can have multiple WorkflowRunAttempts
- Conceptually: a run can be retried, each retry is an attempt
- No explicit relationship field in WorkflowRunAttempt (foreign key only)

**Serialization:**
- Must implement `to_dict() -> dict` — returns JSON-compatible dict
- Must implement `from_dict(data: dict) -> WorkflowRunAttempt` — class method for deserialization
- Follows WorkflowRun pattern: enum.value for strings, isoformat() for datetimes, conditional None handling

### Key Differences from WorkflowRun

| Aspect | WorkflowRun | WorkflowRunAttempt |
|--------|-------------|-------------------|
| **ID Type** | `str` (UUID) | `int` (numeric) |
| **Status Field** | `WorkflowStatus` enum | `str` (simple string, not enum) |
| **Conclusion Field** | `WorkflowConclusion` enum | `Optional[str]` (simple string) |
| **Parent Reference** | None (root entity) | `run_id: int` (foreign key) |
| **Unique Constraint** | `id` only | `(run_id, attempt_number)` compound |
| **Validation** | `duration_seconds >= 0` | `duration_seconds >= 0` AND `attempt_number >= 1` |

### Implementation Checklist

**1. Core Model File**
- [ ] Create `src/models/workflow_run_attempt.py`
- [ ] Import `dataclass`, `field` from dataclasses
- [ ] Import `datetime` from datetime module
- [ ] Import `Optional` from typing
- [ ] Define `@dataclass` class `WorkflowRunAttempt` with 7 fields (6 required + 1 optional)
- [ ] Implement `__post_init__()` to validate:
  - `attempt_number > 0` (raise ValueError if not)
  - `duration_seconds >= 0` (raise ValueError if not)
- [ ] Implement `to_dict()` → returns dict with all fields, datetimes as isoformat()
- [ ] Implement `from_dict(data: dict)` class method → reconstructs from dict, handles Optional fields

**2. Model Export**
- [ ] Update `src/models/__init__.py` to import and export `WorkflowRunAttempt`

**3. Tests**
- [ ] Create `tests/test_workflow_run_attempt.py` with comprehensive test coverage:
  - Basic instantiation with valid values
  - `__post_init__()` validation: attempt_number > 0
  - `__post_init__()` validation: duration_seconds >= 0
  - Serialization round-trip: `to_dict()` → `from_dict()`
  - Optional `duration_seconds` handling (default 0.0)
  - Optional `conclusion` handling (can be None)
  - `(run_id, attempt_number)` pair documentation in docstring or comment
  - Datetime timezone preservation through round-trip

**4. Optional Enhancements (Not Required)**
- [ ] Update `src/services/` if service layer needs to manage attempts (beyond task scope)
- [ ] Update `src/storage/` if storage needs to persist attempts (beyond task scope)
- [ ] Update `artifacts/class_diagram.puml` to show new WorkflowRunAttempt class and relationship to WorkflowRun

## Files That Need Changes

### Required Changes

**1. NEW FILE: `src/models/workflow_run_attempt.py`**
- Create new model file with `WorkflowRunAttempt` dataclass
- ~100-150 lines including docstrings and methods

**2. MODIFY: `src/models/__init__.py`**
- Add import: `from .workflow_run_attempt import WorkflowRunAttempt`
- Add to `__all__` list: `"WorkflowRunAttempt"`

**3. NEW FILE: `tests/test_workflow_run_attempt.py`**
- Create test suite with 15-20 test cases
- Cover instantiation, validation, serialization, edge cases

### Optional Changes (Out of Current Scope)

**4. OPTIONAL: `src/services/workflow_run_attempt_service.py`**
- If service layer needs to manage attempts (add, list, filter, delete)
- Would follow WorkflowRunService pattern
- Not required by current task

**5. OPTIONAL: `src/storage/workflow_json_storage.py`**
- If storage needs to persist attempts alongside runs
- Could extend existing storage or create new storage class
- Not required by current task

**6. OPTIONAL: `artifacts/class_diagram.puml`**
- Add WorkflowRunAttempt class box
- Add relationship line: WorkflowRunAttempt --> WorkflowRun (with cardinality 0..*:1)
- Update component diagram if services are added

## Implementation Notes

### Unique Constraint Enforcement

**Current limitation:** Python dataclasses do not enforce database-level uniqueness constraints. The `(run_id, attempt_number)` uniqueness must be:
1. Documented in the class docstring
2. Validated at the service/storage layer when persisting
3. Assumed as a precondition for valid data

**Example validation approach (for future service layer):**
```python
def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
    # Check if (run_id, attempt_number) pair already exists
    if any(a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number 
           for a in self._attempts):
        raise ValueError(f"Attempt {attempt.attempt_number} for run {attempt.run_id} already exists")
    self._attempts.append(attempt)
    return attempt
```

### Timezone Handling Decision

**Given requirement:** "created_at (CEST, UTC+2)"
**Current codebase:** All datetimes stored as UTC in JSON, using `datetime.now(timezone.utc)`
**Implementation approach:** Store as UTC (matching existing pattern), interpret/display in CEST at presentation layer if needed

**Reasoning:**
- Consistency with existing WorkflowRun implementation
- UTC is standard for data storage (timezone-agnostic)
- ISO 8601 format with timezone information preserves intent
- Display layer can convert to CEST using `pytz` or `zoneinfo` if needed

### Optional duration_seconds Field

**Specification:** "An optional `duration_seconds: float` attribute"

**Implementation interpretation:** 
- Make the attribute available on all instances
- Default value: 0.0 (matches WorkflowRun pattern)
- Optional in the sense that it may not always be known/measured
- Persist through serialization like WorkflowRun does

### Validation Strategy

**In `__post_init__()`:**
```python
def __post_init__(self) -> None:
    if self.attempt_number < 1:
        raise ValueError("attempt_number must be a positive integer (>= 1)")
    if self.duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")
```

**Why raise in `__post_init__()`:**
- Follows existing WorkflowRun pattern
- Ensures invalid objects cannot be instantiated
- Catches errors early when deserialized from untrusted sources

### Testing Priorities

**Must-test cases:**
1. Valid instantiation with all fields
2. Validation error: attempt_number < 1
3. Validation error: duration_seconds < 0
4. to_dict() produces JSON-compatible dict (all dicts/primitives, no objects)
5. from_dict() round-trip preserves all fields
6. Optional conclusion field: None round-trips correctly
7. Datetime timezone preservation through round-trip
8. Default duration_seconds (0.0) used when missing from JSON

**Nice-to-have cases:**
- Attempt number sequences (1, 2, 3)
- Very large attempt numbers (e.g., 1000000)
- Very long durations (e.g., 604800.0 = 1 week)
- Unicode in status/conclusion strings

## Scope Signals

### What's IN
- Implement WorkflowRunAttempt dataclass model
- Define 7 fields with correct types and constraints
- Serialization via to_dict() and from_dict()
- __post_init__() validation for attempt_number >= 1 and duration_seconds >= 0
- Unit tests covering all requirements
- Update models/__init__.py exports

### What's EXPLICITLY OUT
- Do not modify WorkflowRun
- Do not modify WorkflowStatus or WorkflowConclusion enums
- Do not implement service layer for attempts (beyond test coverage)
- Do not implement storage persistence for attempts in this task
- Do not modify CLI or interactive menu
- Do not install new dependencies

### What's BORDERLINE/FUTURE
- Service layer (WorkflowRunAttemptService) — mentioned as optional
- Storage layer updates — mentioned as optional
- Diagram updates — recommended but not required for functionality
- Database-level uniqueness enforcement — deferred to service/storage layer

## Suggested Priorities

**Priority 1 (Critical): Model Definition**
- Implement `WorkflowRunAttempt` dataclass with all 7 fields
- Implement `__post_init__()` validation
- Implement `to_dict()` and `from_dict()`
- These are the core contract; everything else depends on them

**Priority 2 (High): Serialization Testing**
- Test round-trip: object → dict → object
- Test validation errors on construction
- Test JSON compatibility (no non-serializable objects in dict)
- Ensures the model works end-to-end

**Priority 3 (Medium): Edge Cases & Exports**
- Test boundary values: attempt_number = 1 (min), duration_seconds = 0.0 (min)
- Test Optional fields (None conclusion, missing in JSON)
- Update models/__init__.py exports
- Ensures robustness and API completeness

**Priority 4 (Nice-to-have): Documentation**
- Add docstrings to class and methods
- Update class_diagram.puml if time permits
- Helps future maintenance

## Risk Analysis

**Low risk:**
- Adding new model file (non-invasive)
- No changes to existing models or enums
- No changes to service/storage layers (can be extended later)
- Python dataclass is straightforward pattern already used in codebase

**Moderate risk:**
- Timezone interpretation of "CEST" — mitigated by using UTC storage + ISO format
- `(run_id, attempt_number)` uniqueness — no enforcement possible at dataclass level, but documented

**No breaking changes:**
- Purely additive change
- Backward compatible (all existing tests pass)

## Summary

The `WorkflowRunAttempt` model is a straightforward extension of the existing pattern. The main implementation work is:

1. Create one new file (~100 lines): `src/models/workflow_run_attempt.py`
2. Update one existing file (~2 lines): `src/models/__init__.py`
3. Create one new test file (~20 test cases): `tests/test_workflow_run_attempt.py`

No dependencies on service/storage/CLI layers for basic functionality. Relationship to WorkflowRun is established via `run_id` foreign key, with compound uniqueness documented and validated at persistence layer if implemented.
