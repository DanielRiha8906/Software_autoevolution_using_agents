# Task 04 - AttemptService Implementation: Analysis Report

## Task Summary

Implement `AttemptService` to manage workflow run attempts. The service must support creating attempts, retrieving attempts by `run_id`, preventing duplicate attempt numbers per run, and provide full CLI/menu access via `python -m src`.

**MoSCoW Breakdown:**
- **Must Have:** Implement AttemptService, support create/retrieve operations, integrate with storage, expose via CLI/menu
- **Should Have:** Ensure no duplicate attempt numbers per run
- **Could Have:** Add sorting by attempt number

---

## Current Architecture Overview

### Three-Tier Architecture

```
CLI Layer (workflow_cli.py, interactive_menu.py)
    ↓
Service Layer (WorkflowRunService, WorkflowAttemptService, Trackers)
    ↓
Storage Layer (WorkflowJsonStorage, WorkflowAttemptJsonStorage)
    ↓
Domain Models (WorkflowRun, WorkflowRunAttempt, enums)
```

### Component Diagram Location
**File:** `artifacts/component_diagram.puml`

Shows full architecture with:
- Application entrypoint → Interface layer (CLI, interactive menu)
- Interface → Service layer (Trackers, Services)
- Service → Persistence (JsonStorage components)
- Domain models (WorkflowRun, WorkflowRunAttempt, enums)

---

## Existing Attempt/Run Model Structure

### WorkflowRun Model
**File:** `src/models/workflow_run.py` (10 attributes)

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
    duration_seconds: float = 0.0
```

**Key Methods:**
- `to_dict()` / `from_dict()` — JSON serialization/deserialization
- `is_terminal()`, `is_running()`, `is_successful()`, `is_failed()`, `is_cancelled()` — state queries

### WorkflowRunAttempt Model
**File:** `src/models/workflow_attempt.py` (9 attributes)

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
    duration_seconds: float = 0.0
    logs_url: Optional[str] = None
```

**Key Methods:**
- `to_dict()` / `from_dict()` — JSON serialization/deserialization
- State query methods (identical to WorkflowRun)

**Relationship:** Attempts reference a run via `run_id` (foreign key). One-to-many: 1 WorkflowRun → N WorkflowRunAttempts

### Enums
**Files:** `src/models/workflow_status.py`, `src/models/workflow_conclusion.py`

**WorkflowStatus:** `queued`, `in_progress`, `completed`, `waiting`, `requested`, `pending`

**WorkflowConclusion:** `success`, `failure`, `cancelled`, `skipped`, `timed_out`, `action_required`, `neutral`, `stale`

---

## Storage Mechanism Details

### WorkflowJsonStorage
**File:** `src/storage/workflow_json_storage.py`

```python
class WorkflowJsonStorage:
    def __init__(self, filepath: str = "artifacts/workflow_runs.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, runs: List[WorkflowRun]) -> None:
        # Calls run.to_dict() for each run, writes JSON with indent=2
    
    def load(self) -> List[WorkflowRun]:
        # Loads JSON, returns empty list if file missing
        # Calls WorkflowRun.from_dict(item) for each item
```

**Behavior:**
- File-based JSON persistence
- Auto-creates parent directories
- Returns empty list on missing file (safe for first run)
- Serialization via dataclass `to_dict()` and `from_dict()` methods

### WorkflowAttemptJsonStorage
**File:** `src/storage/workflow_attempt_json_storage.py`

```python
class WorkflowAttemptJsonStorage:
    def __init__(self, filepath: str = "artifacts/workflow_attempts.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, attempts: List[WorkflowRunAttempt]) -> None:
        # Identical pattern to WorkflowJsonStorage
    
    def load(self) -> List[WorkflowRunAttempt]:
        # Identical pattern to WorkflowJsonStorage
```

**Currently Implemented:** Yes, fully functional storage layer exists.

---

## Existing Service Layer Implementation

### WorkflowRunService
**File:** `src/services/workflow_run_service.py` (7 methods)

```python
class WorkflowRunService:
    def __init__(self, storage: WorkflowJsonStorage):
        self._storage = storage
        self._runs: List[WorkflowRun] = storage.load()
    
    def add_workflow_run(self, run: WorkflowRun) -> WorkflowRun:
        # Checks for duplicate IDs, appends, persists
    
    def list_runs(self) -> List[WorkflowRun]:
    def get_run_detail(self, run_id: str) -> Optional[WorkflowRun]:
    def filter_by_branch(self, branch: str) -> List[WorkflowRun]:
    def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRun]:
    def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRun]:
    def _persist(self) -> None:
        # Calls storage.save(self._runs)
```

**Pattern:** Load on init → cache in memory → persist on write

