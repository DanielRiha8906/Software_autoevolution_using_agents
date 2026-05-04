# GitHub Workflow Manager - Layer Separation Analysis

## Current Architecture and Layer Identification

### Layer Structure (Current)

The codebase has three logical layers currently intermingled:

1. **Service Layer** (`src/services/`)
   - `WorkflowRunService` — core business logic for workflow runs (CRUD, filtering, querying)
   - `WorkflowRunAttemptService` — manages workflow run attempts
   - `WorkflowRunTracker` — facade that creates and tracks runs
   - `StatisticsService` — computes aggregated statistics
   - `WorkflowRunExportImportService` — handles export/import operations
   - `GitHubAPIFetcher` — REST API adapter (GitHub integration)
   - `GitHubCLIFetcher` — CLI adapter (GitHub integration)

2. **Storage Layer** (`src/storage/`)
   - `WorkflowJsonStorage` — JSON file persistence (single class)

3. **GitHub Adapter Layer** (currently split across services and auth)
   - `GitHubAuthManager` (`src/auth/`) — authentication token management
   - `GitHubWorkflowRunFactory` (`src/models/`) — GitHub API → domain model conversion
   - `GitHubAPIFetcher` (`src/services/`) — REST API integration
   - `GitHubCLIFetcher` (`src/services/`) — CLI integration
   - Exception classes (`src/exceptions/`) — GitHub-specific errors

4. **Models/Domain** (`src/models/`)
   - Pure domain objects: `WorkflowRun`, `WorkflowRunAttempt`, `WorkflowStatus`, `WorkflowConclusion`
   - DTOs/Reports: `StatisticsReport`, `ImportResult`
   - Factory: `GitHubWorkflowRunFactory` (belongs in adapter, not models)

5. **CLI/Interface** (`src/cli/`)
   - `workflow_cli` — command-line interface
   - `interactive_menu` — interactive menu interface

### Dependency Graph

```
                              ┌──────────────────────┐
                              │   CLI Layer          │
                              │  (workflow_cli,      │
                              │ interactive_menu)    │
                              └──────┬───────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
    ┌────▼─────────────┐    ┌────────▼──────────┐   ┌────────────▼────────┐
    │ Service Layer    │    │ GitHub Adapter    │   │ Auth Layer          │
    │                  │    │                   │   │                     │
    │ WorkflowRunSvc   │◄───┤ GitHubAPIFetcher  │   │ GitHubAuthManager   │
    │ WorkflowAttempt  │    │ GitHubCLIFetcher  │   │                     │
    │ WorkflowTracker  │    │ Factory (models)  │   └─────────────────────┘
    │ StatisticsSvc    │    └───────┬───────────┘
    │ ExportImportSvc  │            │
    └────┬─────────────┘      ┌─────▼──────────┐
         │                    │ Exceptions     │
         │                    │ (all layers)   │
         │                    └────────────────┘
         │
    ┌────▼──────────────┐
    │ Storage Layer     │
    │                   │
    │ WorkflowJsonStor  │
    └────┬──────────────┘
         │
         └──► Models (WorkflowRun, etc.)
```

---

## Circular Dependencies and Coupling Issues

### Issue 1: Service Layer Directly Uses Storage

**Location:** `src/services/workflow_run_service.py`, `src/services/workflow_run_attempt_service.py`

**Problem:**
- Both services receive `WorkflowJsonStorage` in constructor
- Services directly call `storage.load()` and `storage.save()`
- No abstraction between service and storage layer
- Tight coupling makes testing difficult and prevents swapping storage backends

**Evidence:**
```python
# workflow_run_service.py
def __init__(self, storage: WorkflowJsonStorage):
    self._storage = storage
    self._runs: List[WorkflowRun] = storage.load()

def _persist(self) -> None:
    self._storage.save(self._runs)
```

**Impact:** Cannot substitute storage implementation without modifying services.

---

### Issue 2: GitHub Adapter Coupled to Service Layer

**Location:** `src/services/github_api_fetcher.py` and `src/services/github_cli_fetcher.py`

**Problem:**
- GitHub fetchers return `WorkflowRun` (domain model) directly
- Use `GitHubWorkflowRunFactory` (currently in models) to convert API responses
- CLI layer directly instantiates fetchers and calls them
- No common interface between `GitHubAPIFetcher` and `GitHubCLIFetcher`
- Both fetchers are in the service layer, not clearly separated as adapters

