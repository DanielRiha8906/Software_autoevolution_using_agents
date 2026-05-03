# Analysis: WorkflowRunAttempt Domain Object Implementation

## Current Codebase State

### Existing Structure
- **Models directory**: `/src/models/` contains three existing domain objects:
  - `workflow_run.py`: WorkflowRun dataclass with 9 fields + methods
  - `workflow_status.py`: WorkflowStatus enum (6 values)
  - `workflow_conclusion.py`: WorkflowConclusion enum (8 values)
- **Models are exported** via `/src/models/__init__.py`
- **Patterns established**: Dataclasses with `@dataclass`, `__post_init__()` validation, `to_dict()`, and `from_dict()` serialization

### No WorkflowRunAttempt Yet
- File does not exist: `/src/models/workflow_run_attempt.py`
- Not imported in `/src/models/__init__.py`

## Existing Domain Model Patterns

### WorkflowRun Pattern (Key Reference)
```python
@dataclass
class WorkflowRun:
    # Fields with type hints
    id: str
    workflow_name: str
    branch: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: Optional[datetime]
    run_number: Optional[int]
    commit_sha: Optional[str]
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate that duration_seconds is not negative."""
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

    def to_dict(self) -> dict:
        # Serializes enum.value, converts datetime to isoformat()
        # Handles None values explicitly

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        # Enum fields reconstructed via enum(data["field"])
        # datetime.fromisoformat() for datetime fields
        # .get() with defaults for optional fields
```

### Key Implementation Notes from WorkflowRun
1. Validation via `__post_init__()`
2. Enums stored as `.value` strings in dict
3. datetime serialization via `.isoformat()` and `datetime.fromisoformat()`
4. Optional fields checked with `.get()` and None fallback
5. Float fields default to 0.0 when missing in from_dict

## Exact Requirements from Test Suite

### Field Definitions (from _attempt helper)
| Field | Type | Required | Constraints | Default |
|-------|------|----------|-------------|---------|
| id | int | Yes | No validation shown | N/A |
| run_id | int | Yes | No validation shown | N/A |
| attempt_number | int | Yes | Must be > 0 (≥ 1) | N/A |
| status | str | Yes | No enum constraint shown in tests | N/A |
| conclusion | str | Yes | No enum constraint shown in tests | N/A |
| created_at | datetime | Yes | CEST timezone ONLY (UTC+2) | N/A |
| duration_seconds | float | No | Optional field | None or 0.0 |

### Validation Requirements

**1. attempt_number validation (test_attempt_number_must_be_positive)**
- Must reject attempt_number ≤ 0
- Should raise Exception (ValueError recommended, matching WorkflowRun pattern)
- Validation in `__post_init__()`

**2. created_at timezone validation (test_created_at_must_use_cest)**
- Must reject any timezone except CEST
- CEST = timezone(timedelta(hours=2))
- Must raise Exception if timezone is not CEST
- Test explicitly checks rejection of timezone.utc

**3. created_at timezone preservation (test_created_at_round_trips_as_cest)**
- After `to_dict()` and `from_dict()` roundtrip
- Restored object's `created_at.tzinfo` must equal CEST
- This means from_dict() must convert parsed datetime to CEST timezone

**4. duration_seconds optionality (test_optional_duration_seconds, test_duration_seconds_defaults_to_none_or_zero)**
- May be omitted from constructor call
- Defaults to None OR 0.0 (test checks: `is None or == 0.0`)
- Can accept float values like 5.5
- Test shows: `_attempt()` without duration_seconds, then checks default

### Serialization Requirements (test_serializes_to_dict, test_round_trips_via_dict)
- `to_dict()` method must exist
- Must include all fields: id, run_id, attempt_number, status, conclusion, created_at, duration_seconds
- `from_dict()` class method must exist
- Must reconstruct object with all fields matching original
- Round-trip via dict preserves id, run_id, attempt_number, created_at, etc.

## Ambiguities and Assumptions

### 1. Enum Types for status and conclusion
**Ambiguity**: Test uses strings ("completed", "success") but doesn't show if these should be Enum types like WorkflowStatus/WorkflowConclusion.

**Working assumption**: Since tests use plain strings and don't import any status/conclusion enums, treat as plain str fields. If enums are intended, they would be imported and tested like WorkflowRun does. However, it's possible the architect/programmer may introduce enums later.

