# Task 08 Analysis: Add Optional GitHub Fetch Mode to Fetch Workflow Runs via GitHub REST API or gh CLI

**Date:** 2026-05-03  
**Architecture:** Pipeline (Sequential Agents)  
**Scope:** Fetch workflow runs from GitHub repositories via REST API (requests) or gh CLI, convert to existing domain model, manage authentication with secure token resolution, handle errors gracefully.

---

## What the Task Is Asking For

Extend the GitHub Workflow Manager with a **GitHub fetch mode** that can retrieve workflow runs directly from a repository on GitHub, convert them into the existing `WorkflowRun` domain model, and integrate them into the local tracking system.

**Core Requirements:**

1. **Fetch source options:**
   - GitHub REST API using `requests` library
   - `gh` CLI tool (command-line)
   - Both must be optional, configurable per fetch operation

2. **Authentication (PAT — Personal Access Token):**
   - Check `GITHUB_TOKEN` environment variable first
   - Fall back to `secrets/.env` file if env var not set
   - Prompt user securely if neither available
   - User-entered PAT NOT persisted unless explicitly configured
   - Token validated before making requests

3. **Data Conversion:**
   - Fetched GitHub API response → existing `WorkflowRun` domain model
   - Must map GitHub API fields to WorkflowRun attributes
   - Handle optional/missing fields gracefully

4. **Error Handling:**
   - Rate limit errors (HTTP 403, etc.)
   - Invalid/expired token errors (HTTP 401, etc.)
   - Network failures (connection errors, timeouts)
   - All errors handled gracefully (no unhandled exceptions)

5. **Incremental Fetch (Bonus):**
   - Option to fetch only new/updated runs since last fetch
   - Not required, but may reduce API calls

6. **CLI & Interactive Menu Integration:**
   - New subcommand: `python -m src fetch` with arguments
   - New interactive menu option for fetch
   - All functionality must be accessible via both interfaces
   - Help text and error messages user-friendly

---

## Current State: Existing Architecture

### Data Models

**WorkflowRun** (`src/models/workflow_run.py`)
- `id: str` — unique identifier (currently UUID or GitHub run ID)
- `workflow_name: str` — workflow name
- `branch: str` — Git branch
- `status: WorkflowStatus` — enum (QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING)
- `conclusion: Optional[WorkflowConclusion]` — enum or None (SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE)
- `created_at: datetime` — UTC timestamp
- `updated_at: Optional[datetime]` — UTC timestamp or None
- `run_number: Optional[int]` — GitHub run number
- `commit_sha: Optional[str]` — commit SHA
- `duration_seconds: float` — execution time (default 0.0)

**No breaking changes needed to WorkflowRun** — it already supports GitHub's native fields (run_number, commit_sha, etc.)

### Service Layer

**WorkflowRunService** (`src/services/workflow_run_service.py`)
- Manages in-memory list of WorkflowRun objects
- `add_workflow_run(run: WorkflowRun)` — persists to storage
- `list_runs()`, `get_run_detail()`, filtering, querying
- Storage backed by WorkflowJsonStorage

**WorkflowRunTracker** (`src/services/workflow_run_tracker.py`)
- High-level facade for creating new runs
- Auto-generates UUIDs if no `run_id` provided
- Delegates to WorkflowRunService for persistence

**No existing GitHub API integration** — all current data is manually entered or imported from JSON files.

### Storage Layer

**WorkflowJsonStorage** (`src/storage/workflow_json_storage.py`)
- Loads/saves WorkflowRun objects as JSON arrays
- Files: `artifacts/workflow_runs.json`, `artifacts/workflow_run_attempts.json`
- In-memory pattern: load on startup, persist after mutations

### CLI & Menu

**workflow_cli.py** (`src/cli/workflow_cli.py`)
- Argparse-based subcommand interface
- Current commands: `add`, `list`, `detail`, `check`, `attempt-*`, `stats`, `export`, `import`
- Entry point: `run_cli(service, attempt_service, args=None)`
- Usage: `python -m src <subcommand> [args]`

**interactive_menu.py** (`src/cli/interactive_menu.py`)
- Menu-driven interface with numbered options
- Current options: Add, List, Detail, Check, Filter, Advanced Filter, Statistics, Attempts, Exit
- Entry point: `run_interactive(service, attempt_service)`
- Usage: `python -m src` (no args)

**__main__.py** (`src/__main__.py`)
- Routes to interactive or CLI mode based on argv length

---

## Task 08 Requirements: GitHub Fetch Feature

### 1. Authentication Management

**Current state:** No auth system exists. Task requires:

#### 1.1 PAT Resolution Strategy