**Evidence:**
```python
# workflow_cli.py (CLI layer calling adapters directly)
api_fetcher = GitHubAPIFetcher(token)
cli_fetcher = GitHubCLIFetcher()
# Then: api_fetcher.fetch_runs(...), cli_fetcher.fetch_runs(...)
```

**Impact:** 
- No way to swap or extend GitHub sources without modifying CLI
- Inconsistent error handling between two similar components
- Factory logic buried in models layer

---

### Issue 3: WorkflowRunExportImportService Directly Accesses Service Internals

**Location:** `src/services/workflow_export_import_service.py`

**Problem:**
- Imports from `workflows_run_service` and `workflow_run_attempt_service`
- Directly manipulates `service._runs` (private attribute)
- Directly manipulates `attempt_service._attempts` (private attribute)
- Calls private `_persist()` method

**Evidence:**
```python
# workflow_export_import_service.py
service._runs = [r for r in service._runs if r.id != run.id]
service._runs.append(run)
service._persist()

attempt_service._attempts = [a for a in attempt_service._attempts if a.id != attempt.id]
attempt_service._persist()
```

**Impact:** 
- Violates encapsulation
- If service layer changes, import/export breaks
- Makes refactoring the service layer risky

---

### Issue 4: CLI Layer Has Wide Dependencies

**Location:** `src/cli/workflow_cli.py`, `src/cli/interactive_menu.py`

**Problem:**
- CLI imports directly from services, auth, adapters, exceptions, models
- 18+ direct imports from different layers
- Mixes service instantiation with CLI logic
- No dependency injection; CLI creates instances directly

**Evidence:**
```python
# workflow_cli.py imports
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.statistics_service import StatisticsService
from ..services.workflow_export_import_service import WorkflowRunExportImportService
from ..services.github_api_fetcher import GitHubAPIFetcher
from ..services.github_cli_fetcher import GitHubCLIFetcher
from ..auth.github_auth import GitHubAuthManager
# ... + exceptions, models
```

**Impact:** 
- Difficult to test CLI in isolation
- Adding new service requires modifying CLI imports
- Hard to understand service dependencies from CLI code

---

### Issue 5: GitHub Adapter Logic Distributed Across Three Locations

**Location:** `src/services/` (fetchers), `src/models/` (factory), `src/auth/` (auth manager), `src/exceptions/` (errors)

**Problem:**
- `GitHubAPIFetcher` and `GitHubCLIFetcher` in services layer
- `GitHubWorkflowRunFactory` in models layer
- `GitHubAuthManager` in auth layer (separate from fetchers)
- GitHub-specific exceptions in exceptions layer
- No cohesive "GitHub adapter" module

**Impact:**
- GitHub adapter logic scattered across codebase
- Cannot easily swap GitHub for another provider
- Adding new GitHub features requires changes in multiple places

---

## Public Interfaces That Must Be Preserved

### Explicitly Public (used by CLI/main)

1. **WorkflowRunService**
   ```python
   def __init__(self, storage: WorkflowJsonStorage)
   def list_runs() -> List[WorkflowRun]
   def get_run_detail(run_id: str) -> Optional[WorkflowRun]
   def add_workflow_run(run: WorkflowRun) -> WorkflowRun
   def filter_by_branch(branch: str) -> List[WorkflowRun]
   def filter_by_status(status: WorkflowStatus) -> List[WorkflowRun]
   def filter_by_conclusion(conclusion: WorkflowConclusion) -> List[WorkflowRun]
   def filter_by_created_after(threshold_date: datetime) -> List[WorkflowRun]
   def filter_by_created_before(threshold_date: datetime) -> List[WorkflowRun]
   def filter_by_duration_min(min_seconds: float) -> List[WorkflowRun]
   def filter_by_duration_max(max_seconds: float) -> List[WorkflowRun]
   def filter_by_attempt_presence(attempt_service, has_attempts: bool) -> List[WorkflowRun]
   def query(...) -> List[WorkflowRun]
   ```