**Decision for analysis**: Fields can be plain str or Enum; implementation should accept plain strings in tests (no type coercion needed).

### 2. duration_seconds Default Value
**Ambiguity**: Test checks `assert attempt.duration_seconds is None or attempt.duration_seconds == 0.0` — either is acceptable.

**Working assumption**: Default to None (more idiomatic for optional), but 0.0 is also valid. Implementation will use None to match "optional" semantics.

**Decision**: Use `Optional[float] = None` with optional parameter handling in from_dict().

### 3. Integer Types for IDs
**Ambiguity**: WorkflowRun uses `id: str`, but test uses `id=1` (int). WorkflowRunAttempt may use integers for IDs.

**Working assumption**: Use int for id and run_id based on test's dict assertion structure and int literals in _attempt().

### 4. CEST Timezone Handling in from_dict()
**Ambiguity**: How to handle datetime deserialization when source might not have tzinfo.

**Working assumption**: fromisoformat() will preserve tzinfo if present in ISO string. For validation, must check/convert to CEST before returning from from_dict().

## Scope: What's In, Out, and Borderline

### Explicitly In Scope
- Create `/src/models/workflow_run_attempt.py`
- Implement WorkflowRunAttempt dataclass
- Implement `__post_init__()` with validation
- Implement `to_dict()` serialization
- Implement `from_dict()` deserialization
- Import in `/src/models/__init__.py`
- All 8 test cases must pass

### Explicitly Out of Scope
- No changes to baseline/
- No changes to services/, storage/, or cli/ (these can reference the new model but don't need modification for the model itself)
- No new tests (test file provided, not to be modified)
- No enum definitions for status/conclusion (use str)

### Borderline: Not Explicitly Required but Inferred
- Should `duration_seconds` be validated (non-negative like WorkflowRun)? Not tested, but pattern suggests YES.
- Should type hints match WorkflowRun patterns? Yes, for consistency.
- Should docstrings be added? No requirement shown, but good practice.

## Suggested Implementation Priorities

### Priority 1: Field Definition (Load-Bearing)
- Dataclass with exact 7 fields as specified
- Correct type hints: id (int), run_id (int), attempt_number (int), status (str), conclusion (str), created_at (datetime), duration_seconds (Optional[float])
- Default for duration_seconds critical for tests

### Priority 2: Validation in __post_init__ (Test Blocker)
- Check attempt_number > 0, raise ValueError if not
- Check created_at.tzinfo equals CEST (timedelta(hours=2)), raise ValueError if not
- Check duration_seconds is None or >= 0 (pattern consistency)

### Priority 3: Serialization/Deserialization (Test Blocker)
- to_dict() must convert datetime to isoformat() string, handle None values
- from_dict() must use datetime.fromisoformat() AND ensure timezone is CEST
- Both must roundtrip all 7 fields correctly

### Priority 4: Import Export (Integration)
- Add to `/src/models/__init__.py`
- Ensure test can `from src.models.workflow_run_attempt import WorkflowRunAttempt`

## Related Objects and Dependencies

### Direct Dependencies (in test imports)
- datetime, timezone, timedelta (Python stdlib)
- CEST constant definition (local to test as timezone(timedelta(hours=2)))

### Related Models (same package)
- WorkflowRun: Use as pattern reference for structure
- WorkflowStatus, WorkflowConclusion: Do NOT use (tests don't show dependency)

### No Service/Storage Changes Needed
- Tests only instantiate and serialize the model directly
- No service layer integration required for this task
- WorkflowRunAttempt may be used by services later, but that's outside this task scope

## Summary of What Must Be Created

**Single file**: `/src/models/workflow_run_attempt.py`

**Must contain**:
1. Import statements: dataclass, field, datetime, timezone, timedelta, Optional
2. CEST timezone constant (or define inline)
3. WorkflowRunAttempt dataclass with:
   - 7 fields as specified
   - `__post_init__()` for 2 validations (attempt_number > 0, created_at in CEST)
   - `to_dict()` method
   - `from_dict()` class method
4. Update `/src/models/__init__.py` to export WorkflowRunAttempt

**Test File** (already provided, read-only):
- `tests/test_workflow_run_attempt.py` (assumed location based on test suite provided)