Three-tier priority (highest to lowest):
1. `GITHUB_TOKEN` environment variable
2. `secrets/.env` file (location TBD, likely `secrets/.env` or `.github/.env`)
3. Secure user prompt (if neither available)

**Key constraints:**
- User-entered token must NOT be saved to disk unless explicitly configured
- Validation: Check token before making API calls (e.g., via test request or local format check)
- Error handling: Invalid/expired tokens → graceful error message, no re-prompt

**New module required:** `src/auth/` or `src/utils/` for token management

#### 1.2 Token Validation

Before fetching:
- Validate token format (GitHub tokens have known prefixes: `ghp_*`, `ghu_*`, `ghs_*`, `gho_*`)
- Make a lightweight test request (e.g., `GET /user`) to verify token validity
- Return clear error if validation fails

### 2. GitHub API Adapter

**Not yet created.** Need a new service to fetch workflow runs from GitHub.

#### 2.1 GitHub REST API Integration

**Responsibilities:**
- Connect to GitHub API v3 endpoint
- Fetch workflow runs for a given `owner/repo`
- Map GitHub API response fields to WorkflowRun domain model
- Handle pagination (API returns max 30 per page by default)
- Support optional filtering (e.g., branch, status, created date)

**GitHub API endpoints involved:**
- `GET /repos/{owner}/{repo}/actions/runs` — List all workflow runs
- Optional filters: `?status=<status>&created=<date_range>&branch=<branch>`
- Pagination: `?page=<n>&per_page=<max>`

**New class:** `GitHubAPIFetcher` in `src/services/github_api_fetcher.py` or similar

**Expected method signature:**
```python
class GitHubAPIFetcher:
    def __init__(self, token: str):
        self.token = token  # or retrieve from env/file
    
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
        per_page: int = 30
    ) -> List[WorkflowRun]:
        """
        Fetch workflow runs from GitHub API.
        Returns list of WorkflowRun objects.
        """
        pass
    
    def validate_token(self) -> bool:
        """Check token validity via test request."""
        pass
```

#### 2.2 gh CLI Integration (Alternative)

**Why:** User may prefer `gh` CLI over direct API calls (simpler, auth already configured)

**Responsibilities:**
- Execute `gh run list` or `gh run view` commands
- Parse output (JSON mode available via `--json`)
- Convert to WorkflowRun domain model

**Expected command:**
```bash
gh run list --repo owner/repo --json id,name,status,conclusion,createdAt,updatedAt,databaseId,headBranch,headSha,runNumber
```

**New class:** `GitHubCLIFetcher` in `src/services/github_cli_fetcher.py` or similar

**Expected method signature:**
```python
class GitHubCLIFetcher:
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None
    ) -> List[WorkflowRun]:
        """
        Fetch workflow runs via gh CLI.
        Returns list of WorkflowRun objects.
        """
        pass
    
    def is_available(self) -> bool:
        """Check if gh CLI is installed and authenticated."""
        pass
```

### 3. API Response → Domain Model Mapping

**Critical challenge:** GitHub API field names differ from WorkflowRun field names.

#### 3.1 GitHub API Response Structure

Example workflow run from `GET /repos/{owner}/{repo}/actions/runs`:
```json
{
  "id": 12345,
  "name": "Build and Test",
  "status": "completed",
  "conclusion": "success",
  "created_at": "2025-05-03T10:30:00Z",
  "updated_at": "2025-05-03T10:35:00Z",
  "run_number": 42,
  "head_sha": "abc123def456",
  "head_branch": "main",
  "event": "push"
}
```

#### 3.2 Mapping Strategy

**Fields to map:**

| GitHub API Field | WorkflowRun Field | Conversion | Notes |
|---|---|---|---|
| `id` (int) | `id` (str) | `str(id)` | Convert to string for consistency |
| `name` (str) | `workflow_name` | Direct | Name of the workflow |
| `status` (str) | `status` (WorkflowStatus) | Enum conversion | May need normalization (GitHub: "completed", "in_progress", "queued", "requested", "waiting"; WorkflowStatus: similar but check enum values) |
| `conclusion` (str \| null) | `conclusion` (WorkflowConclusion \| None) | Enum conversion or None | GitHub: "success", "failure", "cancelled", etc. |
| `created_at` (ISO 8601) | `created_at` (datetime) | Parse ISO format | Already UTC, timezone-aware |
| `updated_at` (ISO 8601) | `updated_at` (datetime \| None) | Parse ISO format or None | Same as above |
| `run_number` (int) | `run_number` (int \| None) | Direct | GitHub's run sequence number |
| `head_sha` (str) | `commit_sha` (str \| None) | Direct | Commit SHA |
| `head_branch` (str) | `branch` (str) | Direct | Branch name |
| **N/A** | `duration_seconds` (float) | Calculated or 0.0 | GitHub API provides `created_at` and `updated_at`; calculate as `(updated_at - created_at).total_seconds()` if both present, else 0.0 |

