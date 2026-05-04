# Task 09 Analysis: Service Layer, Storage Layer, and GitHub Adapter Separation

## Current State Assessment

The codebase currently has **three partially-formed layers** with **no abstract interfaces** and **multiple tight couplings**:

### 1. Models Layer (Clean)
- `/src/models/`: Domain models are well-separated
  - `WorkflowRun`, `WorkflowRunAttempt` (dataclasses)
  - `WorkflowStatus`, `WorkflowConclusion` (enums)
  - `WorkflowStatisticsReport` (dataclass)
- **Status**: Clean. No dependencies on services or storage.

### 2. Storage Layer (Minimal, Coupled)
Located: `/src/storage/`

**Current Classes:**
- `WorkflowJsonStorage` (workflow_json_storage.py)
  - Loads/saves `List[WorkflowRun]` from/to JSON
  - Direct dependency: imports `WorkflowRun` model only
  - Uses `Path`, `json` stdlib

- `WorkflowAttemptJsonStorage` (workflow_attempt_json_storage.py)
  - Loads/saves `List[WorkflowRunAttempt]` from/to JSON
  - Direct dependency: imports `WorkflowRunAttempt` model only
  - Uses `Path`, `json` stdlib

**Coupling Issues:**
- No abstract interface → services assume concrete implementations
- Services hardcode calls to `.save()` and `.load()` with specific signatures
- No way to swap storage backends (e.g., database, S3) without modifying services
- Storage classes are simple but cannot be polymorphic

**Status**: Minimal separation achieved; lacks abstraction.

---

### 3. Service Layer (Mixed Concerns, No Clear Boundaries)
Located: `/src/services/`

**Core Business Logic Services:**

1. **WorkflowRunService** (workflow_run_service.py)
   - Manages `WorkflowRun` in-memory list
   - Depends on: `WorkflowJsonStorage`, `WorkflowRun`, enums
   - Public methods: `add_workflow_run()`, `list_runs()`, `get_run_detail()`, `filter_*()`, `filter_runs()`
   - Private: `_persist()` (calls storage)
   - **Status**: Pure service, good boundaries, but storage is hardcoded concrete type

2. **WorkflowAttemptService** (workflow_attempt_service.py)
   - Manages `WorkflowRunAttempt` in-memory list
   - Depends on: `WorkflowAttemptJsonStorage`, `WorkflowRunAttempt`, enums
   - Public methods: `add_attempt()`, `list_attempts()`, `get_attempt_detail()`, `filter_*()`, `filter_attempts()`
   - Private: `_persist()` (calls storage)
   - **Status**: Pure service, good boundaries, but storage is hardcoded concrete type

3. **WorkflowStatisticsService** (workflow_statistics_service.py)
   - Reads-only aggregation over runs and attempts
   - Depends on: `WorkflowRunService`, `WorkflowAttemptService`, models
   - Public methods: `compute_report()`, `compute_report_for_runs()`
   - Private: Various `_compute_*()` methods for statistics
   - **Status**: Pure service, good separation; depends on other services (acceptable)

4. **WorkflowDataPortabilityService** (workflow_data_portability_service.py)
   - Exports/imports runs and attempts to/from files
   - Depends on: `WorkflowRunService`, `WorkflowAttemptService`, models
   - **Problem**: Uses `json` and `Path` directly for file I/O (storage concerns bleeding into service)
   - Public methods: `export_runs()`, `import_runs()`, `export_attempts()`, `import_attempts()`
   - Private: `_validate_run_schema()`, `_validate_attempt_schema()`
   - **Status**: Service with storage logic mixed in; should delegate JSON I/O to storage layer

5. **WorkflowRunTracker** (workflow_run_tracker.py)
   - High-level facade for creating/tracking runs
   - Depends on: `WorkflowRunService`, `WorkflowAttemptService`, models
   - Public methods: `track()`, `create_attempt()`
   - **Status**: Pure service, acceptable dependencies

6. **WorkflowAttemptTracker** (workflow_attempt_tracker.py)
   - High-level facade for tracking attempts (currently minimal)
   - Depends on: `WorkflowAttemptService`, models
   - **Status**: Simple; likely superseded by `WorkflowRunTracker.create_attempt()`

