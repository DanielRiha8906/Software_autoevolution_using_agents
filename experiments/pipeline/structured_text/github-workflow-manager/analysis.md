# Analysis: Create WorkflowRunAttempt Class

## What the Task Is Asking For

Add a new `WorkflowRunAttempt` class to model multiple attempts per workflow run. This establishes that a single `WorkflowRun` can have multiple retry attempts, each with independent status, conclusion, and timing information. The class must:

**Must Have:**
- Create class `WorkflowRunAttempt` with attributes:
  - `id: int` — unique identifier for the attempt
  - `run_id: int` — foreign key to parent WorkflowRun
  - `attempt_number: int` — ordinal position (1, 2, 3, ...)
  - `status: str` — current execution state
  - `conclusion: Optional[str]` — final result (if terminal)
  - `created_at: datetime` — timestamp in CEST/UTC+2
- Establish relationship to WorkflowRun

**Should Have:**
- Support serialization/deserialization (to_dict/from_dict pattern)

**Could Have:**
- `duration_seconds: float` — execution duration

**Won't Have:**
- Optimize persistence or storage performance

## Current Architecture

### Model Layer
**Location:** `src/models/`

**WorkflowRun class** (`src/models/workflow_run.py`):
- 10 attributes: id, workflow_name, branch, status, conclusion, created_at, updated_at, run_number, commit_sha, duration_seconds
- Uses Python `@dataclass` decorator for structure
- Includes `__post_init__()` for validation (non-negative duration_seconds)
- Methods: `to_dict()`, `from_dict()` (classmethod), and 5 state predicate methods (is_running, is_terminal, is_successful, is_failed, is_cancelled)
- Enums: `WorkflowStatus` (7 states: queued, in_progress, completed, waiting, requested, pending) and `WorkflowConclusion` (8 conclusions: success, failure, cancelled, skipped, timed_out, action_required, neutral, stale)

**Current relationships:**
- WorkflowRun has 1:many implied relationship to attempts (not yet modeled)
- No parent-child relationship currently exists in the data model

### Storage Layer
**Location:** `src/storage/workflow_json_storage.py`

- Generic JSON persistence using `pathlib.Path` and `json` module
- Calls `to_dict()` and `from_dict()` on all model instances
- Stores flat list of WorkflowRun objects in JSON array format
- No nested structure support for related entities currently

**Key pattern:** Storage is decoupled from model structure via serialization methods

### Service Layer
**Location:** `src/services/`

**WorkflowRunService** (`workflow_run_service.py`):
- In-memory list of WorkflowRun objects (`_runs: List[WorkflowRun]`)
- CRUD operations: add_workflow_run(), list_runs(), get_run_detail()
- Filtering: filter_by_branch(), filter_by_status(), filter_by_conclusion()
- Persistence: calls storage.save() after mutations

**WorkflowRunTracker** (`workflow_run_tracker.py`):
- Facade for creating and adding WorkflowRun instances
- Single method: track() with 8 optional parameters
- Generates UUID if run_id not provided
- Uses UTC timezone for timestamps

### Test Patterns
**Location:** `tests/`

Three test suites exist:
1. `test_workflow_json_storage.py` — 7 tests for serialization roundtrip and backward compatibility
2. `test_workflow_run_service.py` — 6 tests for CRUD and filtering operations
3. `test_workflow_run_state.py` — 54 comprehensive tests for state predicates and logical constraints

**Test helper pattern:**
```python
def _make_run(run_id: str = "run-1", branch: str = "main") -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=0.0,
    )
```

## Key Findings

### 1. Serialization Pattern Already Established
The codebase uses a consistent pattern for all models:
- `to_dict()` instance method: converts to JSON-serializable dict (enums to .value, datetimes to .isoformat())
- `from_dict(data: dict)` classmethod: reconstructs from dict with type conversions
- Datetime fields use `datetime.fromisoformat()` for parsing
- Optional fields use `data.get(key, default)` for safe deserialization

**WorkflowRun.to_dict() example:**
```python
"status": self.status.value,  # enum to string
"conclusion": self.conclusion.value if self.conclusion else None,
"created_at": self.created_at.isoformat(),  # datetime to ISO string
```

### 2. Datetime Handling Pattern
- WorkflowRun uses `datetime.now(timezone.utc)` in tracker
- Storage layer calls `.isoformat()` for serialization
- Deserialization uses `.fromisoformat()` for parsing
- **CEST/UTC+2 timezone requirement:** Current code uses UTC internally; CEST is UTC+2, which is a concrete offset, not a timezone name. This requires explicit handling or conversion.

### 3. Current ID Strategy
- WorkflowRun uses string IDs (`id: str`)
- Generated via `uuid.uuid4()` if not provided
- **WorkflowRunAttempt requirement:** int type for id and run_id, breaking from string pattern. This is intentional for attempt tracking (ordinal, not UUID-like).

### 4. Validation Pattern
WorkflowRun.__post_init__() validates non-negative duration:
```python
def __post_init__(self):
    if self.duration_seconds < 0:
        raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}")
```