**Design decision:** Create a **mapping/conversion module** or factory method:

```python
class GitHubWorkflowRunFactory:
    @staticmethod
    def from_github_api_response(data: dict) -> WorkflowRun:
        """
        Convert GitHub API response to WorkflowRun.
        Handles field name translation, enum conversion, datetime parsing.
        """
        pass
```

**Location:** `src/models/github_workflow_run_factory.py` or `src/services/github_workflow_run_converter.py`

### 4. Error Handling & Edge Cases

#### 4.1 Common Error Scenarios

| Scenario | HTTP Code | Handling |
|---|---|---|
| Invalid token | 401 Unauthorized | Print user-friendly error, exit gracefully |
| Expired token | 401 Unauthorized | Same as above |
| Insufficient permissions | 403 Forbidden | Inform user token lacks required scopes (e.g., `repo:read`) |
| Rate limit reached | 403 Forbidden (with `X-RateLimit-Remaining: 0`) | Inform user of rate limit; suggest retry later |
| Network error | Connection error | Catch and print "Network error: ..." |
| Repo not found | 404 Not Found | Print "Repository not found" |
| Malformed API response | JSON decode error | Log error, skip bad record or fail gracefully |

#### 4.2 Implementation Strategy

- Wrap API calls in try/except blocks
- Distinguish between fatal errors (invalid token, network failure) and recoverable errors (bad record in paginated response)
- Log meaningful error messages without exposing raw stack traces
- No retries within feature scope (out of scope per requirements)

### 5. Fetch Modes & CLI Integration

#### 5.1 Fetch Subcommand Structure

**New subcommand:** `fetch`

**Arguments:**
```
python -m src fetch \
    --owner <owner> \
    --repo <repo> \
    --mode <api|cli> \
    [--branch <branch>] \
    [--status <status>] \
    [--created-after <date>] \
    [--token <pat>] \
    [--incremental]
```

**Argument details:**
- `--owner` (required): GitHub username or organization
- `--repo` (required): Repository name
- `--mode` (required): Fetch method — "api" or "cli"
- `--branch` (optional): Filter by branch
- `--status` (optional): Filter by workflow status
- `--created-after` (optional): Only fetch runs created after this date (YYYY-MM-DD or ISO format)
- `--token` (optional): Explicit PAT (if provided, skips env var and .env file)
- `--incremental` (optional, bonus): Fetch only new runs since last fetch

#### 5.2 Interactive Menu Integration

**New menu option:** "Fetch from GitHub" or similar

**Flow:**
1. Prompt for owner/repo
2. Prompt for fetch mode (API or CLI)
3. Optionally prompt for filters (branch, status, created-after)
4. Perform fetch
5. Display results (e.g., "Fetched 42 workflow runs")

**Handler function:** `_fetch_from_github()` in `src/cli/interactive_menu.py`

---

## Current Architecture Overview

### Layered Design

```
┌─────────────────────────────────────────────┐
│      CLI / Interactive Menu (Interface)     │
│  workflow_cli.py / interactive_menu.py      │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│   Services (Business Logic)                 │
│  WorkflowRunService, WorkflowRunTracker,    │
│  StatisticsService, ExportImportService    │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│   Domain Models                             │
│  WorkflowRun, WorkflowStatus,               │
│  WorkflowConclusion, etc.                   │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│   Storage (Persistence)                     │
│  WorkflowJsonStorage                        │
└──────────────┬──────────────────────────────┘
               │
            JSON files
```

**Task 08 adds new layer:**
- GitHub Fetcher services (API + CLI)
- Authentication/token manager
- GitHub response converter

### Key Classes & Their Responsibilities

| Class | Location | Responsibility |
|---|---|---|
| `WorkflowRun` | `src/models/workflow_run.py` | Domain model for workflow run data |
| `WorkflowRunService` | `src/services/workflow_run_service.py` | CRUD operations, querying, filtering |
| `WorkflowRunTracker` | `src/services/workflow_run_tracker.py` | High-level run creation facade |
| `WorkflowJsonStorage` | `src/storage/workflow_json_storage.py` | File-based persistence (JSON) |
| `run_cli()` | `src/cli/workflow_cli.py` | CLI command dispatcher |
| `run_interactive()` | `src/cli/interactive_menu.py` | Interactive menu loop |