---

### 4. GitHub Adapter Layer (Not Separated)
Located: `/src/services/github_integration_service.py`

**Current Class:**
- **GitHubIntegrationService**
  - Handles token resolution, validation, and GitHub API/CLI calls
  - **Core Concerns (Mixed):**
    1. **Token Management**: `_resolve_token()`, `_validate_token()` (env var, secrets file, interactive)
    2. **GitHub API Client**: Direct `requests` calls, `subprocess` for `gh` CLI
    3. **Data Transformation**: `_convert_api_run()`, `_convert_api_attempt()` (GitHub → domain models)
    4. **Timestamp Parsing**: `_parse_github_timestamp()` (ISO 8601 → datetime)
    5. **Fetch Modes**: Supports both REST API and `gh` CLI as backends
  - **Public Methods**:
    - `fetch_runs(owner, repo, workflow_name, limit, token)` → `List[WorkflowRun]`
    - `fetch_run_attempts(owner, repo, run_id, token)` → `List[WorkflowRunAttempt]`
  - **Private Methods**: 8+ internal methods handling token, API calls, data conversion
  - **Dependencies**:
    - Direct: `requests`, `subprocess`, `os`, `logging`
    - Domain: `WorkflowRun`, `WorkflowRunAttempt`, `WorkflowStatus`, `WorkflowConclusion`
  - **Issues**:
    - Too many responsibilities in one class (token mgmt + API client + transformation)
    - No separation between GitHub client and domain conversion
    - No abstraction interface → CLI and menu directly import and instantiate
    - Interacts with services/storage only indirectly (through CLI layer)

**Status**: Exists but is NOT separated; blends external API concerns with domain logic.

---

## Separation Requirements

### Layer 1: Storage Layer (Abstract)

**Current:**
- `WorkflowJsonStorage` (concrete JSON implementation)
- `WorkflowAttemptJsonStorage` (concrete JSON implementation)

**Required Abstract Interface:**
- `WorkflowRunRepository` (protocol/ABC)
  ```python
  class WorkflowRunRepository(Protocol):
      def save(self, runs: List[WorkflowRun]) -> None: ...
      def load(self) -> List[WorkflowRun]: ...
  ```
- `WorkflowAttemptRepository` (protocol/ABC)
  ```python
  class WorkflowAttemptRepository(Protocol):
      def save(self, attempts: List[WorkflowRunAttempt]) -> None: ...
      def load(self) -> List[WorkflowRunAttempt]: ...
  ```

**Concrete Implementations to Keep:**
- `WorkflowJsonStorage` (implements `WorkflowRunRepository`)
- `WorkflowAttemptJsonStorage` (implements `WorkflowAttemptRepository`)

**Future Extensibility:**
- New implementations: `WorkflowDatabaseStorage`, `WorkflowS3Storage`, etc.

---

### Layer 2: Service Layer (Core Business Logic)

**Classes That Stay as Services:**

1. **WorkflowRunService**
   - Constructor change: `__init__(storage: WorkflowRunRepository)` (abstract)
   - No other changes needed
   - Already a pure service

2. **WorkflowAttemptService**
   - Constructor change: `__init__(storage: WorkflowAttemptRepository)` (abstract)
   - No other changes needed
   - Already a pure service

3. **WorkflowStatisticsService**
   - No changes required
   - Pure aggregation service

4. **WorkflowDataPortabilityService**
   - **REFACTOR REQUIRED**: Move file I/O logic out
   - Create new storage classes: `WorkflowRunExportStorage`, `WorkflowAttemptExportStorage`
   - Service should delegate JSON file export/import to these storage classes
   - Keep only validation and orchestration in service

5. **WorkflowRunTracker**
   - No changes required
   - Service facade

6. **WorkflowAttemptTracker**
   - No changes required (or possibly deprecate if unused)

---

### Layer 3: GitHub Adapter Layer (Separate External Concerns)

**Current Problem:**
- `GitHubIntegrationService` mixes token management, API calls, and domain transformation

