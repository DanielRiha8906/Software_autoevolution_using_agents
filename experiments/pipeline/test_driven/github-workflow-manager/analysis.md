# Refactoring Analysis: GitHub Workflow Manager Architecture

## Task Summary

Refactor the workflow manager into clearly separated components:
- Workflow run domain logic
- Attempt management
- Statistics computation
- Storage layer
- GitHub integration layer

Preserve all existing public behavior and method signatures. No domain logic rewrites or new features.

---

## Current Structure

### File Organization

```
src/
├── __main__.py                              # Entry point, wires all services
├── models/
│   ├── workflow_run.py                      # Domain model (dataclass, 79 lines)
│   ├── workflow_run_attempt.py              # Domain model (50 lines)
│   ├── workflow_status.py                   # Enum (11 lines)
│   ├── workflow_conclusion.py               # Enum (13 lines)
│   └── workflow_statistics_report.py        # Data transfer object (14 lines)
├── services/
│   ├── workflow_run_service.py              # Workflow run CRUD and queries (137 lines)
│   ├── attempt_service.py                   # Attempt in-memory storage (63 lines)
│   ├── workflow_run_tracker.py              # Facade for tracking new runs (39 lines)
│   ├── workflow_statistics_service.py       # Statistics computation (92 lines)
│   ├── github_fetch_service.py              # GitHub CLI integration (250 lines)
│   └── workflow_import_export_service.py    # Import/export with validation (252 lines)
├── storage/
│   └── workflow_json_storage.py             # JSON file persistence (22 lines)
└── cli/
    ├── workflow_cli.py                      # CLI command handler
    └── interactive_menu.py                  # Interactive menu UI

tests/
├── test_workflow_run.py
├── test_workflow_run_attempt.py
├── test_attempt_service.py
├── test_workflow_run_service.py
├── test_workflow_json_storage.py
├── test_github_fetch_service.py
├── test_workflow_statistics_service.py
├── test_duration_seconds.py
└── services/
    └── test_workflow_run_service_query.py
```

---

## Current Responsibilities (Mixed in Services)

### WorkflowRunService (137 lines)
**Current responsibilities:**
1. **Run storage/persistence**: Holds in-memory list, syncs to storage via `_persist()`
2. **Run CRUD**: `add_workflow_run()`, `get_run_detail()`, `list_runs()`
3. **Run filtering**: `filter_by_branch()`, `filter_by_status()`, `filter_by_conclusion()`
4. **Complex querying**: `query()` method with 6 optional parameters (duration, timestamps, attempts)
5. **Storage coupling**: Direct dependency on `WorkflowJsonStorage`
6. **Attempt service coupling**: Optional dependency in `query()` method for attempt filtering

**What should be separated:**
- Domain logic for run state transitions, validation (currently inline in models, OK to keep)
- Query logic could be factored out, but `query()` is already a public API tested extensively
- Filtering methods are queryable operations, could be composed

### AttemptService (63 lines)
**Current responsibilities:**
1. **Attempt in-memory storage**: Holds list without persistence
2. **Attempt creation**: `create()` with duplicate prevention
3. **Attempt retrieval**: `get_by_run_id()`, `get_all_attempts()`

**What should be separated:**
- Storage layer is minimal and focused; separation not urgent
- Could extract interface but tight coupling to WorkflowRunAttempt is appropriate

### WorkflowStatisticsService (92 lines)
**Current responsibilities:**
1. **Statistics computation**: Aggregates runs and attempts
2. **Count by conclusion**: Only COMPLETED runs, grouped by conclusion enum
3. **Duration metrics**: avg, min, max across all runs
4. **Attempt metrics**: average attempts per run (includes zero-attempt runs)

**What should be separated:**
- Statistics computation is domain logic, should remain
- Could extract to separate "statistics domain" but lightweight enough to keep together

### GitHubFetchService (250 lines)
**Current responsibilities:**
1. **Token resolution**: 3-step priority (env, file, user input)
2. **GitHub CLI subprocess invocation**: Builds and runs `gh run list` command
3. **JSON response parsing**: Handles both camelCase and snake_case field names
4. **Domain model conversion**: Maps GitHub API response to WorkflowRun with enums
5. **Timezone handling**: Converts Z-suffix UTC to Python ISO format

**What should be separated:**
- Token resolution logic (not used by any other service)
- Subprocess invocation (GitHub-specific)
- Response parsing (GitHub API schema specific)
- Type conversion (could be stateless utility, but kept here is fine)