**WorkflowRunAttempt will need similar validation** for attempt_number >= 1.

### 5. No Existing Relationship Modeling
The codebase currently:
- Does NOT have 1:many parent-child relationships
- Does NOT have foreign key references
- Stores flat lists of independent entities
- Does NOT have a service layer for child entities

**Impact:** WorkflowRunAttempt and its relationship to WorkflowRun must be designed from scratch. Options:
1. Embed attempts list in WorkflowRun (nested structure)
2. Create separate WorkflowRunAttempt model and service (parallel structure)
3. Add attempts list to WorkflowRun + create dedicated service for attempt operations

### 6. Status and Conclusion Reuse
The task specifies:
- `status: str` (string, not enum)
- `conclusion: Optional[str]` (string, not enum)

**Current code:**
- WorkflowRun.status is enum (WorkflowStatus)
- WorkflowRun.conclusion is enum (WorkflowConclusion)

**Design decision:** WorkflowRunAttempt uses strings for status/conclusion, NOT enums. This is a deliberate divergence from WorkflowRun. Rationale: attempts may have different status/conclusion values than the 7/8 predefined for runs, or the requirement specifies simpler string handling.

### 7. JSON Storage Structure Impact
Current storage saves flat array:
```json
[
  {"id": "...", "workflow_name": "...", ...},
  {"id": "...", "workflow_name": "...", ...}
]
```

**With WorkflowRunAttempt nested in WorkflowRun:**
```json
[
  {
    "id": "...",
    "workflow_name": "...",
    "attempts": [
      {"id": 1, "run_id": "...", "attempt_number": 1, ...},
      {"id": 2, "run_id": "...", "attempt_number": 2, ...}
    ]
  }
]
```

This requires updating:
- WorkflowRun.to_dict() to include nested attempts list
- WorkflowRun.from_dict() to reconstruct attempt instances
- WorkflowJsonStorage inherits these changes automatically

## Ambiguities and Assumptions

### 1. Relationship Model (Unclear)
**Ambiguity:** How should attempts be stored and accessed?

**Options:**
- A) Embed `attempts: List[WorkflowRunAttempt]` in WorkflowRun dataclass
- B) Create separate `WorkflowRunAttemptService` and store attempts independently
- C) Store both together but with separate query paths

**Assumption:** Option A (embedded) — simplest, aligns with task requirement "establish relationship to WorkflowRun", and matches the existing flat-storage pattern. WorkflowRunAttempt is a child entity, not a standalone entity in the service layer.

### 2. Timezone Handling (Unclear)
**Ambiguity:** What exactly is meant by "created_at (datetime CEST/UTC+2)"?

**Options:**
- Requirement to store time in CEST specifically (UTC+2 hardcoded offset)
- Requirement to accept/display times in CEST timezone
- Just clarification that timestamps are UTC and should be displayed as CEST when shown to users

**Assumption:** CEST is a fixed offset (UTC+2). Python's datetime.timezone.utc is the standard; conversion to CEST happens at display/API boundary if needed. WorkflowRunAttempt stores UTC internally (like WorkflowRun) for consistency.

### 3. Status/Conclusion String Values (Unclear)
**Ambiguity:** What are valid string values for attempt status and conclusion? Are they a subset of WorkflowStatus/WorkflowConclusion enums, or completely independent?

**Assumption:** They are strings (not typed enums) because the requirement explicitly says `str` and `Optional[str]`, not enum types. This allows flexibility for attempt-specific states not defined in WorkflowStatus/WorkflowConclusion. No validation of specific values is required unless specified.

### 4. ID Generation Strategy (Unclear)
**Ambiguity:** Task says `id: int` (not `id: str` like WorkflowRun). Should attempt IDs be:
- Auto-incrementing integers within a run?
- Global UUIDs converted to integers?
- Hash-based integers?

**Assumption:** Auto-incrementing per-run (attempt_number is already ordinal, id could be derived from it). For now, assume id and attempt_number are independently assigned, with validation that attempt_number >= 1 and id >= 1.

### 5. Duration Seconds Default (Unclear)
**Ambiguity:** Task lists `duration_seconds` as "Could Have" but doesn't specify if it should be required or optional or have a default.

**Assumption:** If implemented, follow the WorkflowRun pattern: `duration_seconds: float = 0.0` with `__post_init__()` validation for non-negative values.

## Scope Signals

### Explicitly In Scope
- New class `WorkflowRunAttempt` with 6 required attributes (id, run_id, attempt_number, status, conclusion, created_at)
- Establish parent-child relationship to WorkflowRun
- Serialization/deserialization support (to_dict, from_dict)

### Explicitly Out of Scope
- Optimize persistence or storage performance
- Create database schema or ORM
- Implement API endpoints
- Add web UI
- Integration with external GitHub APIs

### Borderline / Depends on Implementation Choice
- **Relationship representation:** If embedded in WorkflowRun, affects WorkflowRun.to_dict/from_dict. If separate, requires new service class.
- **Service layer for attempts:** Task doesn't explicitly require it; depends on CRUD operations needed.
- **CLI support:** Task doesn't ask for CLI changes, but serialization support implies it.
- **Tests for WorkflowRunAttempt:** No explicit requirement, but test coverage pattern in the codebase suggests tests should be added.