**Required Separation:**

**A. GitHub API Client (New)**
- Class: `GitHubApiClient` (or `GitHubRestApiClient`)
  - Private HTTP client (requests-based)
  - Methods: `get_runs()`, `get_run_attempts()` → return raw dicts
  - Handles: Authorization header, endpoint construction, HTTP methods, error handling
  - **Does NOT touch domain models**

**B. GitHub CLI Adapter (New)**
- Class: `GitHubCliAdapter`
  - Wraps `subprocess` calls to `gh`
  - Methods: `run_gh_command()` → returns raw JSON output
  - Handles: Command construction, subprocess lifecycle, output parsing to dict
  - **Does NOT touch domain models**

**C. Token Resolution (New or Moved)**
- Class: `GitHubTokenResolver` or move to config layer
  - Methods: `resolve()` → str
  - Handles: Env vars, secrets files, interactive prompts
  - **Separate from API client**

**D. GitHub Data Converter (New)**
- Class: `GitHubToWorkflowConverter`
  - Methods: `convert_run(api_data: dict) -> WorkflowRun`
  - Methods: `convert_attempt(api_data: dict) -> WorkflowRunAttempt`
  - Handles: Enum validation, timestamp parsing
  - **Pure transformation, no I/O**

**E. GitHub Integration Service (Refactored)**
- Becomes a thin facade: `GitHubIntegrationService`
  - Composes: `GitHubApiClient`, `GitHubCliAdapter`, `GitHubTokenResolver`, `GitHubToWorkflowConverter`
  - Public methods: `fetch_runs()`, `fetch_run_attempts()` (unchanged signature)
  - Orchestrates the layers, returns domain models
  - **Clear separation of concerns**

---

## Circular Dependency Analysis

### Current Circular Dependencies: NONE DETECTED

**Dependency Graph (Acyclic):**
```
CLI/Menu
    ↓
Services (WorkflowRunService, WorkflowAttemptService, etc.)
    ↓
Storage (WorkflowJsonStorage, WorkflowAttemptJsonStorage)
    ↓
Models (WorkflowRun, WorkflowAttempt, Enums)
```

**GitHub Integration:**
```
CLI/Menu → GitHubIntegrationService → (requests, subprocess) → Models
```

**No circular edges detected**. However, services are tightly coupled to concrete storage implementations, which limits flexibility.

---

## Public Interfaces to Preserve

### Function Signatures and Return Types (MUST NOT CHANGE)

**WorkflowRunService:**
```python
def add_workflow_run(self, run: WorkflowRun) -> WorkflowRun
def list_runs(self) -> List[WorkflowRun]
def get_run_detail(self, run_id: str) -> Optional[WorkflowRun]
def filter_by_branch(self, branch: str) -> List[WorkflowRun]
def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRun]
def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRun]
def filter_by_duration_range(self, min_s: Optional[float], max_s: Optional[float]) -> List[WorkflowRun]
def filter_by_created_at(self, before: Optional[datetime], after: Optional[datetime]) -> List[WorkflowRun]
def filter_by_updated_at(self, before: Optional[datetime], after: Optional[datetime]) -> List[WorkflowRun]
def filter_by_has_attempts(self, has_attempts: bool, attempt_service: WorkflowAttemptService) -> List[WorkflowRun]
def filter_runs(...) -> List[WorkflowRun]  # all parameters
```

**WorkflowAttemptService:**
```python
def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt
def list_attempts(self) -> List[WorkflowRunAttempt]
def get_attempt_detail(self, attempt_id: str) -> Optional[WorkflowRunAttempt]
def filter_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]
def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRunAttempt]
def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRunAttempt]
def filter_by_duration_range(self, min_s: Optional[float], max_s: Optional[float]) -> List[WorkflowRunAttempt]
def filter_by_started_at(self, before: Optional[datetime], after: Optional[datetime]) -> List[WorkflowRunAttempt]
def filter_by_completed_at(self, before: Optional[datetime], after: Optional[datetime]) -> List[WorkflowRunAttempt]
def filter_attempts(...) -> List[WorkflowRunAttempt]
```