2. **WorkflowRunAttemptService**
   ```python
   def __init__(self, storage: WorkflowJsonStorage)
   def list_attempts(sorted: bool = True) -> List[WorkflowRunAttempt]
   def get_attempt(attempt_id: int) -> Optional[WorkflowRunAttempt]
   def get_attempts_for_run(run_id: int, sorted: bool = True) -> List[WorkflowRunAttempt]
   def add_attempt(attempt: WorkflowRunAttempt) -> WorkflowRunAttempt
   ```

3. **WorkflowRunTracker**
   ```python
   def __init__(self, service: WorkflowRunService)
   def track(workflow_name, branch, status, conclusion, run_number, commit_sha, run_id, duration_seconds) -> WorkflowRun
   ```

4. **StatisticsService**
   ```python
   def calculate_statistics(runs: List[WorkflowRun], attempt_service: Optional[...]) -> StatisticsReport
   ```

5. **WorkflowRunExportImportService**
   ```python
   def export_to_file(filepath, service, attempt_service, include_attempts)
   def import_from_file(filepath, service, attempt_service, overwrite, dry_run) -> ImportResult
   ```

6. **GitHubAPIFetcher**
   ```python
   def __init__(self, token: str)
   def fetch_runs(owner, repo, status, branch, created_after, per_page) -> List[WorkflowRun]
   ```

7. **GitHubCLIFetcher**
   ```python
   def is_available() -> bool
   def fetch_runs(owner, repo, status, branch, created_after) -> List[WorkflowRun]
   ```

8. **GitHubAuthManager**
   ```python
   def get_token(explicit_token: Optional[str]) -> str
   def validate_token(token: str) -> bool
   ```

9. **WorkflowJsonStorage**
   ```python
   def __init__(filepath, attempts_filepath)
   def save(runs: List[WorkflowRun])
   def load() -> List[WorkflowRun]
   def save_attempts(attempts: List[WorkflowRunAttempt])
   def load_attempts() -> List[WorkflowRunAttempt]
   ```

10. **Domain Models** (used everywhere)
    - `WorkflowRun`, `WorkflowRunAttempt`, `WorkflowStatus`, `WorkflowConclusion`
    - `StatisticsReport`, `ImportResult`

11. **Exception Classes** (must exist and be importable)
    - `GitHubAuthError`, `GitHubAPIError`, `GitHubNetworkError`, `GitHubRateLimitError`

12. **Factory**
    - `GitHubWorkflowRunFactory.from_github_api_response(data: dict) -> WorkflowRun`

### Entry Point
- `src/__main__.py` — calls `WorkflowJsonStorage`, `WorkflowRunService`, `WorkflowRunAttemptService`, `run_cli()`, `run_interactive()`

---

## Required Abstractions for Decoupling

### 1. Storage Interface (Protocol)

**Purpose:** Decouple services from JSON storage implementation

**Location:** `src/storage/base.py` (new file)

```python
from typing import Protocol, List
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt

class WorkflowRunStorage(Protocol):
    """Abstract storage contract for workflow runs."""
    
    def save(self, runs: List[WorkflowRun]) -> None:
        """Persist workflow runs."""
        ...
    
    def load(self) -> List[WorkflowRun]:
        """Load all workflow runs."""
        ...

class WorkflowRunAttemptStorage(Protocol):
    """Abstract storage contract for workflow run attempts."""
    
    def save_attempts(self, attempts: List[WorkflowRunAttempt]) -> None:
        """Persist workflow run attempts."""
        ...
    
    def load_attempts(self) -> List[WorkflowRunAttempt]:
        """Load all workflow run attempts."""
        ...
```

**Impact on Services:**
- `WorkflowRunService.__init__()` changes parameter type from `WorkflowJsonStorage` → `WorkflowRunStorage`
- `WorkflowRunAttemptService.__init__()` changes parameter type from `WorkflowJsonStorage` → `WorkflowRunAttemptStorage`
- No change to method signatures; backward compatible at call site

**Rationale:**
- Protocols are duck-typed, so existing `WorkflowJsonStorage` still satisfies the contract
- Allows testing with mock storage
- Allows swapping to database, Redis, S3, etc. without touching service code

---

### 2. GitHub Fetcher Interface (Protocol + Adapter Consolidation)

**Purpose:** Unify fetcher interfaces and make them interchangeable

**Location:** `src/adapters/github/base.py` (new file)

```python
from typing import Protocol, List, Optional
from datetime import datetime
from ...models.workflow_run import WorkflowRun

class WorkflowFetcher(Protocol):
    """Abstract interface for fetching workflow runs from any source."""
    
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from source."""
        ...
```