## Files Impacted

### Must Create
1. **`src/models/workflow_run_attempt.py`** — New WorkflowRunAttempt class
   - All 6+ required attributes
   - to_dict() method
   - from_dict() classmethod
   - Validation in __post_init__()

### Must Modify
1. **`src/models/workflow_run.py`** — Add relationship
   - Add `attempts: List[WorkflowRunAttempt] = field(default_factory=list)` to dataclass
   - Update to_dict() to serialize attempts
   - Update from_dict() to deserialize attempts
   
2. **`src/models/__init__.py`** — Export new class
   - Add `from .workflow_run_attempt import WorkflowRunAttempt`
   - Add `"WorkflowRunAttempt"` to __all__

### May Create (Based on Implementation)
3. **`src/services/workflow_run_attempt_service.py`** — Optional, if separate CRUD service needed
4. **`tests/test_workflow_run_attempt.py`** — New test suite for attempts

### May Modify (Based on Implementation)
5. **`src/services/workflow_run_tracker.py`** — If tracker creates attempts
6. **Tests** — Update test helpers (_make_run) to initialize attempts

## Constraints and Dependencies

### 1. Dataclass Field Ordering
- If embedding attempts in WorkflowRun, the field must use `field(default_factory=list)` because it comes after optional fields
- Syntax: `attempts: List[WorkflowRunAttempt] = field(default_factory=list)`

### 2. Circular Import Risk
- WorkflowRunAttempt imports WorkflowRun for type hint in relationship
- WorkflowRun imports WorkflowRunAttempt for the attempts list type
- **Solution:** Use forward references or TYPE_CHECKING guard:
```python
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .workflow_run import WorkflowRun
```

### 3. Serialization Recursion
- WorkflowRun.to_dict() must call attempt.to_dict() for each attempt in the list
- WorkflowRun.from_dict() must call WorkflowRunAttempt.from_dict() for each attempt dict
- Backward compatibility: old JSON without attempts key should default to empty list

### 4. Validation Order
- WorkflowRunAttempt.__post_init__() must validate attempt_number >= 1
- If id is to be validated, must validate id >= 1
- Datetime validation (if any) should follow existing pattern

### 5. Timezone Awareness
- datetime objects must be timezone-aware (not naive)
- Use `datetime.fromisoformat()` to parse ISO strings (preserves timezone)
- Conversion to CEST should happen at display/API layer, not storage layer

## Suggested Priorities

### Priority 1: Create WorkflowRunAttempt Class (Must Have Foundation)
**Why:** Without this, nothing else can be implemented. This is the core data structure.

**Deliverables:**
- `src/models/workflow_run_attempt.py` with:
  - Dataclass definition
  - All 6 required attributes
  - to_dict() and from_dict() methods
  - Validation in __post_init__() for attempt_number >= 1

**Success criteria:**
- Class instantiates successfully with valid inputs
- Negative attempt_number raises ValueError
- Serialization roundtrip preserves all data types

### Priority 2: Establish Relationship (Must Have)
**Why:** Task explicitly requires "establish relationship to WorkflowRun"

**Deliverables:**
- Add attempts list to WorkflowRun dataclass
- Update WorkflowRun.to_dict() to serialize attempts
- Update WorkflowRun.from_dict() to deserialize attempts
- Update src/models/__init__.py to export WorkflowRunAttempt

**Success criteria:**
- WorkflowRun can hold list of WorkflowRunAttempt instances
- Serialization includes nested attempts
- Deserialization reconstructs attempts from JSON
- Old JSON files without attempts key load without error

### Priority 3: Test Coverage (Should Have)
**Why:** Existing codebase has comprehensive test patterns; new class should follow suit

**Deliverables:**
- `tests/test_workflow_run_attempt.py` with:
  - Basic instantiation tests
  - Serialization roundtrip tests
  - Validation tests
- Update test helpers (_make_run) to include sample attempts

**Success criteria:**
- All WorkflowRunAttempt features are tested
- Integration tests verify attempts serialize with WorkflowRun

### Priority 4: Optional Features (Could Have)
**Why:** Enhances functionality but not blocking

**Deliverables:**
- Add duration_seconds attribute if needed
- Create WorkflowRunAttemptService if CRUD operations are required
- Update CLI if attempt display/input is needed

**Success criteria:**
- All tests pass
- No breaking changes to existing WorkflowRun functionality

## Key Design Questions for System Architect

1. **Relationship storage:** Should attempts be embedded in WorkflowRun or stored separately?
2. **CRUD operations:** Should there be a WorkflowRunAttemptService with add/list/filter methods?
3. **Timezone display:** When serializing to JSON, should CEST conversion happen, or is UTC fine for storage?
4. **ID generation:** How should attempt IDs be generated? Auto-increment, UUID, or user-provided?
5. **CLI integration:** Should CLI be updated to display/input attempts, or is this for backend only?