**WorkflowStatisticsService:**
```python
def compute_report(self) -> WorkflowStatisticsReport
def compute_report_for_runs(self, runs: List[WorkflowRun]) -> WorkflowStatisticsReport
```

**WorkflowDataPortabilityService:**
```python
def export_runs(self, filepath: str, runs: Optional[List[WorkflowRun]]) -> int
def import_runs(self, filepath: str, skip_duplicates: bool) -> Dict[str, Any]
def export_attempts(self, filepath: str, attempts: Optional[List[WorkflowRunAttempt]]) -> int
def import_attempts(self, filepath: str, skip_duplicates: bool) -> Dict[str, Any]
```

**WorkflowRunTracker:**
```python
def track(self, workflow_name: str, branch: str, status: WorkflowStatus,
          conclusion: Optional[WorkflowConclusion], run_number: Optional[int],
          commit_sha: Optional[str], run_id: Optional[str], duration_seconds: float) -> WorkflowRun
def create_attempt(self, run_id: str, attempt_number: int, status: WorkflowStatus,
                   conclusion: Optional[WorkflowConclusion], completed_at: Optional[datetime],
                   duration_seconds: float, logs_url: Optional[str], attempt_id: Optional[str]) -> WorkflowRunAttempt
```

**GitHubIntegrationService:**
```python
def fetch_runs(self, owner: str, repo: str, workflow_name: Optional[str] = None,
               limit: int = 30, token: Optional[str] = None) -> List[WorkflowRun]
def fetch_run_attempts(self, owner: str, repo: str, run_id: str, token: Optional[str] = None) -> List[WorkflowRunAttempt]
```

### Class Names (MUST REMAIN)
- `WorkflowRunService`
- `WorkflowAttemptService`
- `WorkflowStatisticsService`
- `WorkflowDataPortabilityService`
- `WorkflowRunTracker`
- `GitHubIntegrationService` (existing name)

### Import Paths (MUST REMAIN)
- Expect imports from `src.services.*` for all service classes
- Expect imports from `src.storage.*` for storage implementations
- Expect `GitHubIntegrationService` from `src.services.github_integration_service`

---

## Proposed Abstract Layer Interfaces

### 1. Storage Repository Protocols

**File:** `/src/storage/base.py` (or `__init__.py`)

```python
from typing import Protocol, List
from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt

class WorkflowRunRepository(Protocol):
    """Abstract interface for WorkflowRun persistence."""
    def save(self, runs: List[WorkflowRun]) -> None:
        """Save runs to storage."""
        ...
    
    def load(self) -> List[WorkflowRun]:
        """Load all runs from storage."""
        ...

class WorkflowAttemptRepository(Protocol):
    """Abstract interface for WorkflowRunAttempt persistence."""
    def save(self, attempts: List[WorkflowRunAttempt]) -> None:
        """Save attempts to storage."""
        ...
    
    def load(self) -> List[WorkflowRunAttempt]:
        """Load all attempts from storage."""
        ...
```

---

### 2. GitHub Adapter Interfaces

**File:** `/src/adapters/github/base.py` (new module)

```python
from typing import Protocol, Dict, List, Optional

class GitHubClient(Protocol):
    """Abstract interface for GitHub API calls."""
    def get_runs(self, owner: str, repo: str, limit: int) -> List[Dict]:
        """Fetch raw run data from GitHub."""
        ...
    
    def get_run_attempts(self, owner: str, repo: str, run_id: str) -> List[Dict]:
        """Fetch raw attempt data for a run from GitHub."""
        ...

class GitHubDataConverter(Protocol):
    """Abstract interface for GitHub API → domain model conversion."""
    def convert_run(self, api_data: Dict) -> "WorkflowRun":
        """Convert GitHub run data to WorkflowRun."""
        ...
    
    def convert_attempt(self, api_data: Dict, run_id: str) -> "WorkflowRunAttempt":
        """Convert GitHub attempt data to WorkflowRunAttempt."""
        ...

class TokenProvider(Protocol):
    """Abstract interface for GitHub token resolution."""
    def resolve(self) -> str:
        """Resolve and return a GitHub token."""
        ...
```

