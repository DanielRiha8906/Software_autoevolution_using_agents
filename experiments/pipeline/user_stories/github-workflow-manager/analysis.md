# Task 03 Analysis: Create WorkflowRunAttempt Class

## What the Task Is Asking For

Create a first-class model `WorkflowRunAttempt` that represents individual workflow run attempts (a run can be retried, each retry is an attempt). The class must include:

**Required attributes:**
- `id: int` — unique identifier for the attempt
- `run_id: int` — foreign key to parent WorkflowRun
- `attempt_number: int` — sequential attempt counter (positive integer, starting from 1)
- `status: str` — execution status
- `conclusion: Optional[str]` — execution outcome (nullable)
- `created_at: datetime` — creation timestamp (CEST, UTC+2)
- `duration_seconds: float` — execution duration (optional)

**Constraints:**
- Unique constraint on (run_id, attempt_number) pair — no duplicate attempts for the same run
- attempt_number must be a positive integer starting from 1
- Must support JSON serialization/deserialization (like WorkflowRun)
- Associated with parent WorkflowRun (relationship/association pattern needed)

## Current Data Model Architecture

### WorkflowRun Class (Location: src/models/workflow_run.py)

**Current structure:**
```
WorkflowRun (dataclass):
  - id: str (string UUID)
  - workflow_name: str
  - branch: str
  - status: WorkflowStatus (enum)
  - conclusion: Optional[WorkflowConclusion] (optional enum)
  - created_at: datetime
  - updated_at: Optional[datetime]
  - run_number: Optional[int]
  - commit_sha: Optional[str]
  - duration_seconds: float (default 0.0)
```

**Patterns used:**
- **Dataclass pattern** — Uses Python 3.7+ dataclass decorator, not ORM
- **Enum typing** — status and conclusion use Enum classes (WorkflowStatus, WorkflowConclusion)
- **Validation in __post_init__()** — duration_seconds >= 0 enforced at construction
- **Optional fields** — Uses Optional[type] for nullable fields (updated_at, conclusion, run_number, etc.)
- **ISO format serialization** — to_dict() and from_dict() use datetime.isoformat() for timestamps
- **Class method deserialization** — from_dict() is a @classmethod that reconstructs from dict

### Serialization Pattern Observed

In WorkflowRun.to_dict():
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "workflow_name": self.workflow_name,
        "branch": self.branch,
        "status": self.status.value,              # Enum → string value
        "conclusion": self.conclusion.value if self.conclusion else None,  # Null-safe enum
        "created_at": self.created_at.isoformat(),  # datetime → ISO string
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,  # Null-safe ISO
        "run_number": self.run_number,
        "commit_sha": self.commit_sha,
        "duration_seconds": self.duration_seconds,
    }
```

And in WorkflowRun.from_dict():
```python
@classmethod
def from_dict(cls, data: dict) -> "WorkflowRun":
    return cls(
        id=data["id"],
        workflow_name=data["workflow_name"],
        branch=data["branch"],
        status=WorkflowStatus(data["status"]),  # String → Enum
        conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,  # Null-safe
        created_at=datetime.fromisoformat(data["created_at"]),  # ISO string → datetime
        updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,  # Null-safe
        run_number=data.get("run_number"),
        commit_sha=data.get("commit_sha"),
        duration_seconds=data.get("duration_seconds", 0.0),
    )
```

**Key pattern:** Enums are stored as .value (string), datetimes as isoformat() strings; deserialization reverses this.

### Storage Layer (Location: src/storage/workflow_json_storage.py)

**Current approach:**
- JSON file storage (no database/ORM)
- Single file per list: `artifacts/workflow_runs.json`
- Loads entire list at startup, keeps in memory, saves whole list on mutation
- Calls `run.to_dict()` for serialization, `WorkflowRun.from_dict()` for deserialization

**Pattern:** Store all objects in a JSON array; no relational schema.

### Service Layer (Location: src/services/workflow_run_service.py)

**Current approach:**
- Single responsibility: in-memory CRUD operations for WorkflowRun objects
- Methods: add_workflow_run(), list_runs(), get_run_detail(), filter_by_branch(), filter_by_status(), filter_by_conclusion()
- Duplicate detection: `if any(r.id == run.id for r in self._runs)` raises ValueError on duplicate
- Persistence: calls `self._storage.save(self._runs)` after each mutation

**Pattern:** Service manages in-memory list; storage handles persistence. No transaction model.

### Enum Definitions

**WorkflowStatus** (src/models/workflow_status.py):
- String enum (inherits from str, Enum)
- Values: QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING

**WorkflowConclusion** (src/models/workflow_conclusion.py):
- String enum (inherits from str, Enum)
- Values: SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE

**Note:** These represent GitHub Actions API states; task requirement says not to modify them.

### Import Pattern in Models

In src/models/__init__.py:
```python
from .workflow_run import WorkflowRun
from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion

__all__ = ["WorkflowRun", "WorkflowStatus", "WorkflowConclusion"]
```

**Pattern:** Each model gets its own file; __init__.py re-exports them.

## What Needs to Be Added for WorkflowRunAttempt

### 1. New Model Class

**File:** `src/models/workflow_run_attempt.py` (new file)

**Requirements:**
```python
@dataclass
class WorkflowRunAttempt:
    id: int                                      # Unique identifier
    run_id: int                                  # Foreign key to WorkflowRun
    attempt_number: int                          # Positive integer, starts at 1
    status: str                                  # Execution status (string, not enum)
    conclusion: Optional[str]                    # Optional outcome (string, not enum)
    created_at: datetime                         # CEST timezone (UTC+2)
    duration_seconds: float = 0.0                # Optional, defaults to 0.0
    
    def __post_init__(self) -> None:
        # Validate attempt_number is positive integer >= 1
        if not isinstance(self.attempt_number, int) or self.attempt_number < 1:
            raise ValueError("attempt_number must be a positive integer (>= 1)")
        # Validate duration_seconds is non-negative (same pattern as WorkflowRun)
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")
    
    def to_dict(self) -> dict:
        # Serialize to JSON-compatible dict
        # created_at should be ISO format (isoformat())
        # Handle nullable conclusion
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        # Deserialize from dict
        # Parse created_at from ISO format (fromisoformat())
        # Handle nullable conclusion
        pass