**Task 08 adds:**

| Class | Location | Responsibility |
|---|---|---|
| `GitHubAuthManager` | `src/auth/github_auth.py` (new) | Resolve PAT from env/file/user; validate token |
| `GitHubAPIFetcher` | `src/services/github_api_fetcher.py` (new) | Fetch via GitHub REST API |
| `GitHubCLIFetcher` | `src/services/github_cli_fetcher.py` (new) | Fetch via gh CLI |
| `GitHubWorkflowRunFactory` | `src/models/github_workflow_run_factory.py` (new) | Map GitHub API → WorkflowRun |
| `GitHubFetchService` | `src/services/github_fetch_service.py` (new, optional) | Facade for API/CLI selection & error handling |

---

## Domain Model: WorkflowRun (Existing)

The WorkflowRun dataclass already supports all fields required for GitHub workflow runs:

```python
@dataclass
class WorkflowRun:
    id: str                           # Can hold GitHub run ID (as string)
    workflow_name: str                # GitHub workflow name
    branch: str                       # GitHub head_branch
    status: WorkflowStatus            # GitHub status (enum)
    conclusion: Optional[WorkflowConclusion]  # GitHub conclusion (enum or None)
    created_at: datetime              # GitHub created_at (ISO → datetime)
    updated_at: Optional[datetime]    # GitHub updated_at (ISO → datetime)
    run_number: Optional[int]         # GitHub run_number
    commit_sha: Optional[str]         # GitHub head_sha
    duration_seconds: float = 0.0     # Calculated from updated_at - created_at
```

**No changes needed to WorkflowRun itself** — it's already GitHub-compatible.

---

## What Needs to Be Implemented

### 1. Authentication Module (New)

**File:** `src/auth/github_auth.py` (new directory/file)

**Responsibilities:**
- Load PAT from environment variable (`GITHUB_TOKEN`)
- Load PAT from file (`secrets/.env` or `.github/.env`)
- Prompt user securely if neither available
- Validate token before use (format check + test API call)
- Manage token lifecycle (not persisting user-entered tokens)

**Key methods:**
```python
class GitHubAuthManager:
    def get_token(self, explicit_token: Optional[str] = None) -> str:
        """Resolve PAT with priority: explicit > env > file > prompt."""
        pass
    
    def validate_token(self, token: str) -> bool:
        """Check token validity."""
        pass
```

### 2. GitHub REST API Fetcher (New)

**File:** `src/services/github_api_fetcher.py`

**Responsibilities:**
- Use `requests` library (may need to add to dependencies)
- Construct API requests to GitHub REST API v3
- Handle pagination
- Parse responses and convert to WorkflowRun objects
- Handle errors (rate limits, auth failures, network issues)

**Key methods:**
```python
class GitHubAPIFetcher:
    def __init__(self, token: str):
        pass
    
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
        per_page: int = 30
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub API."""
        pass
```

### 3. GitHub CLI Fetcher (New)

**File:** `src/services/github_cli_fetcher.py`

**Responsibilities:**
- Detect if `gh` CLI is installed
- Execute `gh run list` with JSON output
- Parse JSON response
- Convert to WorkflowRun objects

**Key methods:**
```python
class GitHubCLIFetcher:
    def is_available(self) -> bool:
        """Check if gh CLI is installed."""
        pass
    
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None
    ) -> List[WorkflowRun]:
        """Fetch via gh CLI."""
        pass
```

### 4. GitHub Response Converter (New)

**File:** `src/models/github_workflow_run_factory.py` or `src/services/github_workflow_run_converter.py`

**Responsibilities:**
- Map GitHub API field names to WorkflowRun attributes
- Handle enum conversions (status, conclusion)
- Parse ISO 8601 datetime strings
- Calculate duration_seconds from timestamps
- Validate data before creating WorkflowRun

**Key method:**
```python
class GitHubWorkflowRunFactory:
    @staticmethod
    def from_github_api_response(data: dict) -> WorkflowRun:
        """Convert GitHub API response to WorkflowRun."""
        pass
```

### 5. CLI Integration (Modified)

**File:** `src/cli/workflow_cli.py`

**Changes:**
1. Import GitHubAuthManager, GitHubAPIFetcher, GitHubCLIFetcher, factory
2. Add `fetch` subcommand to argparse parser
3. Add handler in `run_cli()` for `ns.command == "fetch"`
4. Handler logic:
   - Validate owner/repo arguments
   - Resolve token (env → file → prompt)
   - Create fetcher instance (API or CLI)
   - Fetch runs
   - Add to service
   - Print summary

### 6. Interactive Menu Integration (Modified)