**Changes Required:**
1. Create `src/adapters/` directory
2. Create `src/adapters/github/` subdirectory
3. Move `GitHubAPIFetcher` from `src/services/github_api_fetcher.py` → `src/adapters/github/api_fetcher.py`
4. Move `GitHubCLIFetcher` from `src/services/github_cli_fetcher.py` → `src/adapters/github/cli_fetcher.py`
5. Move `GitHubWorkflowRunFactory` from `src/models/` → `src/adapters/github/factory.py`
6. Move `GitHubAuthManager` from `src/auth/` → `src/adapters/github/auth.py`
7. Move GitHub exceptions to `src/adapters/github/exceptions.py` (or keep in `src/exceptions/`)

**Rationale:**
- Consolidates all GitHub-specific logic in one place
- Makes it easy to swap GitHub for GitLab, Bitbucket, etc.
- Isolates GitHub API version changes and quirks
- Clarifies that fetchers are adapters, not services

---

### 3. Export/Import Service Refactoring

**Purpose:** Eliminate direct access to service internals

**Location:** Add methods to `WorkflowRunService` and `WorkflowRunAttemptService`

**New Public Methods:**

In `WorkflowRunService`:
```python
def replace_run(self, run: WorkflowRun) -> None:
    """Replace existing run or add if not exists. For import operations."""
    self._runs = [r for r in self._runs if r.id != run.id]
    self._runs.append(run)
    self._persist()

def delete_run(self, run_id: str) -> bool:
    """Delete run by id. Returns True if deleted, False if not found."""
    original_count = len(self._runs)
    self._runs = [r for r in self._runs if r.id != run_id]
    if len(self._runs) < original_count:
        self._persist()
        return True
    return False
```

In `WorkflowRunAttemptService`:
```python
def replace_attempt(self, attempt: WorkflowRunAttempt) -> None:
    """Replace existing attempt or add if not exists. For import operations."""
    self._attempts = [a for a in self._attempts if a.id != attempt.id]
    self._attempts.append(attempt)
    self._persist()

def delete_attempt(self, attempt_id: int) -> bool:
    """Delete attempt by id. Returns True if deleted, False if not found."""
    original_count = len(self._attempts)
    self._attempts = [a for a in self._attempts if a.id != attempt_id]
    if len(self._attempts) < original_count:
        self._persist()
        return True
    return False
```

**Updated `WorkflowRunExportImportService`:**
```python
# Before (violates encapsulation)
service._runs = [r for r in service._runs if r.id != run.id]
service._runs.append(run)
service._persist()

# After (uses public API)
service.replace_run(run)
```

**Rationale:**
- Eliminates private member access
- Makes import/export operations explicit and testable
- Service layer controls persistence guarantees

---

### 4. Service Layer Facade (Optional but Recommended)

**Purpose:** Simplify CLI's dependencies; provide unified entry point

**Location:** `src/services/workflow_service_container.py` (new file)

```python
from .workflow_run_service import WorkflowRunService
from .workflow_run_attempt_service import WorkflowRunAttemptService
from .workflow_run_tracker import WorkflowRunTracker
from .statistics_service import StatisticsService
from .workflow_export_import_service import WorkflowRunExportImportService
from ..storage.workflow_json_storage import WorkflowJsonStorage

class WorkflowServiceContainer:
    """Facade providing unified access to all workflow services."""
    
    def __init__(self, storage: WorkflowJsonStorage):
        self.runs = WorkflowRunService(storage)
        self.attempts = WorkflowRunAttemptService(storage)
        self.tracker = WorkflowRunTracker(self.runs)
        self.statistics = StatisticsService()
        self.export_import = WorkflowRunExportImportService()
```

**CLI Usage:**
```python
# Before
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.statistics_service import StatisticsService
from ..services.workflow_export_import_service import WorkflowRunExportImportService

service = WorkflowRunService(storage)
attempt_service = WorkflowRunAttemptService(storage)
tracker = WorkflowRunTracker(service)
stats = StatisticsService()

# After
from ..services.workflow_service_container import WorkflowServiceContainer

container = WorkflowServiceContainer(storage)
service = container.runs
attempt_service = container.attempts
tracker = container.tracker
stats = container.statistics
```