### WorkflowAttemptService
**File:** `src/services/workflow_attempt_service.py` (7 methods)

```python
class WorkflowAttemptService:
    def __init__(self, storage: WorkflowAttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()
    
    def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        # Checks for duplicate IDs, appends, persists
    
    def list_attempts(self) -> List[WorkflowRunAttempt]:
    def get_attempt_detail(self, attempt_id: str) -> Optional[WorkflowRunAttempt]:
    def filter_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]:
    def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRunAttempt]:
    def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRunAttempt]:
    def _persist(self) -> None:
```

**Currently Implemented:** Yes, fully mirrors WorkflowRunService pattern.

**Key Gap:** Does NOT validate duplicate attempt numbers per (run_id, attempt_number) tuple.

---

## Tracker/Facade Layer

### WorkflowRunTracker
**File:** `src/services/workflow_run_tracker.py`

```python
class WorkflowRunTracker:
    def __init__(self, service: WorkflowRunService, 
                 attempt_service: Optional[WorkflowAttemptService] = None):
        self._service = service
        self._attempt_service = attempt_service
    
    def track(self, workflow_name: str, branch: str, status: WorkflowStatus, ...) -> WorkflowRun:
        # Creates WorkflowRun with defaults (id=UUID, created_at=now)
        # Calls service.add_workflow_run()
    
    def create_attempt(self, run_id: str, attempt_number: int, ...) -> WorkflowRunAttempt:
        # Creates WorkflowRunAttempt (id=UUID, started_at=now)
        # Calls attempt_service.add_attempt()
```

**Currently Implemented:** Yes. Both `track()` and `create_attempt()` exist.

### WorkflowAttemptTracker
**File:** `src/services/workflow_attempt_tracker.py`

```python
class WorkflowAttemptTracker:
    def __init__(self, service: WorkflowAttemptService):
        self._service = service
    
    def create_attempt(...) -> WorkflowRunAttempt:
        # Wrapper around service.add_attempt()
```

**Currently Implemented:** Yes, provides alternative entry point for attempt creation.

---

## CLI/Menu Entry Points

### Application Entrypoint
**File:** `src/__main__.py` (26 lines)

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

**Behavior:** No args → interactive menu. Args present → CLI mode.

### CLI Module: workflow_cli.py
**File:** `src/cli/workflow_cli.py` (259 lines)

**Build Parser:**
- Top-level subcommands: `add`, `list`, `detail`, `query-state`, `attempt`
- Attempt subcommands: `add`, `list`, `detail`, `query-state`

**Run CLI Function Signature:**
```python
def run_cli(service: WorkflowRunService, 
            attempt_service: WorkflowAttemptService = None, 
            args=None) -> None:
```

**Attempt Commands Implemented:**
- `attempt add` — Creates new attempt with run_id, attempt_number, status, etc.
- `attempt list` — Lists all or filters by run_id/status/conclusion
- `attempt detail` — Shows single attempt by ID
- `attempt query-state` — Shows state flags (terminal, running, successful, etc.)

**Currently Implemented:** Yes, all commands exist and are wired.

### Interactive Menu Module: interactive_menu.py
**File:** `src/cli/interactive_menu.py` (327 lines)

**Main Menu:**
1. Workflow Runs → submenu with 5 operations (add, list, detail, filter, query-state)
2. Workflow Attempts → submenu with 5 operations (add, list, detail, filter, query-state)
3. Exit

**Attempt Operations:**
- `_add_attempt()` — Prompts for run_id, attempt_number, status, conclusion, timestamps, duration, logs_url
- `_list_attempts()` — Lists all or calls filter
- `_detail_attempt()` — Shows single attempt
- `_filter_attempts_menu()` — Filters by run_id, status, or conclusion
- `_query_attempt_state()` — Shows state flags

**Currently Implemented:** Yes, all operations exist and menu is fully integrated.

---

## What AttemptService Needs to Implement

### Current Implementation Status

**IMPLEMENTED (Fully Functional):**
1. ✓ `WorkflowAttemptService` class exists with 7 methods
2. ✓ `add_attempt(attempt: WorkflowRunAttempt) -> WorkflowRunAttempt`
3. ✓ `get_attempt_detail(attempt_id: str) -> Optional[WorkflowRunAttempt]`
4. ✓ `filter_by_run_id(run_id: str) -> List[WorkflowRunAttempt]` — supports "retrieve by run_id"
5. ✓ JSON persistence integrated (WorkflowAttemptJsonStorage)
6. ✓ CLI commands for all operations
7. ✓ Interactive menu for all operations
8. ✓ WorkflowAttemptTracker facade for creation

**GAP - Should Have (NOT IMPLEMENTED):**
1. ✗ **Duplicate attempt number validation per run** — `add_attempt()` only checks duplicate IDs, not (run_id, attempt_number) pairs