---

## Blockers and Ambiguities

### 1. **Module Organization Ambiguity**

**Question:** Should GitHub adapter be a new top-level package?

**Current:** `src/services/github_integration_service.py`

**Options:**
1. Keep in `services/` (simpler, service-like responsibility)
2. Move to `src/adapters/github/` (clearer separation, implies external integration)
3. Move to `src/integrations/github/` (alternative naming)

**Assumption for this analysis:** Moving to `src/adapters/github/` for clarity, but existing public name `GitHubIntegrationService` is preserved for backward compatibility.

---

### 2. **Abstract Class vs Protocol**

**Question:** Use `typing.Protocol` (structural subtyping) or `ABC` (nominal)?

**Current codebase:** No abstract bases in use.

**Options:**
1. `Protocol` from `typing` (more flexible, duck-typing)
2. `ABC` from `abc` (explicit contracts, checked at runtime)
3. Both (protocols for clearer intent, ABC as fallback)

**Assumption:** Use `Protocol` for interfaces (more Pythonic, aligns with modern typing). Add `ABC` if explicit base class is needed for `isinstance()` checks.

---

### 3. **WorkflowDataPortabilityService Scope**

**Question:** Should export/import logic stay in a service or move to storage?

**Current:** Service does JSON file I/O directly.

**Options:**
1. Create new storage classes for export/import (`ExportRunStorage`, etc.)
2. Add export/import methods to existing `WorkflowJsonStorage`
3. Keep in service but abstract the file operations

**Assumption:** Create dedicated storage classes. Allows export/import to coexist with standard load/save, and keeps `WorkflowDataPortabilityService` as pure orchestration.

---

### 4. **GitHubIntegrationService Constructor Change**

**Question:** Should token resolution be injected or resolved internally?

**Current:** `__init__(fetch_mode: str = "api")`; token resolved on demand.

**Options:**
1. Add `token_provider: TokenProvider` parameter (dependency injection)
2. Keep current lazy resolution (simpler for CLI)
3. Both (constructor optional, falls back to lazy)

**Assumption:** Support both. Constructor can optionally accept a `token_provider`. If omitted, fall back to current `_resolve_token()` logic.

---

### 5. **Trackers: Needed or Deprecated?**

**Question:** Are `WorkflowRunTracker` and `WorkflowAttemptTracker` facade classes or legacy?

**Current:** `WorkflowRunTracker` is actively used. `WorkflowAttemptTracker` is minimal.

**Assumption:** Keep both. They serve as convenient facades for CLI/menu code. Refactoring does not require changes to public signatures.

---

## Scope: In, Out, Borderline

### IN (Must Fix)
1. Abstract storage interfaces (Repository pattern)
2. Separate GitHub adapter into distinct concerns (client, converter, token provider)
3. Remove tight coupling between services and concrete storage
4. Preserve all public method signatures and class names
5. Move file I/O from `WorkflowDataPortabilityService` to storage layer

### OUT (Out of Scope)
1. Rewrite CLI or interactive menu
2. Add database support (only design for it)
3. Refactor model classes or enums
4. Change existing tests beyond what refactoring requires
5. Add new features (e.g., webhooks, caching)

### BORDERLINE (May Need Clarification)
1. **Module reorganization**: Move GitHub service to `adapters/` package?
   - **Pragmatic decision:** Keep in `src/services/` for now, document intent
2. **Backward compatibility of imports**: Do we need compatibility shims?
   - **Pragmatic decision:** No; breaking imports are acceptable if documented
3. **Test updates**: How many test updates are acceptable?
   - **Pragmatic decision:** Update tests to match refactored code; don't modify baseline test suite unless necessary

---

## Priorities

### High Priority (Blocks Adoption)
1. **Create abstract storage interfaces** (Repository pattern)
   - Services cannot be properly tested without this
   - Enables multiple storage backends
   - ~2-3 hours of work