### WorkflowImportExportService (252 lines)
**Current responsibilities:**
1. **Export**: Serializes runs and attempts to JSON string
2. **Import**: Reads JSON file and validates comprehensively
3. **Schema validation**: Enum values, ISO 8601 dates, timezone awareness
4. **Deduplication logic**: Skips existing runs/attempts during import
5. **Error reporting**: `SchemaValidationError` exception

**What should be separated:**
- Validation logic is tightly coupled to import, appropriate to keep
- Export logic is simple (just serialization), OK to keep
- Could extract to separate validator class but import/export are minimal

### WorkflowRunTracker (39 lines)
**Current responsibilities:**
1. **Run creation facade**: Takes parameters, creates `WorkflowRun` with defaults
2. **Auto-UUID generation**: Generates UUID if run_id not provided
3. **Timestamp injection**: Sets `created_at` to UTC now
4. **Service delegation**: Calls `add_workflow_run()` on WorkflowRunService

**What should be separated:**
- This is already a focused facade; no separation needed

### WorkflowJsonStorage (22 lines)
**Current responsibilities:**
1. **File I/O**: Reads and writes JSON
2. **Directory creation**: Creates parent directories as needed
3. **Model serialization**: Calls `to_dict()` and `from_dict()`

**What should be separated:**
- Already minimal and focused
- Could extract interface, but no other storage implementations exist

---

## Public API (Must Preserve)

### Models (Dataclasses & Enums)
**Imported by tests and CLI:**
- `WorkflowRun` — 10 fields, serializable via `to_dict()`/`from_dict()`
  - Public methods: `is_running()`, `is_terminal()`, `is_successful()`, `is_failed()`, `is_cancelled()`
- `WorkflowRunAttempt` — 7 fields (id, run_id, attempt_number, status, conclusion, created_at, duration_seconds)
  - Public methods: `to_dict()`, `from_dict()` 
- `WorkflowStatus` enum — QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING
- `WorkflowConclusion` enum — SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE
- `WorkflowStatisticsReport` — dataclass with 5 fields (count_by_conclusion, avg/min/max_duration_seconds, avg_attempts_per_run)

### Service Interfaces (Required Signatures)
**WorkflowRunService:**
```python
__init__(storage: WorkflowJsonStorage) -> None
add_workflow_run(run: WorkflowRun) -> WorkflowRun
list_runs() -> List[WorkflowRun]
get_run_detail(run_id: str) -> Optional[WorkflowRun]
filter_by_branch(branch: str) -> List[WorkflowRun]
filter_by_status(status: WorkflowStatus) -> List[WorkflowRun]
filter_by_conclusion(conclusion: WorkflowConclusion) -> List[WorkflowRun]
query(min_duration, max_duration, created_after, created_before, has_attempts, attempt_service) -> List[WorkflowRun]
```

**AttemptService:**
```python
__init__() -> None
create(attempt: WorkflowRunAttempt) -> WorkflowRunAttempt
get_by_run_id(run_id: int) -> List[WorkflowRunAttempt]
get_all_attempts() -> List[WorkflowRunAttempt]
```

**WorkflowRunTracker:**
```python
__init__(service: WorkflowRunService) -> None
track(workflow_name, branch, status, conclusion, run_number, commit_sha, run_id) -> WorkflowRun
```

**WorkflowStatisticsService:**
```python
__init__(workflow_run_service: WorkflowRunService) -> None
compute(attempt_service: Optional[AttemptService] = None) -> WorkflowStatisticsReport
```

**GitHubFetchService:**
```python
__init__(secrets_path: Optional[str] = None) -> None
resolve_token() -> str
fetch(owner: str, repo: str) -> List[WorkflowRun]
```

**WorkflowImportExportService:**
```python
__init__(workflow_run_service, attempt_service) -> None
export() -> str
import_from(filepath: str) -> None
```

**WorkflowJsonStorage:**
```python
__init__(filepath: str = "artifacts/workflow_runs.json") -> None
save(runs: List[WorkflowRun]) -> None
load() -> List[WorkflowRun]
```

### Storage Exception
- `SchemaValidationError` exception (raised by WorkflowImportExportService)

---

## Refactoring Requirements (What Needs to Change)

### Goal: Separate Into 5 Components

#### 1. Workflow Run Domain Logic
**Purpose:** Encapsulate workflow run state transitions and queries

**Should contain:**
- `WorkflowRun` model (already clean)
- `WorkflowStatus`, `WorkflowConclusion` enums (already clean)
- Query operations (currently in WorkflowRunService)
- State validation methods (is_running, is_terminal, etc. — already in WorkflowRun)

**Should NOT contain:**
- Persistence layer
- Storage I/O
- Import/export logic