**GAP - Could Have (NOT IMPLEMENTED):**
1. ✗ **Sorting by attempt number** — No sort method exists

---

## Integration Points with CLI/Menu System

### CLI Wiring
**File:** `src/cli/workflow_cli.py`

**Current Implementation:**
- `run_cli()` function receives both `service` and `attempt_service`
- Parser has `attempt` subcommand with 4 sub-subcommands
- All sub-subcommands are implemented in main `run_cli()` function body

**No Changes Needed:** The CLI infrastructure for AttemptService is complete. Only validation logic needs to be added to the service layer.

### Interactive Menu Wiring
**File:** `src/cli/interactive_menu.py`

**Current Implementation:**
- `run_interactive()` function receives both `service` and `attempt_service`
- Main menu has "Workflow Attempts" option
- `_attempt_menu()` function handles submenu with all 5 operations

**No Changes Needed:** The menu infrastructure for AttemptService is complete. Only validation logic needs to be added to the service layer.

### Service Initialization
**File:** `src/__main__.py`

**Current Implementation:**
- Both storage and service are created
- Both are passed to CLI and menu functions

**No Changes Needed:** Initialization is complete.

---

## Constraints and Patterns to Follow

### Validation Strategy

**Current Pattern (WorkflowRunService):**
```python
def add_workflow_run(self, run: WorkflowRun) -> WorkflowRun:
    if any(r.id == run.id for r in self._runs):
        raise ValueError(f"Run with id '{run.id}' already exists.")
    self._runs.append(run)
    self._persist()
    return run
```

**Required Pattern for Attempts:**
```python
def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
    # Existing check (keep)
    if any(a.id == attempt.id for a in self._attempts):
        raise ValueError(f"Attempt with id '{attempt.id}' already exists.")
    
    # NEW: Check for duplicate attempt number per run
    if any(a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number 
           for a in self._attempts):
        raise ValueError(
            f"Attempt number {attempt.attempt_number} already exists for run '{attempt.run_id}'."
        )
    
    self._attempts.append(attempt)
    self._persist()
    return attempt
```

### Serialization Pattern

Already implemented in WorkflowRunAttempt:
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "run_id": self.run_id,
        "attempt_number": self.attempt_number,
        "status": self.status.value,
        "conclusion": self.conclusion.value if self.conclusion else None,
        "started_at": self.started_at.isoformat(),
        "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        "duration_seconds": self.duration_seconds,
        "logs_url": self.logs_url,
    }