**File:** `src/cli/interactive_menu.py`

**Changes:**
1. Add new handler function `_fetch_from_github(service, attempt_service)`
2. Prompt for owner, repo, fetch mode
3. Optionally prompt for filters
4. Call fetch logic
5. Add to menu options list

### 7. Incremental Fetch (Bonus, Optional)

**If implemented:**
- Store timestamp of last successful fetch
- Query API with `created_after=last_fetch_time`
- Reduce API calls and data transfer
- Requires state persistence (e.g., in a `.github/last_fetch.txt` file)

---

## Integration Points & Data Flow

### Fetch Flow (New)

```
User: python -m src fetch --owner alice --repo my-repo --mode api [--token xyz]
                    ↓
run_cli() routes to fetch handler
                    ↓
GitHubAuthManager.get_token(explicit_token)
    - Check GITHUB_TOKEN env var
    - Check secrets/.env file
    - Prompt user if neither
                    ↓
Validate token: GitHubAuthManager.validate_token()
                    ↓
Create fetcher: GitHubAPIFetcher(token) or GitHubCLIFetcher()
                    ↓
Call fetcher.fetch_runs(owner, repo, filters...)
                    ↓
For each GitHub API response:
    GitHubWorkflowRunFactory.from_github_api_response()
        - Map fields
        - Convert enums
        - Parse datetimes
        - Calculate duration
                    ↓
WorkflowRunService.add_workflow_run() for each run
                    ↓
Print: "Fetched N workflow run(s) from owner/repo"
```

### Interactive Menu Flow (New)

```
User: python -m src  (no args)
                    ↓
run_interactive() shows menu
                    ↓
User selects "Fetch from GitHub" option
                    ↓
_fetch_from_github(service, attempt_service)
                    ↓
Prompt for owner/repo
                    ↓
Prompt for fetch mode (API or CLI)
                    ↓
Prompt for optional filters
                    ↓
Validate inputs
                    ↓
Execute fetch (same as CLI flow)
                    ↓
Display results
```

---

## Ambiguities & Working Assumptions

### 1. GitHub API vs. CLI Selection

**Ambiguity:** When should user choose API vs. CLI?

**Working Assumption:**
- **API (requests):** More reliable, direct control, no CLI dependency, explicit error handling
- **CLI (gh):** User may already have `gh` authenticated locally; simpler for first-time users
- **Implementation:** Both supported; user chooses per invocation
- **Error handling:** If CLI not available, informative error; user can fall back to API

### 2. Token Validation Strategy

**Ambiguity:** Should we validate token before fetching, or fail on first API call?

**Working Assumption:** Validate token early (before API calls). This prevents unnecessary network overhead and provides clearer error messages.

**Validation method:**
- Format check: GitHub tokens follow patterns like `ghp_*`, `ghu_*`, etc.
- Test API call: `GET /user` (lightweight endpoint)
- On failure: Print "Invalid or expired token" and exit

### 3. Secrets File Location

**Ambiguity:** Where should the secrets/.env file be located?

**Working Assumption:** Check `secrets/.env` relative to project root (or absolute path `~/.github/.env`). Configurable via code comments. Path likely: `project_root/secrets/.env` or `~/.github/.env`.

**Design decision:** Start with relative path `secrets/.env` (simple, local to project); document that user can symlink or copy to that location.

### 4. Duration Calculation

**Ambiguity:** How to calculate duration_seconds from GitHub API timestamps?

**Working Assumption:** 
- If both `created_at` and `updated_at` are present: `duration = (updated_at - created_at).total_seconds()`
- If only `created_at`: Use 0.0 (run still in progress, actual duration unknown)
- Handle edge cases (negative duration due to clock skew): Return 0.0

### 5. Duplicate Run Handling

**Ambiguity:** If fetched run already exists locally (same `id`), what happens?

**Working Assumption:**
- Check `service.get_run_detail(id)` before adding
- If exists: Skip with a note (e.g., "Run already tracked")
- If new: Add to service
- No upsert/update of existing runs (out of scope; import feature handles that)

### 6. Incremental Fetch State

**Ambiguity:** How to track "last fetch time" for incremental fetches?

**Working Assumption:** Store in a simple text file (e.g., `.github/last_fetch.timestamp`) with ISO 8601 timestamp. Bonus feature; can be skipped.

### 7. API Rate Limit Handling

**Ambiguity:** GitHub has rate limits (60 req/hour unauthenticated, 5000/hour authenticated). How to handle hitting the limit?

**Working Assumption:**
- Check `X-RateLimit-*` response headers
- If `X-RateLimit-Remaining: 0`, inform user and fail gracefully
- No automatic retry or wait loop (out of scope)
- User can retry after rate limit resets