**Rationale:**
- Single import in CLI instead of many
- Service dependencies managed in one place
- Easier to test with mock container
- Better dependency graph visibility

---

## Circular Dependencies Analysis

### Current Flow (No True Cycles, But Tight Coupling)

1. CLI → Services → Storage → Models ✓ (acyclic)
2. CLI → GitHub Adapters → Models → Exceptions ✓ (acyclic)
3. Services → Storage → Models ✓ (acyclic)

**However:**
- `GitHubWorkflowRunFactory` is in models but only used by adapters → should move to adapters
- `ExportImportService` accesses `_runs` and `_persist()` → should use public API
- `GitHubCLIFetcher` and `GitHubAPIFetcher` have no shared interface → should both implement protocol

**No true circular dependencies detected**, but poor separation causes:
- Tight coupling (hard to test)
- Unclear responsibilities (adapters mixed with services)
- Encapsulation violations (private member access from export/import)

---

## Minimal Structural Changes Needed

### Directory Structure Changes

```
BEFORE:
src/
  ├── auth/
  │   ├── __init__.py
  │   └── github_auth.py
  ├── models/
  │   ├── __init__.py
  │   ├── github_workflow_run_factory.py
  │   ├── workflow_*.py
  │   ├── statistics_report.py
  │   └── import_result.py
  ├── services/
  │   ├── __init__.py
  │   ├── github_api_fetcher.py
  │   ├── github_cli_fetcher.py
  │   ├── statistics_service.py
  │   ├── workflow_export_import_service.py
  │   ├── workflow_run_service.py
  │   ├── workflow_run_attempt_service.py
  │   └── workflow_run_tracker.py
  ├── storage/
  │   ├── __init__.py
  │   └── workflow_json_storage.py
  ├── exceptions/
  │   ├── __init__.py
  │   └── github_exceptions.py
  └── cli/
      ├── __init__.py
      ├── interactive_menu.py
      └── workflow_cli.py

AFTER:
src/
  ├── adapters/
  │   ├── __init__.py
  │   └── github/
  │       ├── __init__.py
  │       ├── api_fetcher.py          (moved from services)
  │       ├── cli_fetcher.py          (moved from services)
  │       ├── factory.py              (moved from models)
  │       ├── auth.py                 (moved from auth/)
  │       └── exceptions.py           (or keep in src/exceptions)
  ├── models/                          (unchanged)
  │   ├── __init__.py
  │   ├── workflow_*.py
  │   ├── statistics_report.py
  │   └── import_result.py
  ├── services/                        (only core services)
  │   ├── __init__.py
  │   ├── base.py                     (storage protocols)
  │   ├── statistics_service.py
  │   ├── workflow_export_import_service.py
  │   ├── workflow_run_service.py      (refactored: no _persist private access)
  │   ├── workflow_run_attempt_service.py (refactored: no _persist private access)
  │   ├── workflow_run_tracker.py
  │   └── workflow_service_container.py (new: facade)
  ├── storage/                         (unchanged)
  │   ├── __init__.py
  │   ├── base.py                     (new: protocols)
  │   └── workflow_json_storage.py
  ├── exceptions/                      (unchanged or with GitHub moved out)
  │   ├── __init__.py
  │   └── github_exceptions.py
  └── cli/
      ├── __init__.py
      ├── interactive_menu.py
      └── workflow_cli.py
```

### Files to Create (6 new files)

1. `src/adapters/__init__.py` — empty
2. `src/adapters/github/__init__.py` — re-exports
3. `src/adapters/github/base.py` — protocol for `WorkflowFetcher`
4. `src/storage/base.py` — protocols for `WorkflowRunStorage`, `WorkflowRunAttemptStorage`
5. `src/services/workflow_service_container.py` — facade (optional but recommended)

### Files to Move (5 moves)

1. `src/services/github_api_fetcher.py` → `src/adapters/github/api_fetcher.py`
2. `src/services/github_cli_fetcher.py` → `src/adapters/github/cli_fetcher.py`
3. `src/models/github_workflow_run_factory.py` → `src/adapters/github/factory.py`
4. `src/auth/github_auth.py` → `src/adapters/github/auth.py`
5. `src/exceptions/github_exceptions.py` → `src/adapters/github/exceptions.py` (optional; can stay in exceptions)

### Files to Modify (8 files)