```

**No Changes Needed:** Serialization is correct.

### In-Memory Cache Pattern

**Current Pattern:** Load on init, cache in memory, persist on write.

This is efficient for small datasets (typical for a CLI tool) and matches WorkflowRunService exactly.

**No Changes Needed:** Pattern is sound.

---

## Data Flow for Attempts

### Creation Flow
1. **User input** (CLI args or interactive menu)
2. **WorkflowRunTracker.create_attempt()** or **WorkflowAttemptTracker.create_attempt()**
   - Creates WorkflowRunAttempt instance (id=UUID, started_at=now)
   - Calls `attempt_service.add_attempt()`
3. **WorkflowAttemptService.add_attempt()**
   - ✓ Validates no duplicate ID
   - ✗ **MISSING:** Validates no duplicate (run_id, attempt_number)
   - Appends to `self._attempts`
   - Calls `_persist()`
4. **WorkflowAttemptJsonStorage.save()**
   - Calls `attempt.to_dict()` for each attempt
   - Writes JSON array to file

### Reading Flow
1. **WorkflowAttemptJsonStorage.load()**
   - Loads JSON from file
   - Calls `WorkflowRunAttempt.from_dict()` for each item
2. **WorkflowAttemptService.__init__()**
   - Loads via storage, caches in `self._attempts`
3. **Service methods:**
   - `get_attempt_detail()` — single attempt
   - `filter_by_run_id()` — attempts for a run
   - `list_attempts()` — all attempts

---

## Summary: What Must Change

### Must Have (1 item)
| Component | Change Type | Details |
|-----------|------------|---------|
| WorkflowAttemptService.add_attempt() | Add validation | Check for duplicate (run_id, attempt_number) pairs; raise ValueError if found |

**Impact:**
- 1 method modification (add_attempt)
- No new methods needed
- No signature changes
- No storage changes
- No CLI changes
- No menu changes

### Should Have (1 item)
| Component | Change Type | Optional Details |
|-----------|------------|---------|
| WorkflowAttemptService | Add method (optional) | `get_attempts_by_run_id_sorted(run_id: str) -> List[WorkflowRunAttempt]` — returns sorted by attempt_number |

**Impact:**
- Optional: add 1 helper method for convenience
- Could also add sorting to filter_by_run_id (breaking change?)
- Could add standalone sort utility

### Could Have (1 item)
| Component | Change Type | Optional Details |
|-----------|------------|---------|
| filter_by_run_id() | Enhanced | Return results sorted by attempt_number ascending |

---

## Files to Modify

**If implementing "Should Have" validation:**
1. `src/services/workflow_attempt_service.py` — Modify `add_attempt()` method

**If implementing "Could Have" sorting:**
1. `src/services/workflow_attempt_service.py` — Modify `filter_by_run_id()` (or add new method)

**If adding tests:**
1. `tests/test_workflow_attempt_service.py` — Add tests for duplicate (run_id, attempt_number)
2. Possibly add tests for sorting

---

## Edge Cases and Considerations

### Existing Data
**Question:** If existing `workflow_attempts.json` has duplicate (run_id, attempt_number) pairs, will the validation break?

**Answer:** Yes. The validation occurs in `add_attempt()`, which is called during tracker creation and CLI commands, not during load. Existing invalid data in JSON will load silently but won't allow new duplicates to be added.

**Mitigation Options:**
1. Add validation in `from_dict()` — catches during load
2. Add cleanup method to remove/warn about duplicates
3. Accept that existing data (if any) is legacy and new data is clean

**Recommendation:** Add validation in `from_dict()` to catch corruption during deserialization (consistent with duration_seconds validation pattern).

### Attempt Number Semantics
**Question:** Is attempt_number just a counter (1, 2, 3, ...) or can it be arbitrary (1, 3, 5)?

**Answer:** From GitHub Actions, it's sequential (1-indexed). But the model doesn't enforce this; it's just an int.

**Implication:** Duplicate check is sufficient; no need to validate sequencing.

### Sorting Stability
**Question:** If we sort by attempt_number, what's the secondary sort key?

**Answer:** In current code, no secondary sort is mentioned. Could use `started_at` if needed.

**For now:** Simple sort by attempt_number is sufficient for "Could Have".

---

## Testing Gaps

### Current Test Coverage
- 105 tests pass (from progress.md)
- Test files exist for models, storage, service, tracker, CLI, menu

### Required Tests for Duplicate Validation
1. Test that duplicate (run_id, attempt_number) raises ValueError
2. Test that different attempts for same run with different numbers are allowed
3. Test that same attempt_number in different runs is allowed
4. Test error message clarity

### Optional Tests for Sorting
1. Test that filter_by_run_id returns attempts in order by attempt_number
2. Test with non-sequential attempt numbers (1, 3, 5)

---

## Summary Table

| Aspect | Status | Details |
|--------|--------|---------|
| **WorkflowAttemptService class** | ✓ Exists | 7 methods, mirrors WorkflowRunService |
| **Create attempt** | ✓ Exists | add_attempt() method |
| **Retrieve by run_id** | ✓ Exists | filter_by_run_id() method |
| **Storage integration** | ✓ Exists | WorkflowAttemptJsonStorage wired |
| **CLI accessibility** | ✓ Exists | 4 attempt subcommands implemented |
| **Menu accessibility** | ✓ Exists | 5 attempt operations in menu |
| **Duplicate ID validation** | ✓ Exists | Checked in add_attempt() |
| **Duplicate attempt# per run** | ✗ Missing | Should validate (run_id, attempt_number) |
| **Sorting by attempt#** | ✗ Missing | Could add sort logic |

---

## Files Referenced

### Key Implementation Files
- `src/models/workflow_attempt.py` — WorkflowRunAttempt dataclass
- `src/models/workflow_status.py` — WorkflowStatus enum
- `src/models/workflow_conclusion.py` — WorkflowConclusion enum
- `src/storage/workflow_attempt_json_storage.py` — JSON persistence
- `src/services/workflow_attempt_service.py` — Core service (MODIFY HERE)
- `src/services/workflow_attempt_tracker.py` — Facade for creation
- `src/services/workflow_run_tracker.py` — Facade with create_attempt method
- `src/cli/workflow_cli.py` — CLI commands (already complete)
- `src/cli/interactive_menu.py` — Menu operations (already complete)
- `src/__main__.py` — Entrypoint and initialization
- `src/models/__init__.py` — Model exports

### Test Files
- `tests/test_workflow_attempt_service.py` — Service tests (extend for validation)
- `tests/test_workflow_run_tracker_attempt.py` — Tracker tests (may extend)

### Architecture Diagrams
- `artifacts/class_diagram.puml` — Models and relationships
- `artifacts/component_diagram.puml` — System components
- `artifacts/activity_diagram_main.puml` — CLI flow
- `artifacts/activity_diagram_interactive.puml` — Menu flow