### 8. Enum Value Normalization

**Ambiguity:** Do GitHub API status/conclusion values exactly match WorkflowStatus/WorkflowConclusion enums?

**Working Assumption:** 
- Likely match (GitHub API uses standard values like "completed", "success", etc.)
- If mismatch: Implement mapping table or case-insensitive conversion
- If unknown value: Log warning and skip run (or use a fallback status)

---

## Scope Signals

### In Scope
- ✅ Fetch via GitHub REST API (requests library)
- ✅ Fetch via gh CLI (subprocess execution)
- ✅ PAT resolution: env var → file → secure prompt
- ✅ Token validation before API calls
- ✅ Graceful error handling (rate limits, invalid token, network, malformed data)
- ✅ Conversion from GitHub API response to WorkflowRun
- ✅ Optional filtering (branch, status, created-after)
- ✅ Integration with existing WorkflowRunService
- ✅ CLI subcommand `fetch` with required args
- ✅ Interactive menu option for fetch
- ✅ User-friendly error messages and help text

### Out of Scope (per requirements)
- ❌ OAuth flow (manual PAT only)
- ❌ Token refresh logic (assume single-use PAT)
- ❌ Automatic retries on rate limit (user retries manually)
- ❌ Webhook-based sync (one-shot fetch only)
- ❌ Database instead of JSON (stay with current storage)
- ❌ GUI / graphical interface

### Bonus (Optional)
- ✓ Incremental fetch (store last fetch time)
- ✓ Per-status or per-branch filtering via API query params
- ✓ Progress indication during large fetches

---

## Existing Patterns to Follow

### 1. Service Pattern (Stateless)
```python
# Pattern from WorkflowRunService
class SomeService:
    def __init__(self, some_dependency):
        self._dep = some_dependency
    
    def some_method(self) -> Result:
        # Operate on dependency, return result
        pass
```

**For Task 08:** GitHubAPIFetcher, GitHubCLIFetcher follow this pattern (initialized per-call in CLI handler).

### 2. Dataclass Pattern (Domain Model)
```python
# Pattern from WorkflowRun
@dataclass
class SomeModel:
    field1: str
    field2: Optional[float]
    
    def __post_init__(self):
        # Validation
        if self.field2 is not None and self.field2 < 0:
            raise ValueError(...)
    
    def to_dict(self) -> dict:
        return {...}
    
    @classmethod
    def from_dict(cls, data: dict) -> "SomeModel":
        return cls(...)
```

**For Task 08:** GitHubWorkflowRunFactory uses static factory method (no @dataclass, just conversion logic).

### 3. CLI Pattern (Argparse)
```python
# Pattern from workflow_cli.py
def build_parser():
    parser = argparse.ArgumentParser(...)
    sub = parser.add_subparsers(dest="command", required=True)
    
    some_p = sub.add_parser("some-cmd", help="...")
    some_p.add_argument("--arg", required=True, ...)
    
    return parser

def run_cli(service, attempt_service, args=None):
    parser = build_parser()
    ns = parser.parse_args(args)
    
    if ns.command == "some-cmd":
        # Handle command
        pass
```

**For Task 08:** Add `fetch` subparser with owner, repo, mode, optional filters.

### 4. Interactive Menu Pattern
```python
# Pattern from interactive_menu.py
def _handler_name(service, attempt_service):
    print("--- Operation ---")
    # Prompt user
    # Call service methods
    # Print results

MENU = [
    ("Option 1", _handler_name),
    ...
]

def run_interactive(service, attempt_service):
    while True:
        # Display menu, read choice, call handler
        pass
```

**For Task 08:** Add `_fetch_from_github()` handler; add to MENU; update dispatcher.

---

## Required Changes: Files to Create/Modify

### New Files

#### 1. `src/auth/github_auth.py` (New Directory + File)

**Purpose:** Manage GitHub Personal Access Token (PAT) resolution and validation

**Responsibilities:**
- Load token from environment (GITHUB_TOKEN)
- Load token from file (secrets/.env)
- Prompt user securely if neither available
- Validate token format and validity
- No persistence of user-entered tokens (unless explicitly configured)

**Estimated class:**
```python
class GitHubAuthManager:
    def get_token(self, explicit_token: Optional[str] = None) -> str:
        """Resolve PAT with priority: explicit > env > file > prompt."""
        pass
    
    def validate_token(self, token: str) -> bool:
        """Validate token format and API access."""
        pass
```

#### 2. `src/services/github_api_fetcher.py` (New File)

**Purpose:** Fetch workflow runs from GitHub REST API

