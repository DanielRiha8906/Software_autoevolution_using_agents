# Task 03 Analysis: Create WorkflowRunAttempt Domain Object

## Task Summary
Create a new `WorkflowRunAttempt` domain class to model individual execution attempts within a workflow run. This domain object will encapsulate attempt-level execution metadata while maintaining consistency with the existing domain model architecture.

## Current State of Codebase

### Existing Domain Models
The codebase contains three domain models in `src/models/`:

1. **WorkflowStatus** (enum) - Status of workflow execution
   - Values: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING

2. **WorkflowConclusion** (enum) - Outcome of a completed workflow
   - Values: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE

3. **WorkflowRun** (dataclass) - Main workflow execution entity
   - Fields: id, workflow_name, branch, status, conclusion, created_at, duration_seconds, updated_at, run_number, commit_sha
   - Methods: __post_init__(), to_dict(), from_dict(), is_running(), is_terminal(), is_successful(), is_failed(), is_cancelled()

### Serialization Pattern
The codebase follows a consistent serialization pattern:
- Domain objects use `to_dict()` method to convert to dictionary representation
- `from_dict(data: dict)` class method reconstructs objects from dictionary
- Datetime objects are serialized to ISO format strings via `isoformat()`
- Enums are serialized to their string values
- Optional fields use conditional serialization (e.g., `if self.conclusion`)
- Deserialization handles backward compatibility with `get()` method for optional fields

**Pattern in WorkflowRun:**
```python
def to_dict(self) -> dict:
    return {
        "created_at": self.created_at.isoformat(),
        ...
    }

@classmethod
def from_dict(cls, data: dict) -> "WorkflowRun":
    return cls(
        created_at=datetime.fromisoformat(data["created_at"]),
        ...
    )
```

### Timezone Handling
Current implementation uses UTC timezone:
- `datetime.now(timezone.utc)` in WorkflowRunTracker
- Tests use `datetime(2024, 1, 1, tzinfo=timezone.utc)`
- All datetime serialization uses `.isoformat()` which preserves timezone info

**Important Note on CEST Requirement:** The task specifies that `created_at` must be timezone-aware CEST (UTC+2) and must reject naive/non-CEST datetimes. This represents a **BREAKING CHANGE** from current UTC-only implementation. The current codebase uses UTC exclusively.

### Storage and Service Layer
- **WorkflowJsonStorage**: Handles persistence via `to_dict()` / `from_dict()` round-tripping
- **WorkflowRunService**: Manages collection of WorkflowRun objects with filtering by branch, status, conclusion
- **WorkflowRunTracker**: High-level facade for creating WorkflowRun instances with UUID generation

### Code Organization
- Models are simple, immutable dataclasses
- No external dependencies in models (no requests, I/O)
- Models follow consistent naming and structure
- All serialization/deserialization happens within the model classes

## What WorkflowRunAttempt Needs to Be

### Required Fields (from task specification)
1. **id** : str - Unique identifier for the attempt
2. **run_id** : str - Foreign key to parent WorkflowRun
3. **attempt_number** : int - Sequential attempt number (must be ≥ 1)
4. **status** : WorkflowStatus - Current execution status
5. **conclusion** : Optional[WorkflowConclusion] - Outcome if terminal
6. **created_at** : datetime - Timestamp of attempt creation (timezone-aware CEST, UTC+2)
7. **duration_seconds** : Optional[float] - Elapsed time (defaults to None or 0.0)

### Validation Requirements
- **attempt_number**: Must be a positive integer (≥ 1)
  - Should be validated in `__post_init__()`
  - ValueError raised for invalid values
- **created_at**: Must be timezone-aware CEST (UTC+2)
  - Must reject naive datetimes
  - Must reject non-CEST timezones (e.g., UTC)
  - Validation needed in `__post_init__()`
- **duration_seconds**: Optional field, defaults to None or 0.0
  - If present, should be non-negative (similar to WorkflowRun pattern)

### Serialization Requirements
- Must implement `to_dict()` → dict
- Must implement `from_dict(data: dict)` → WorkflowRunAttempt (class method)
- Must support round-trip serialization with consistency
- Datetime serialization via `.isoformat()` (preserves CEST timezone info)
- Enum values serialized as strings

### Implementation Approach