```

**Design notes:**
- Use dataclass decorator (matches WorkflowRun pattern)
- `status` and `conclusion` are strings, NOT enums (task specifies str type)
- `created_at` has CEST (UTC+2) requirement — likely metadata/documentation; actual storage should use UTC and let callers adjust if needed
- `duration_seconds` is optional with default 0.0 (matches WorkflowRun pattern)
- Unique constraint (run_id, attempt_number) is enforced at **service layer**, not in dataclass

### 2. Service Layer Enhancements

**File:** `src/services/workflow_run_service.py` (or new file `src/services/workflow_run_attempt_service.py`)

**Decision point:** Should attempts be:
- **Option A:** Nested inside WorkflowRunService (add_attempt, get_attempts, etc.)
- **Option B:** New separate service class WorkflowRunAttemptService
- **Option C:** Embedded in WorkflowRun (has_many relationship)

**Recommended:** Option B (separate service) — Keeps concerns separate, matches SRP, easier to test and reuse.

**Methods needed:**
```python
class WorkflowRunAttemptService:
    def __init__(self, storage: WorkflowJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load_attempts()
    
    def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        # Enforce unique constraint: (run_id, attempt_number)
        if any(a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number for a in self._attempts):
            raise ValueError(f"Attempt {attempt.attempt_number} for run {attempt.run_id} already exists.")
        self._attempts.append(attempt)
        self._persist()
        return attempt
    
    def list_attempts(self) -> List[WorkflowRunAttempt]:
        return list(self._attempts)
    
    def get_attempt(self, attempt_id: int) -> Optional[WorkflowRunAttempt]:
        # By attempt id
        pass
    
    def get_attempts_for_run(self, run_id: int) -> List[WorkflowRunAttempt]:
        # All attempts for a given run
        return [a for a in self._attempts if a.run_id == run_id]
    
    def _persist(self) -> None:
        self._storage.save_attempts(self._attempts)
```

### 3. Storage Layer Enhancements

**File:** `src/storage/workflow_json_storage.py` (extend existing)

**Methods to add:**
```python
class WorkflowJsonStorage:
    def __init__(self, filepath: str = "artifacts/workflow_runs.json", attempts_filepath: str = "artifacts/workflow_run_attempts.json"):
        self.filepath = Path(filepath)
        self.attempts_filepath = Path(attempts_filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def save_attempts(self, attempts: List[WorkflowRunAttempt]) -> None:
        data = [attempt.to_dict() for attempt in attempts]
        self.attempts_filepath.write_text(json.dumps(data, indent=2))
    
    def load_attempts(self) -> List[WorkflowRunAttempt]:
        if not self.attempts_filepath.exists():
            return []
        raw = json.loads(self.attempts_filepath.read_text())
        return [WorkflowRunAttempt.from_dict(item) for item in raw]
```

**Design decision:** Separate JSON file for attempts (`workflow_run_attempts.json`) keeps data cleanly separated and allows independent queries.

### 4. Model Package Update

**File:** `src/models/__init__.py` (extend)

```python
from .workflow_run import WorkflowRun
from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion
from .workflow_run_attempt import WorkflowRunAttempt

__all__ = ["WorkflowRun", "WorkflowStatus", "WorkflowConclusion", "WorkflowRunAttempt"]
```

### 5. CLI Integration (if required)

**Task requirement:** "JSON serialization/deserialization support" and association with parent WorkflowRun

**Minimum:** Serialization and model relationship working

**Optional but recommended:** CLI commands to add/list/detail attempts
- `python -m src attempt add --run-id <id> --attempt-number <n> --status <s> --conclusion <c>`
- `python -m src attempt list [--run-id <id>]`
- `python -m src attempt detail <attempt-id>`

**Extend:** `src/cli/workflow_cli.py` with new subcommand or menu option

### 6. Relationship Between WorkflowRun and WorkflowRunAttempt

**Pattern needed:** Parent-child association

**Option A (Lazy association):**
```python
# In WorkflowRun or service:
def get_attempts(self, run_id: int) -> List[WorkflowRunAttempt]:
    return self.attempt_service.get_attempts_for_run(run_id)
```

**Option B (Eager association):**
```python
@dataclass
class WorkflowRun:
    # ... existing fields ...
    attempts: List[WorkflowRunAttempt] = field(default_factory=list)
```

**Recommended:** Option A (lazy) — Keeps WorkflowRun simple and independent; WorkflowRunAttempt is a peer model, not a nested structure.

## Data Model Architecture Pattern Summary

**Stack:**
1. **Model layer** (src/models/) — Dataclasses with validation, serialization
2. **Service layer** (src/services/) — In-memory CRUD, uniqueness constraints, persistence delegation
3. **Storage layer** (src/storage/) — JSON file read/write, model reconstruction
4. **CLI layer** (src/cli/) — User-facing commands, menu options

**Key traits:**
- No ORM/database — pure JSON with in-memory state
- Dataclass-based models — simple, lightweight, no boilerplate
- Enum typing for constrained string values — type safety
- ISO datetime serialization — interop with JSON/external systems
- Optional fields use Optional[type] — explicit nullability
- Validation in __post_init__() — fail-fast on invalid construction
- Duplicate detection at service layer — enforces uniqueness
- Separate persistence — storage layer is thin, models are dumb

## Architectural Constraints to Respect

1. **No ORM/database drivers** — Stick with JSON storage pattern
2. **Dataclass pattern only** — Don't use custom classes without @dataclass
3. **Enum for constrained values** — But WorkflowRunAttempt.status and conclusion are strings (task spec)
4. **No __main__.py wiring required** — But if adding CLI, follow existing arg parser patterns
5. **Existing test patterns** — Use pytest, MagicMock, parametrize where helpful
6. **ISO datetime format** — Use isoformat() for serialization

## Timestamp Timezone Consideration

**Task requirement:** `created_at` should be CEST (UTC+2)

**Current code pattern** (WorkflowRunTracker):
```python
created_at=datetime.now(timezone.utc)  # Creates UTC timestamp
```

**Decision for WorkflowRunAttempt:**
- Store in UTC (best practice for storage/interchange)
- Provide method or documentation for CEST conversion at display time
- Or: Accept created_at parameter as-is (caller provides correct timezone)
- **Working assumption:** Task mentions CEST as context (GitHub Actions is UTC), but storage should be UTC. CLI/display layer handles timezone conversion if needed.

## Files That Will Need Changes/Creation

### New Files
1. **src/models/workflow_run_attempt.py** — New WorkflowRunAttempt dataclass
2. **src/services/workflow_run_attempt_service.py** (optional) — Service for attempt CRUD

### Modified Files
1. **src/models/__init__.py** — Export WorkflowRunAttempt
2. **src/storage/workflow_json_storage.py** — Add load_attempts(), save_attempts()
3. **src/__main__.py** (optional) — Wire new service to CLI if commands needed
4. **src/cli/workflow_cli.py** (optional) — Add `attempt` subcommand if desired
5. **src/cli/interactive_menu.py** (optional) — Add menu option for attempts if desired
6. **tests/** — Add test_workflow_run_attempt.py with unit and integration tests

### Diagram Updates (post-implementation)
1. **artifacts/class_diagram.puml** — Add WorkflowRunAttempt class box
2. **artifacts/component_diagram.puml** — Show WorkflowRunAttemptService if added

## Ambiguities and Working Assumptions

### 1. Unique Constraint Enforcement

**Ambiguity:** Should (run_id, attempt_number) uniqueness be enforced at model, service, or database level?

**Working assumption:** Enforce at service layer (like WorkflowRunService does for id). Model doesn't validate business rules, service does.

### 2. ID Generation

**Ambiguity:** How are `id` values assigned? Auto-increment, UUID, provided by caller?

**Working assumption:** Likely auto-increment (mimics database behavior) or UUID. Task doesn't specify. Recommend: Let caller provide or generate; service accepts as-is (like WorkflowRun's run_id parameter).

### 3. Status and Conclusion as Strings

**Ambiguity:** Why are these strings instead of enums (like WorkflowRun)?

**Working assumption:** Task explicitly specifies `status: str` and `conclusion: Optional[str]`. This may indicate that attempt status/conclusion values differ from WorkflowRun statuses. Respect the task spec; don't change to enums.

### 4. CEST Timezone Requirement

**Ambiguity:** Should created_at be stored as CEST or UTC?

**Working assumption:** Store as UTC (best practice), document CEST context. Callers can convert for display. If task strictly requires CEST storage, use UTC+2 offset in datetime.

### 5. Parent Association Implementation

**Ambiguity:** How should WorkflowRun and WorkflowRunAttempt relate?

**Working assumption:** Lazy association via run_id foreign key. No eager loading or nested structures. Query via service layer (attempt_service.get_attempts_for_run(run_id)).

### 6. CLI Exposure Requirement

**Ambiguity:** Are CLI commands required or just JSON serialization?

**Working assumption:** Task says "JSON serialization/deserialization support" and "associated with parent WorkflowRun". This suggests model + storage. CLI commands are optional but recommended for testing and usability (following "all functionality must be reachable via `python -m src`" governance).

## Scope Signals

### In Scope
- ✅ WorkflowRunAttempt dataclass with 7 required fields
- ✅ Unique constraint (run_id, attempt_number) enforced at service layer
- ✅ JSON serialization/deserialization (to_dict, from_dict)
- ✅ Validation in __post_init__() (attempt_number >= 1, duration_seconds >= 0)
- ✅ Association with parent WorkflowRun (via run_id foreign key)
- ✅ Storage in separate JSON file (workflow_run_attempts.json)
- ✅ Service layer CRUD operations

### Out of Scope
- ❌ Creating or modifying database schema (JSON storage only)
- ❌ Adding database ORM (stay with JSON)
- ❌ Modifying WorkflowRun enum definitions (only JSON-compatible strings for attempts)
- ❌ Nested/eager loading (lazy associations only)
- ❌ Update/edit operations (if task doesn't specify, assume add only)

### Borderline
- ✓ CLI commands — Not explicitly required, but recommended for completeness and testing
- ✓ Menu integration — Not explicit, but follows governance "all functionality via python -m src"
- ✓ State-checking methods (like WorkflowRun has) — Not mentioned; keep focus on CRUD

## Suggested Priorities

### 1. **HIGH**: Create WorkflowRunAttempt dataclass (core requirement)
   - Define fields per task spec
   - Implement __post_init__() validation
   - Implement to_dict() and from_dict()
   - No external dependencies needed

### 2. **HIGH**: Extend storage layer (JSON persistence)
   - Add load_attempts() and save_attempts() to WorkflowJsonStorage
   - Ensure round-trip serialization works (to_dict → JSON → from_dict)
   - Test with sample attempts

### 3. **HIGH**: Create WorkflowRunAttemptService (CRUD + uniqueness)
   - add_attempt() with (run_id, attempt_number) uniqueness check
   - list_attempts(), get_attempt(), get_attempts_for_run()
   - Persist after mutations

### 4. **MEDIUM**: Test coverage (correctness assurance)
   - Unit tests for dataclass validation
   - Serialization round-trip tests
   - Service uniqueness constraint tests
   - Integration tests with storage layer

### 5. **MEDIUM**: CLI integration (optional but recommended)
   - Add `attempt` subcommand or extend workflow_cli
   - Wire new service to __main__.py
   - Update interactive menu if desired

### 6. **LOW**: Diagram updates (documentation)
   - Update class_diagram.puml to show WorkflowRunAttempt
   - Add service if created
   - Update component diagram if service added

---

## Summary

WorkflowRunAttempt is a first-class model for retried workflow runs, paralleling WorkflowRun but independent. It uses the same dataclass pattern, JSON serialization, and service-layer validation architecture as WorkflowRun. The key differences:
- Attempts are identified by (run_id, attempt_number) pair, not a standalone id
- Status and conclusion are strings, not enums (per task spec)
- Related to WorkflowRun via run_id (lazy association)
- Stored separately (workflow_run_attempts.json) but managed by parallel service

No architectural innovation needed; follow the established patterns from WorkflowRun closely, adjust field types/constraints per task spec, and ensure unique constraint enforcement at service layer.