**Responsibilities:**
- Use `requests` library
- Construct and send API requests
- Handle pagination
- Parse responses
- Convert to WorkflowRun objects
- Handle errors (rate limits, auth, network)

**Estimated class:**
```python
class GitHubAPIFetcher:
    def __init__(self, token: str):
        pass
    
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
        per_page: int = 30
    ) -> List[WorkflowRun]:
        pass
```

#### 3. `src/services/github_cli_fetcher.py` (New File)

**Purpose:** Fetch workflow runs via `gh` CLI

**Responsibilities:**
- Detect gh CLI availability
- Execute gh commands with JSON output
- Parse output
- Convert to WorkflowRun objects

**Estimated class:**
```python
class GitHubCLIFetcher:
    def is_available(self) -> bool:
        pass
    
    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None
    ) -> List[WorkflowRun]:
        pass
```

#### 4. `src/models/github_workflow_run_factory.py` (New File)

**Purpose:** Convert GitHub API response to WorkflowRun domain model

**Responsibilities:**
- Map GitHub API field names to WorkflowRun attributes
- Convert enum values (status, conclusion)
- Parse ISO 8601 datetimes
- Calculate duration
- Validate data

**Estimated class:**
```python
class GitHubWorkflowRunFactory:
    @staticmethod
    def from_github_api_response(data: dict) -> WorkflowRun:
        """Convert GitHub API response to WorkflowRun."""
        pass
```

#### 5. `src/services/github_fetch_service.py` (New File, Optional)

**Purpose:** Facade combining auth, fetcher selection, and error handling

**Responsibilities:**
- Resolve token via GitHubAuthManager
- Select fetcher (API or CLI) based on mode
- Execute fetch
- Handle errors
- Return results

**Estimated class:**
```python
class GitHubFetchService:
    def fetch(
        self,
        owner: str,
        repo: str,
        mode: str,  # "api" or "cli"
        service: WorkflowRunService,
        token: Optional[str] = None,
        filters: Optional[dict] = None
    ) -> Tuple[int, List[str]]:  # (count, errors)
        """Fetch and persist runs."""
        pass
```

### Modified Files

#### 1. `src/cli/workflow_cli.py`

**Changes:**
1. Import new classes: GitHubAuthManager, GitHubAPIFetcher, GitHubCLIFetcher, GitHubWorkflowRunFactory
2. Add `fetch` subcommand to `build_parser()`:
   ```
   fetch_p = sub.add_parser("fetch", help="Fetch workflow runs from GitHub")
   fetch_p.add_argument("--owner", required=True, help="GitHub username or organization")
   fetch_p.add_argument("--repo", required=True, help="Repository name")
   fetch_p.add_argument("--mode", required=True, choices=["api", "cli"], help="Fetch method")
   fetch_p.add_argument("--branch", default=None, help="Filter by branch")
   fetch_p.add_argument("--status", default=None, help="Filter by workflow status")
   fetch_p.add_argument("--created-after", default=None, help="Filter runs created after date")
   fetch_p.add_argument("--token", default=None, help="GitHub PAT (optional; env var/file checked first)")
   fetch_p.add_argument("--incremental", action="store_true", help="Fetch only new runs (bonus)")
   ```
3. Add handler in `run_cli()` for `ns.command == "fetch"`

#### 2. `src/cli/interactive_menu.py`

**Changes:**
1. Import new classes
2. Add handler function `_fetch_from_github(service, attempt_service)`
3. Add to MENU list
4. Update dispatcher logic

#### 3. `src/__init__.py` (or `src/auth/__init__.py`)

**Changes:**
- Export GitHubAuthManager (if imported elsewhere)

#### 4. `src/models/__init__.py` (Optional)

**Changes:**
- Export GitHubWorkflowRunFactory (if needed for public API)

---

## Key Design Decisions

### 1. Separate Fetcher Classes (API vs. CLI)

- **Rationale:** Different implementation details; common interface (fetch_runs)
- **Pattern:** Strategy pattern — user chooses implementation at runtime
- **Benefit:** Testable independently; easy to add more fetchers later

### 2. Conversion Factory Pattern

- **Rationale:** Separates API response parsing from domain logic
- **Implementation:** Static method (no state)
- **Benefit:** Single responsibility; testable in isolation

### 3. Token Resolution Priority

- **Order:** Explicit arg > env var > file > user prompt
- **Rationale:** Follows principle of least surprise; explicit takes precedence
- **Non-persistence:** User-entered tokens not saved (avoids security risk)

### 4. Error Handling Strategy