#### Step 1: Create WorkflowRunAttempt dataclass
File: `src/models/workflow_run_attempt.py`
- Use @dataclass decorator (matching WorkflowRun pattern)
- Import necessary types (datetime, Optional, dataclass)
- Define fields in order: id, run_id, attempt_number, status, conclusion, created_at, duration_seconds

#### Step 2: Implement validation in __post_init__()
- Validate attempt_number ≥ 1 (ValueError if not)
- Validate created_at is CEST timezone-aware
  - Check `created_at.tzinfo is not None` (reject naive)
  - Check UTC offset equals 2 hours = 7200 seconds (CEST is UTC+2)
  - Raise ValueError with descriptive message for invalid timezone
- Validate duration_seconds ≥ 0.0 if present (matching WorkflowRun pattern)

#### Step 3: Implement to_dict() method
- Serialize id, run_id, attempt_number as-is
- Serialize status → status.value (string)
- Serialize conclusion → conclusion.value if present, else None
- Serialize created_at → created_at.isoformat() (preserves timezone)
- Serialize duration_seconds as-is (handle None case)

#### Step 4: Implement from_dict() class method
- Reconstruct all fields from dictionary
- Convert status string → WorkflowStatus(value)
- Convert conclusion string → WorkflowConclusion(value) if present
- Convert created_at ISO string → datetime.fromisoformat()
- Use .get() for optional fields with appropriate defaults
- Perform no additional validation (dataclass __post_init__ will run)

#### Step 5: Update exports
- Add WorkflowRunAttempt to `src/models/__init__.py`

## Key Constraints and Design Decisions

### CEST Timezone Requirement
**Assumption:** The CEST requirement applies only to WorkflowRunAttempt, not to existing WorkflowRun. The task states "created_at must be timezone-aware CEST (UTC+2)" in the context of WorkflowRunAttempt requirements, and the existing codebase uses UTC without issue. Implementing timezone conversion/enforcement should be localized to WorkflowRunAttempt to avoid breaking existing WorkflowRun functionality.

**Implementation Detail:** CEST is UTC+2 with offset of 7200 seconds. Validation should check:
```python
if created_at.tzinfo is None or created_at.utcoffset().total_seconds() != 7200:
    raise ValueError("created_at must be timezone-aware CEST (UTC+2)")
```

### Immutability
WorkflowRunAttempt should be immutable like WorkflowRun (frozen dataclass is optional but recommended for consistency).

### Relationship to WorkflowRun
- WorkflowRunAttempt references a parent WorkflowRun via `run_id` field
- No bidirectional relationship implemented (no List[WorkflowRunAttempt] on WorkflowRun)
- This allows attempts to be stored separately in JSON persistence layer

### Duration Handling
Task specifies "optional, defaults to None or 0.0" - this is ambiguous:
- **Assumption:** Use None as default (Optional[float] with default None)
- Matches pattern of other optional fields
- Still validates non-negative if present, matching WorkflowRun validation

### Serialization Round-Tripping
The serialization pattern must support:
- JSON persistence via storage layer (to_dict → JSON → from_dict)
- Timezone preservation (ISO format includes timezone offset)
- Backward compatibility (from_dict uses .get() for future optional fields)

## Files to Create/Modify

### New Files
- `src/models/workflow_run_attempt.py` - Domain object class

### Modified Files
- `src/models/__init__.py` - Add WorkflowRunAttempt export

## Test Expectations

Based on the task requirements, tests should verify:
1. WorkflowRunAttempt can be instantiated with all required fields
2. attempt_number validation (rejects < 1)
3. created_at timezone validation (rejects naive, rejects non-CEST)
4. duration_seconds validation (rejects negative if present)
5. to_dict() serialization works correctly
6. from_dict() deserialization works correctly
7. Round-trip serialization is consistent
8. All enum values serialize/deserialize correctly
9. Optional fields handle None correctly in serialization

## Summary

WorkflowRunAttempt is a new domain class that models individual execution attempts within workflow runs. It follows the established patterns of WorkflowRun (dataclass, to_dict/from_dict, validation in __post_init__) while introducing a new timezone constraint (CEST). The main implementation complexity lies in CEST timezone validation, which must be strict to enforce the requirement while preserving ISO format serialization for JSON persistence.