2. **Separate GitHub adapter from integration service**
   - Current service is >500 lines with 8+ private methods
   - Token handling, API client, and domain conversion need clear boundaries
   - ~3-4 hours of work

3. **Move file I/O out of WorkflowDataPortabilityService**
   - Service is currently violating single responsibility
   - Should orchestrate storage, not perform I/O
   - ~1-2 hours of work

### Medium Priority (Nice to Have)
1. **Add `__all__` exports to module `__init__.py` files**
   - Clarifies public API
   - Documents what is exported at each layer
   - ~1 hour of work

2. **Create explicit base classes or protocols for extension points**
   - Currently implicit (only docs and naming)
   - Future maintainers need clear guidance
   - ~1 hour of work

### Low Priority (Can Defer)
1. **Rename GitHubIntegrationService to reflect refactoring**
   - Current name is acceptable; internal structure is what matters
   - Defer unless a major re-release happens

2. **Consolidate WorkflowAttemptTracker logic**
   - Currently minimal; not blocking anything
   - Can be left as-is

---

## Summary of Classes and Their Layers

| Class Name | File | Current Layer | Target Layer | Action |
|---|---|---|---|---|
| `WorkflowRun` | `models/workflow_run.py` | Models | Models | No change |
| `WorkflowRunAttempt` | `models/workflow_attempt.py` | Models | Models | No change |
| `WorkflowStatus` | `models/workflow_status.py` | Models | Models | No change |
| `WorkflowConclusion` | `models/workflow_conclusion.py` | Models | Models | No change |
| `WorkflowStatisticsReport` | `models/workflow_statistics_report.py` | Models | Models | No change |
| `WorkflowJsonStorage` | `storage/workflow_json_storage.py` | Storage (Concrete) | Storage (Concrete) | Update to use abstract interface |
| `WorkflowAttemptJsonStorage` | `storage/workflow_attempt_json_storage.py` | Storage (Concrete) | Storage (Concrete) | Update to use abstract interface |
| **(NEW)** `WorkflowRunRepository` | `storage/base.py` | — | Storage (Abstract) | Create Protocol |
| **(NEW)** `WorkflowAttemptRepository` | `storage/base.py` | — | Storage (Abstract) | Create Protocol |
| `WorkflowRunService` | `services/workflow_run_service.py` | Services | Services | Update constructor to accept abstract repo |
| `WorkflowAttemptService` | `services/workflow_attempt_service.py` | Services | Services | Update constructor to accept abstract repo |
| `WorkflowStatisticsService` | `services/workflow_statistics_service.py` | Services | Services | No change |
| `WorkflowDataPortabilityService` | `services/workflow_data_portability_service.py` | Services | Services | Refactor to delegate I/O to storage |
| `WorkflowRunTracker` | `services/workflow_run_tracker.py` | Services | Services | No change |
| `WorkflowAttemptTracker` | `services/workflow_attempt_tracker.py` | Services | Services | No change |
| `GitHubIntegrationService` | `services/github_integration_service.py` | Services (Mixed) | Adapters (GitHub) | Refactor; split concerns; keep public API |
| **(NEW)** `GitHubApiClient` | `adapters/github/api_client.py` | — | Adapters (GitHub) | Create; extract HTTP client logic |
| **(NEW)** `GitHubCliAdapter` | `adapters/github/cli_adapter.py` | — | Adapters (GitHub) | Create; extract CLI wrapper logic |
| **(NEW)** `GitHubTokenResolver` | `adapters/github/token_resolver.py` | — | Adapters (GitHub) | Create; extract token resolution logic |
| **(NEW)** `GitHubToWorkflowConverter` | `adapters/github/converter.py` | — | Adapters (GitHub) | Create; extract domain conversion logic |

---

## Next Steps for System Architect

1. **Design file layout** for `/src/adapters/github/` module
2. **Define constructors** for refactored `GitHubIntegrationService` (token provider injection, etc.)
3. **Plan test coverage** for new abstract interfaces and concrete implementations
4. **Write migration guide** for CLI layer to use refactored GitHub service
5. **Identify any hidden dependencies** in interactive menu or CLI that assume concrete storage types