- **Philosophy:** Fail fast with clear messages; no silent skips
- **Rate limits:** Inform user; suggest retry later
- **Bad data:** Skip individual runs with warning (non-atomic)
- **Auth failures:** Exit immediately

### 5. No Upsert Logic

- **Assumption:** Fetched runs are new (or older than local copies)
- **Behavior:** Skip if ID already exists (no update)
- **Rationale:** Avoids accidental overwrites; import feature handles upserts

### 6. Stateless Fetchers

- **Design:** Instantiate per-call, no persistent state
- **Rationale:** Simple, testable, no cleanup needed
- **Incremental bonus:** Implement as optional state file (outside service)

---

## Expected CLI Usage

```bash
# Fetch via GitHub REST API
python -m src fetch --owner octocat --repo hello-world --mode api

# Fetch via gh CLI
python -m src fetch --owner octocat --repo hello-world --mode cli

# Fetch with filters
python -m src fetch --owner octocat --repo hello-world --mode api --branch main --status completed

# Provide token explicitly
python -m src fetch --owner octocat --repo hello-world --mode api --token ghp_xxxxxxxxxxxx

# Incremental fetch (bonus)
python -m src fetch --owner octocat --repo hello-world --mode api --incremental
```

## Expected Menu Usage

```
Interactive Menu

1. Add workflow run
2. List all runs
...
N. Fetch from GitHub  # NEW
N+1. Exit

Select option: N

--- Fetch Workflow Runs from GitHub ---
Owner: octocat
Repository: hello-world
Fetch mode (api/cli): api
Filter by branch? (leave blank to skip): main
Filter by status? (leave blank to skip): completed
Filter by created-after date? (leave blank to skip): 2025-05-01

Fetching from GitHub...
Fetched 42 workflow run(s) from octocat/hello-world

Press Enter to continue...
```

---

## Summary of Changes

**New modules:**
- `src/auth/github_auth.py` — PAT resolution and validation
- `src/services/github_api_fetcher.py` — REST API fetcher
- `src/services/github_cli_fetcher.py` — gh CLI fetcher
- `src/models/github_workflow_run_factory.py` — Response converter

**Modified modules:**
- `src/cli/workflow_cli.py` — Add `fetch` subcommand
- `src/cli/interactive_menu.py` — Add fetch menu option

**Dependencies (may need to add):**
- `requests` — For HTTP calls to GitHub REST API (if not already present)
- Standard library: `subprocess` (for gh CLI), `os`, `getpass` (for secure prompts), `json`, `datetime`

**No changes to domain model** — WorkflowRun already compatible with GitHub API fields

**No changes to storage** — Persist via existing WorkflowRunService and WorkflowJsonStorage

---

## Validation & Testing Scope

### Unit Tests (Expected)

**Authentication:**
- Token resolution priority (env > file > prompt)
- Token validation (format check)
- Error handling (invalid token, missing secrets file)

**Fetchers:**
- API response parsing (mock requests)
- gh CLI output parsing (mock subprocess)
- Pagination logic
- Error handling (HTTP errors, timeouts)

**Factory:**
- Field mapping (GitHub → WorkflowRun)
- Enum conversion (status, conclusion)
- Datetime parsing
- Duration calculation
- Edge cases (missing fields, null values)

**CLI Integration:**
- Argument parsing
- Handler logic (token resolution, fetcher selection)
- Error messages

**Interactive Menu:**
- Prompt flow
- Handler invocation
- Result display

### Manual Testing (Expected)

- Fetch from real GitHub repo (with mock or test repo)
- Token validation flow (env, file, prompt)
- Error handling (invalid token, rate limit, network error)
- Filtering (branch, status, created-after)
- Both API and CLI modes

---

## Conclusion

Task 08 requires extending the GitHub Workflow Manager with GitHub integration. The feature must:

1. Fetch workflow runs from GitHub (REST API or gh CLI)
2. Convert GitHub API responses to the existing WorkflowRun domain model
3. Manage authentication securely (env var → file → user prompt)
4. Handle errors gracefully (rate limits, invalid tokens, network issues)
5. Integrate with both CLI and interactive menu interfaces
6. Persist runs via existing WorkflowRunService

**Key new components:**
- Authentication manager (PAT resolution and validation)
- Two fetcher implementations (API and CLI)
- Response converter (GitHub API → WorkflowRun)
- CLI subcommand and interactive menu option

**No breaking changes to existing code** — domain model and storage remain unchanged.

**Optional enhancements:**
- Incremental fetch (store last fetch time)
- Filtering parameters in fetch requests
- Progress indication during large fetches

The implementation follows existing patterns (service layer, factory methods, argparse CLI, interactive menu) for consistency with the codebase.