1. `src/services/workflow_run_service.py`
   - Change: `def __init__(self, storage: WorkflowJsonStorage)` → `def __init__(self, storage: WorkflowRunStorage)`
   - Add: `replace_run()`, `delete_run()` public methods
   - No logic changes; protocol typing only

2. `src/services/workflow_run_attempt_service.py`
   - Change: `def __init__(self, storage: WorkflowJsonStorage)` → `def __init__(self, storage: WorkflowRunAttemptStorage)`
   - Add: `replace_attempt()`, `delete_attempt()` public methods
   - No logic changes; protocol typing only

3. `src/services/workflow_export_import_service.py`
   - Change: `service._runs.append()` → `service.replace_run()`
   - Change: `attempt_service._attempts.append()` → `attempt_service.replace_attempt()`
   - Change: `service._persist()` calls → removed (now implicit in public methods)

4. `src/__main__.py`
   - Update imports: `from .adapters.github.auth import GitHubAuthManager` etc.
   - Optionally use `WorkflowServiceContainer` for cleaner setup

5. `src/cli/workflow_cli.py`
   - Update imports from moved files
   - Optionally refactor to use `WorkflowServiceContainer`

6. `src/cli/interactive_menu.py`
   - Update imports from moved files
   - Optionally refactor to use `WorkflowServiceContainer`

7. `src/adapters/github/api_fetcher.py` (moved)
   - Update import paths: `from ...models` → `from ...models`
   - Update import: `from ..github.factory import GitHubWorkflowRunFactory`

8. `src/adapters/github/cli_fetcher.py` (moved)
   - Update import paths: `from ...models` → `from ...models`
   - Update import: `from ..github.factory import GitHubWorkflowRunFactory`

---

## Summary of Changes by Impact Level

### Minimal (No Logic Changes)
- Create protocols: `WorkflowRunStorage`, `WorkflowRunAttemptStorage`, `WorkflowFetcher`
- Move adapter files to `src/adapters/github/`
- Update import paths throughout codebase
- Change parameter types in services from concrete to protocol (duck-typing compatible)

### Small (Encapsulation Fixes)
- Add public methods to services: `replace_run()`, `replace_attempt()`, `delete_run()`, `delete_attempt()`
- Update `WorkflowRunExportImportService` to use public API instead of private member access

### Optional (Convenience)
- Create `WorkflowServiceContainer` facade to simplify CLI dependencies
- Consolidate GitHub exceptions into `src/adapters/github/exceptions.py` (can stay in original location)

---

## Files Affected

### Must Modify (Core Changes)
1. `/src/services/workflow_run_service.py` — protocol typing, new public methods
2. `/src/services/workflow_run_attempt_service.py` — protocol typing, new public methods
3. `/src/services/workflow_export_import_service.py` — use public API
4. `/src/__main__.py` — update imports

### Should Modify (Best Practice)
5. `/src/cli/workflow_cli.py` — update imports
6. `/src/cli/interactive_menu.py` — update imports

### Must Create
7. `/src/storage/base.py` — storage protocols
8. `/src/adapters/__init__.py` — empty module marker
9. `/src/adapters/github/__init__.py` — re-exports

### Must Move (Or Create as New Locations)
10. `github_api_fetcher.py` → `/src/adapters/github/api_fetcher.py`
11. `github_cli_fetcher.py` → `/src/adapters/github/cli_fetcher.py`
12. `github_workflow_run_factory.py` → `/src/adapters/github/factory.py`
13. `github_auth.py` → `/src/adapters/github/auth.py`
14. `github_exceptions.py` → `/src/adapters/github/exceptions.py` (or stay where it is)

### Optional (Convenience)
15. `/src/services/workflow_service_container.py` — optional facade

---

## Verification Checklist

After refactoring, ensure:
- [ ] All public interfaces (signatures from "Public Interfaces" section) are preserved
- [ ] `python -m src` runs without errors
- [ ] `python -m src --help` lists all commands
- [ ] Tests pass: `pytest tests/ -q`
- [ ] Imports use protocols where appropriate (no import errors)
- [ ] No private member access (`_runs`, `_attempts`, `_persist()`) from other modules
- [ ] GitHub adapter logic is consolidated in `src/adapters/github/`
- [ ] Storage layer abstraction via protocols exists and is used
- [ ] No new circular dependencies introduced