**Proposed structure:**
- Keep `WorkflowRun`, `WorkflowStatus`, `WorkflowConclusion` in models/
- Consider extracting query logic to a separate `QueryBuilder` or keeping in service layer
- Keep `is_*()` methods in WorkflowRun

#### 2. Attempt Management
**Purpose:** Isolate attempt tracking and aggregation from run logic

**Should contain:**
- `WorkflowRunAttempt` model
- `AttemptService` (minimal in-memory storage)
- Attempt validation (attempt_number > 0, CEST timezone)

**Should NOT contain:**
- Workflow run operations
- Statistics aggregation

**Current state:**
- Already well-separated; no major changes needed
- AttemptService is already focused

#### 3. Statistics Computation
**Purpose:** Aggregate metrics from runs and attempts

**Should contain:**
- `WorkflowStatisticsService` (computes aggregates)
- `WorkflowStatisticsReport` (data transfer object)
- Statistics logic (count by conclusion, duration stats, attempt stats)

**Should NOT contain:**
- Run storage
- Run queries
- Attempt storage

**Current state:**
- Already extracted; well-separated
- No changes needed

#### 4. Storage Layer
**Purpose:** Abstract persistence and I/O

**Should contain:**
- `WorkflowJsonStorage` (file I/O)
- Interface/abstract base class for storage
- Serialization logic (to_dict/from_dict handling)

**Should NOT contain:**
- Business logic
- Domain model definitions (only use them)
- Query logic

**Current state:**
- Already focused and minimal
- Could extract interface for extensibility
- `WorkflowImportExportService` currently couples to both services; should use storage abstraction

#### 5. GitHub Integration Layer
**Purpose:** Isolate all GitHub-specific code

**Should contain:**
- `GitHubFetchService` (subprocess, token resolution, API mapping)
- GitHub-specific response parsing
- GitHub field name conversions

**Should NOT contain:**
- Domain model definitions
- General persistence logic

**Current state:**
- Already isolated; no major changes needed
- Token resolution is GitHub-specific but reasonable to keep here

---

## Dependencies and Circular Dependencies

### Current Dependency Graph

```
WorkflowRunService
  ├─ depends on: WorkflowJsonStorage
  ├─ depends on: WorkflowRun, WorkflowStatus, WorkflowConclusion
  └─ optionally depends on: AttemptService (in query())

AttemptService
  └─ depends on: WorkflowRunAttempt

WorkflowRunTracker
  ├─ depends on: WorkflowRunService
  ├─ depends on: WorkflowRun, WorkflowStatus, WorkflowConclusion

WorkflowStatisticsService
  ├─ depends on: WorkflowRunService
  ├─ depends on: AttemptService (optional, in compute())
  ├─ depends on: WorkflowStatisticsReport

GitHubFetchService
  └─ depends on: WorkflowRun, WorkflowStatus, WorkflowConclusion

WorkflowImportExportService
  ├─ depends on: WorkflowRunService
  ├─ depends on: AttemptService
  ├─ depends on: WorkflowRun, WorkflowRunAttempt
  ├─ depends on: WorkflowStatus, WorkflowConclusion

WorkflowJsonStorage
  └─ depends on: WorkflowRun
```

### Circular Dependencies
**NONE DETECTED** — Dependency graph is acyclic. All dependencies flow downward (services → models → enums).

### Coupling Issues to Address

1. **WorkflowRunService couples to specific storage implementation (WorkflowJsonStorage)**
   - **Issue:** Cannot swap storage implementations
   - **Fix:** Extract interface `WorkflowStorage` with `load()` and `save()` methods
   - **Impact:** Allow alternate storage backends

2. **WorkflowImportExportService couples directly to services (not storage abstraction)**
   - **Current:** Uses `WorkflowRunService.add_workflow_run()`, `AttemptService.create()`
   - **Fix:** Keep as-is; coupling to service behavior is appropriate for import
   - **Reasoning:** Import needs to trigger duplicate checks and validation in services

3. **AttemptService has no persistence layer**
   - **Current:** In-memory only; data lost on restart
   - **Issue:** Workflow runs persist, but attempts don't
   - **Fix:** Optional: Add storage layer for attempts (out of scope for this refactoring)
   - **Note:** Currently by design; tests assume in-memory

4. **Model dependencies on enums**
   - **Current:** WorkflowRun imports WorkflowStatus, WorkflowConclusion
   - **Status:** Appropriate; enums are lightweight domain types
   - **No change needed**

---

## Implementation Constraints

### What Must Be Preserved (Hard Constraints)

1. **Public method signatures** — All listed in "Public API" section must remain unchanged
2. **Domain logic** — No rewriting of WorkflowRun.is_*() methods or query logic
3. **Exception types** — SchemaValidationError must remain
4. **Model fields** — All dataclass fields must exist with same names and types
5. **Enum values** — WorkflowStatus and WorkflowConclusion values must not change
6. **File format** — JSON storage format (key names, structure) must remain compatible

### What Can Be Changed (Scope for Refactoring)

1. **Internal structure** — Reorganize code within services without changing public API
2. **Private methods** — Refactor internal helper methods as needed
3. **Dependency injection** — Extract interfaces, inject abstractions instead of concrete types
4. **Code organization** — Move utility functions, consolidate related logic
5. **Intermediate layers** — Add repositories, repositories, query builders without breaking public API

### Test Coverage
- **95+ tests** across all components
- **All public API methods** are tested
- **Edge cases** (empty datasets, duplicates, invalid enums) are covered
- **Tests import directly from modules** — Refactoring must not break import paths

---

## Separation Strategy

### Phase 1: Storage Abstraction
1. Extract `WorkflowStorage` interface from `WorkflowJsonStorage`
2. Update `WorkflowRunService.__init__()` to accept storage interface
3. Update `WorkflowImportExportService` to work with storage abstraction
4. **No public API change** — constructor signature same (accept subclass of interface)

### Phase 2: Workflow Run Domain Logic Isolation
1. Create `workflow_run_domain.py` or `query_builder.py` for complex query logic
2. Keep `WorkflowRun` in models/ (already clean)
3. Optionally extract filtering logic to separate class
4. Keep `WorkflowRunService` as facade over storage and domain logic
5. **No public API change** — methods stay in WorkflowRunService

### Phase 3: Attempt Management Isolation
1. AttemptService already isolated; minimal changes needed
2. Could add optional storage layer (out of scope)
3. **No public API change**

### Phase 4: Statistics Computation Isolation
1. Already isolated; no changes needed
2. WorkflowStatisticsService is pure computation
3. **No public API change**

### Phase 5: GitHub Integration Isolation
1. Already isolated; no changes needed
2. Could extract token resolution to separate class
3. **No public API change**

### Phase 6: Testing & Diagram Updates
1. Run full test suite to verify preservation
2. Update UML diagrams to reflect new module organization
3. Update component diagram to show 5 clear layers

---

## Key Findings

### Architecture is Already Reasonably Separated
- **Models** are domain-focused (no service logic)
- **Services** are responsibility-specific (no cross-cutting concerns)
- **Storage** is minimal and focused
- **GitHub integration** is isolated

### Primary Refactoring Opportunity
1. **Extract storage interface** to enable swappable implementations
2. **Clarify module boundaries** to explicitly name the 5 components
3. **Organize code** into distinct subpackages if desired

### No Rewrites Needed
- Domain logic in WorkflowRun is clean
- Query logic in WorkflowRunService is well-tested
- Statistics computation is appropriate
- Import/export validation is thorough

### Circular Dependency Risk: NONE
- All dependencies flow in single direction
- No bidirectional coupling detected
- Safe to refactor with confidence

---

## Recommendations for Architect

1. **Extract WorkflowStorage interface** to decouple from JsonStorage
2. **Consider package reorganization:**
   ```
   src/
   ├── domain/          # WorkflowRun, WorkflowRunAttempt, enums
   ├── queries/         # Query logic (optional separate module)
   ├── statistics/      # WorkflowStatisticsService, report
   ├── attempts/        # AttemptService (could be separate subpackage)
   ├── storage/         # Storage interface + implementations
   ├── github/          # GitHubFetchService
   ├── import_export/   # WorkflowImportExportService
   └── cli/             # CLI interface
   ```
3. **Keep public method signatures identical** to avoid breaking tests
4. **Run full test suite after refactoring** to verify no regressions
5. **Update diagrams** to show clear 5-component separation

---

## Summary

The codebase is already well-structured with clear separation of concerns. The main refactoring opportunity is:

1. **Extract storage abstraction** (WorkflowStorage interface) to enable flexibility
2. **Reorganize code** into explicitly named components (domain, statistics, attempts, storage, github)
3. **Preserve all public APIs** — no signature changes, no domain logic rewrites

**Complexity: Low-to-Medium** — Mostly reorganization; no complex logic rewrite.
**Risk: Low** — Circular dependency-free; good test coverage; public APIs well-defined.
**Estimated scope:** 1-2 programmer tasks with refactoring + 1 tester task to verify.

