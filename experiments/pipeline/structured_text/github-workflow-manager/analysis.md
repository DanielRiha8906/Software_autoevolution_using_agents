# Task 08 - GitHub Integration: Analysis Report

## Task Summary

Add optional GitHub integration to fetch workflow runs via GitHub API or CLI and convert fetched data to the application's domain model.

**Must Have:**
- Add mode: `github_fetch_mode` (new fetch strategy to complement manual entry)
- Fetch workflow runs via GitHub REST API (using `requests`) or `gh` CLI
- Convert fetched data into WorkflowRun and WorkflowRunAttempt domain models
- Resolve PAT (Personal Access Token) priority: GITHUB_TOKEN env var → secrets/.env → prompt user
- Do not persist user-entered PAT unless configured
- Accessible via `python -m src` (both interactive menu and CLI flag)

**Should Have:**
- Handle API errors gracefully (network failures, auth errors, rate limits)
- Validate token before requests (test connectivity)

---

## Current Architecture Overview

### Layered Application Structure

```
Application Entrypoint (__main__.py)
    ↓
Interface Layer (workflow_cli.py, interactive_menu.py)
    ├── CLI: argparse-driven one-shot commands
    └── Interactive: multi-step menu-driven interface
    ↓
Service Layer (WorkflowRunService, WorkflowAttemptService, Trackers, Statistics, Portability)
    ├── WorkflowRunService — CRUD + filtering for runs
    ├── WorkflowAttemptService — CRUD + filtering for attempts
    ├── WorkflowRunTracker — run creation facade (generates UUIDs, timestamps)
    ├── WorkflowAttemptTracker — attempt creation facade
    ├── WorkflowStatisticsService — report generation
    └── WorkflowDataPortabilityService — export/import JSON
    ↓
Storage Layer (WorkflowJsonStorage, WorkflowAttemptJsonStorage)
    ├── JSON file persistence
    └── Load/save operations
    ↓
Domain Models (WorkflowRun, WorkflowRunAttempt, enums)
    ├── Dataclasses with serialization (to_dict/from_dict)
    ├── State query methods
    └── Type-safe enums
```

### Entry Point Pattern

File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/__main__.py`

Currently:
- Initializes storage layers (WorkflowJsonStorage, WorkflowAttemptJsonStorage)
- Instantiates services (WorkflowRunService, WorkflowAttemptService, WorkflowStatisticsService, WorkflowDataPortabilityService)
- Routes to CLI or interactive menu based on sys.argv presence
- All services are injected into both CLI and menu functions

New GitHub integration must follow same pattern: create service → initialize in __main__.py → pass to CLI/menu.

### CLI Routing Pattern

File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/cli/workflow_cli.py`

Current subcommands:
- `add` — manually add workflow run
- `list` — list runs with optional filters
- `detail` — show single run
- `query-state` — query run state
- `attempt add/list/detail/query-state` — attempt management
- `report` — generate statistics
- `export runs/attempts` — export data
- `import runs/attempts` — import data

New `fetch` subcommand needed for GitHub integration:
- `fetch --owner <owner> --repo <repo> [--workflow <name>] [--limit <n>] [--mode api|cli]`

### Interactive Menu Pattern

File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/cli/interactive_menu.py`

Current menu structure:
```
Main menu options:
  1. Workflow Runs → run_menu (add, list, detail, filter, query state)
  2. Workflow Attempts → attempt_menu (add, list, detail, filter, query state)
  3. Statistics → view_statistics
  4. Export/Import Data → portability_menu
  5. Exit
```

New menu option needed:
- Option "Fetch from GitHub" in main menu (before exit) → github_fetch_menu with prompts for owner, repo, workflow name, token source

---

## Existing Domain Model Structure

### WorkflowRun
File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/models/workflow_run.py`

Fields:
- `id: str` — unique identifier (currently UUID generated locally)
- `workflow_name: str` — name of the workflow
- `branch: str` — git branch
- `status: WorkflowStatus` — enum (queued, in_progress, completed, waiting, requested, pending)
- `conclusion: Optional[WorkflowConclusion]` — enum (success, failure, cancelled, skipped, timed_out, action_required, neutral, stale) or None
- `created_at: datetime` — UTC timestamp
- `updated_at: Optional[datetime]` — UTC timestamp or None
- `run_number: Optional[int]` — GitHub run number (optional, can be fetched from API)
- `commit_sha: Optional[str]` — commit SHA (optional, can be fetched from API)
- `duration_seconds: float` — execution time in seconds

Methods:
- `to_dict() / from_dict()` — serialization
- `is_terminal(), is_running(), is_successful(), is_failed(), is_cancelled()` — state queries

### WorkflowRunAttempt
File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/models/workflow_attempt.py`

Fields:
- `id: str` — unique identifier
- `run_id: str` — foreign key to WorkflowRun
- `attempt_number: int` — sequence number (1, 2, 3...)
- `status: WorkflowStatus` — same as WorkflowRun
- `conclusion: Optional[WorkflowConclusion]` — same as WorkflowRun
- `started_at: datetime` — UTC timestamp
- `completed_at: Optional[datetime]` — UTC timestamp or None
- `duration_seconds: float` — execution time in seconds
- `logs_url: Optional[str]` — URL to logs (can be fetched from API)

Methods:
- `to_dict() / from_dict()` — serialization
- `is_terminal(), is_running(), is_successful(), is_failed(), is_cancelled()` — state queries

### Enums

**WorkflowStatus:** queued, in_progress, completed, waiting, requested, pending

**WorkflowConclusion:** success, failure, cancelled, skipped, timed_out, action_required, neutral, stale

---

## Service Layer: Existing Patterns

### WorkflowRunService
File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/services/workflow_run_service.py`

Pattern:
- Constructor takes `WorkflowJsonStorage` → loads data into `self._runs: List[WorkflowRun]`
- Public methods: `add_workflow_run(run)`, `list_runs()`, `get_run_detail(run_id)`, various `filter_*` methods
- Private method: `_persist()` calls storage.save(self._runs)
- All mutations immediately persist to JSON

### WorkflowRunTracker
File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/services/workflow_run_tracker.py`

Pattern:
- High-level facade for creating WorkflowRun instances
- Constructor: `__init__(service, attempt_service)`
- Public method: `track(workflow_name, branch, status, ...)` → creates WorkflowRun, calls service.add_workflow_run()
- Generates UUIDs and timestamps automatically (not from external data)

### WorkflowAttemptService & Tracker

Similar pattern to runs: service handles CRUD, tracker is creation facade.

---

## GitHub API / Data Mapping

### GitHub REST API Response Structure (Workflow Runs)

From GitHub Actions API: GET /repos/{owner}/{repo}/actions/runs

Response contains array of runs with fields:
- `id` — numeric run ID (convert to string for domain model id field)
- `name` — workflow name (maps to workflow_name)
- `status` — GitHub status: "queued", "in_progress", "completed", "waiting", "requested", "pending" (maps directly to WorkflowStatus)
- `conclusion` — GitHub conclusion: "success", "failure", "cancelled", "skipped", "timed_out", "action_required", "neutral", "stale" or null (maps directly to WorkflowConclusion)
- `head_branch` — branch name (maps to branch)
- `run_number` — numeric run number (maps to run_number)
- `head_sha` — commit SHA (maps to commit_sha)
- `created_at` — ISO timestamp string (parse to datetime, maps to created_at)
- `updated_at` — ISO timestamp string (parse to datetime, maps to updated_at)

Derived:
- `duration_seconds` — Not directly in API response. Calculate from created_at and updated_at if status is completed, otherwise 0.0

### GitHub REST API Response Structure (Workflow Run Attempts)

From GitHub Actions API: GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts

Response contains array of attempts with fields:
- `id` — numeric attempt ID (convert to string)
- `attempt_number` — sequence number
- `status` — same enum as runs
- `conclusion` — same enum as runs
- `created_at` — ISO timestamp (maps to started_at)
- `completed_at` — ISO timestamp or null (maps to completed_at)
- `name` — workflow name (for reference, not stored in WorkflowRunAttempt)

Derived:
- `run_id` — passed as parameter from the run fetch loop
- `duration_seconds` — calculate from created_at and completed_at if available

---

## Required Changes: File-by-File Scope

### NEW FILES

#### 1. src/services/github_integration_service.py
Purpose: Fetch data from GitHub API or CLI and convert to domain models.

Responsibilities:
- Token resolution (env var → secrets/.env → prompt user)
- API client initialization (requests library for REST API, or subprocess for gh CLI)
- Fetch workflow runs for a given owner/repo
- Fetch workflow attempts for a given run
- Convert GitHub API response → WorkflowRun / WorkflowRunAttempt instances
- Error handling (network, auth, rate limits, API errors)
- Token validation before fetching

Key methods:
- `__init__(fetch_mode: str = "api")` — mode: "api" (requests) or "cli" (gh)
- `_resolve_token() -> str` — check GITHUB_TOKEN env, then secrets/.env, then prompt
- `_validate_token(token: str) -> bool` — test token validity (shallow API call)
- `fetch_runs(owner: str, repo: str, workflow_name: Optional[str] = None, limit: int = 30) -> List[WorkflowRun]`
- `fetch_run_attempts(owner: str, repo: str, run_id: str) -> List[WorkflowRunAttempt]`
- `_convert_api_run(api_data: dict, repo: str) -> WorkflowRun` — private helper
- `_convert_api_attempt(api_data: dict, run_id: str, repo: str) -> WorkflowRunAttempt` — private helper
- `_call_gh_cli(args: List[str]) -> str` — private helper for subprocess execution
- `_call_api(url: str, method: str = "GET", data: Optional[dict] = None) -> dict` — private helper for requests

#### 2. tests/test_github_integration_service.py
Unit and integration tests for:
- Token resolution logic (mocking env vars, file reads)
- API response parsing (mock GitHub responses)
- Conversion logic (API data → domain models)
- Error handling (network errors, auth failures, invalid responses)
- CLI mode testing (mocking subprocess calls)
- API mode testing (mocking requests library)

### MODIFIED FILES

#### 1. src/__main__.py
Add initialization of GitHubIntegrationService:
- Create instance with fetch_mode parameter (default "api")
- Pass to CLI and interactive menu

#### 2. src/cli/workflow_cli.py
Add new subcommand `fetch`:
- `fetch` subparser with subcommands:
  - `fetch runs` — fetch workflow runs
    - `--owner <owner>` (required)
    - `--repo <repo>` (required)
    - `--workflow <name>` (optional, filter to specific workflow)
    - `--limit <n>` (optional, default 30)
    - `--mode api|cli` (optional, default api)
    - `--token <token>` (optional, for testing or explicit override)
  - `fetch attempts` — fetch attempts for a specific run
    - `--owner <owner>` (required)
    - `--repo <repo>` (required)
    - `--run-id <id>` (required)
    - `--mode api|cli` (optional)
    - `--token <token>` (optional)

Integration with existing services:
- After fetching, call `WorkflowRunService.add_workflow_run()` for each run
- After fetching attempts, call `WorkflowAttemptService.add_attempt()` for each attempt
- Display summary (count added, count skipped due to duplicate ID)

#### 3. src/cli/interactive_menu.py
Add new menu option:
- "Fetch from GitHub" → `_github_fetch_menu()`

Menu flow:
1. Prompt user for owner (required)
2. Prompt user for repo (required)
3. Prompt user for workflow name (optional)
4. Prompt user for mode (api or cli, default api)
5. Prompt user for token source (env, secrets file, prompt, or skip)
6. Call GitHubIntegrationService.fetch_runs() and display results
7. Option to fetch attempts for first result (or show menu to select run)

#### 4. src/services/__init__.py
Export GitHubIntegrationService in __all__

---

## Implementation Scope: Token Management

### Token Resolution Priority (Must Have)
1. Check `GITHUB_TOKEN` environment variable (os.getenv("GITHUB_TOKEN"))
2. If not found, check `secrets/.env` file in working directory
   - Format: `GITHUB_TOKEN=ghp_...` (or similar)
   - Use dotenv or manual file parsing
3. If not found, prompt user interactively
4. Do NOT persist user-entered token unless explicitly configured

### Token Validation (Should Have)
Before using token for actual API calls:
- Make a simple GET request: https://api.github.com/user (or gh auth status for CLI mode)
- If valid, continue with run/attempt fetches
- If invalid (401), retry prompt or fail gracefully with error message

### Sensitive Data Handling
- Never log full token value (show only first 4 chars: "ghp_****")
- Do not write prompted token to any file
- Keep token in memory only for duration of session
- Close file handles after reading secrets/.env

---

## Integration Points: Exact Files and Functions

### Entry Point
**File:** `src/__main__.py`
**Function:** `main()`

Before line 27 (if len(sys.argv) == 1), after portability_service init:
```python
# Create GitHub integration service
github_service = GitHubIntegrationService(fetch_mode="api")
```

Update function signatures:
```python
run_interactive(service, attempt_service, stats_service, portability_service, github_service)
run_cli(service, attempt_service, stats_service, portability_service, github_service, args)
```

### CLI
**File:** `src/cli/workflow_cli.py`
**Function:** `build_parser()`

Add after line 276 (after import section):
```python
# fetch subcommand with runs/attempts subcommands
fetch_p = sub.add_parser("fetch", help="Fetch workflow runs from GitHub")
fetch_sub = fetch_p.add_subparsers(dest="fetch_command", required=True)

fetch_runs_p = fetch_sub.add_parser("runs", help="Fetch workflow runs from GitHub")
fetch_runs_p.add_argument("--owner", required=True, help="GitHub repository owner")
fetch_runs_p.add_argument("--repo", required=True, help="GitHub repository name")
fetch_runs_p.add_argument("--workflow", default=None, help="Filter by workflow name (optional)")
fetch_runs_p.add_argument("--limit", type=int, default=30, help="Maximum runs to fetch (default 30)")
fetch_runs_p.add_argument("--mode", choices=["api", "cli"], default="api", help="Fetch mode (default api)")
fetch_runs_p.add_argument("--token", default=None, help="GitHub token (optional, uses env/file if omitted)")

fetch_attempts_p = fetch_sub.add_parser("attempts", help="Fetch workflow attempts from GitHub")
fetch_attempts_p.add_argument("--owner", required=True, help="GitHub repository owner")
fetch_attempts_p.add_argument("--repo", required=True, help="GitHub repository name")
fetch_attempts_p.add_argument("--run-id", required=True, help="Workflow run ID")
fetch_attempts_p.add_argument("--mode", choices=["api", "cli"], default="api", help="Fetch mode")
fetch_attempts_p.add_argument("--token", default=None, help="GitHub token (optional)")
```

**Function:** `run_cli()` command handler

Add before line 279 (after command routing):
```python
elif ns.command == "fetch":
    if github_service is None:
        print("GitHub service not initialized.", file=sys.stderr)
        sys.exit(1)
    
    if ns.fetch_command == "runs":
        # Call github_service.fetch_runs(...)
        # Add results via tracker.track(...)
        # Report count added/skipped
        pass
    elif ns.fetch_command == "attempts":
        # Call github_service.fetch_run_attempts(...)
        # Add results via tracker.create_attempt(...)
        # Report count added/skipped
        pass
```

### Interactive Menu
**File:** `src/cli/interactive_menu.py`

Add to MENU list (before "Exit" entry):
```python
("Fetch from GitHub", "github_fetch"),
```

Add handler in `run_interactive()` after portability check:
```python
elif submenu == "github_fetch":
    if github_service is None:
        print("GitHub service not initialized.")
        continue
    _github_fetch_menu(service, attempt_service, github_service, tracker)
```

Add new function `_github_fetch_menu()`:
- Prompt for owner, repo, workflow name, mode, token source
- Call github_service.fetch_runs()
- Call service.add_workflow_run() or tracker.track() for each result
- Display results
- Offer to fetch attempts for selected runs

---

## Error Handling Strategy

### Network Errors
- requests.ConnectionError → "Network error: check internet connection"
- Subprocess failure for gh CLI → "gh CLI not available or authentication failed"

### Authentication Errors (401, 403)
- github_service._validate_token() fails → "Token validation failed. Check GITHUB_TOKEN or delete secrets/.env and try again."

### Rate Limiting (403 rate limit)
- Detect from response header → "GitHub API rate limit exceeded. Try again later."

### Invalid Data Responses
- Missing expected fields → "Invalid GitHub API response: missing field '<name>'"
- Invalid enum values → Skip that record and continue (log warning)

### File I/O Errors
- secrets/.env not readable → Fall back to prompt
- Token prompt cancelled (Ctrl+C) → Exit with "Cancelled"

---

## Ambiguities and Working Assumptions

### 1. Token File Location
Assumption: `secrets/.env` in working directory (the root of the experiment folder).
Alternative: Could be `.env` in working directory. Decision: Use `secrets/.env` first for explicit separation of secrets directory.

### 2. Fetch Mode Default
Assumption: Default to REST API (`requests` library) because it's more portable and doesn't require `gh` CLI installation.
Alternative: Default to `gh` CLI if available, fall back to requests. Decision: Stick with requests as default, CLI as opt-in.

### 3. Duplicate Run Handling
Assumption: If a run with the same ID already exists (from manual entry or prior fetch), skip it and report count.
Alternative: Allow option to overwrite. Decision: Skip with message (consistent with import behavior in Task 7).

### 4. Attempt Fetching
Assumption: Attempts can be fetched separately per run (not automatically when fetching runs).
Rationale: API quota and user control—not all workflows have multiple attempts.

### 5. Token Persistence
Assumption: User-entered token is NOT persisted anywhere (kept in memory only for this session).
Rationale: Security best practice and explicit "don't persist" requirement in must-have.

### 6. Datetime Handling
Assumption: GitHub API returns ISO 8601 timestamps. Parse with `datetime.fromisoformat()`.
Consideration: GitHub may use 'Z' suffix (UTC). Handle with timezone_converter utility or Python's fromisoformat().

### 7. Duration Calculation
Assumption: For runs, duration = (updated_at - created_at).total_seconds() if both exist, else 0.0
Assumption: For attempts, duration = (completed_at - started_at).total_seconds() if both exist, else 0.0
Rationale: Matches existing model convention.

---

## Testing Strategy

### Unit Tests (Mock All External Calls)
- Token resolution: mock os.getenv, file reads
- API parsing: mock requests.get responses
- Enum conversions: GitHub API data → domain models
- Error cases: 401, 403, 404, network error, invalid JSON

### Integration Tests
- End-to-end with github_service → add to service → verify persistence

### Test Fixtures
- Sample GitHub API response JSON (use real examples from GitHub docs)
- Valid and invalid tokens
- Various workflow statuses/conclusions

---

## Scope Boundaries

### In Scope
- Fetch workflow runs from GitHub (owner/repo/workflow filter)
- Fetch workflow attempts for a given run
- Convert API response to WorkflowRun and WorkflowRunAttempt models
- Token resolution (env → file → prompt)
- Error handling (network, auth, rate limits)
- Token validation (shallow check)
- Interactive menu and CLI flag entry points
- Persist fetched data to existing JSON storage

### Out of Scope
- Webhook-based automatic fetching (pull-based only)
- Graphql API (REST API only, plus gh CLI as alternative)
- Advanced filtering (status, conclusion, date range) — that's for existing filter commands
- Caching (fetch fresh each time)
- Data transformation beyond domain model conversion
- Visualization of fetched runs

---

## Summary: Required Implementation Files and Functions

**New Service Class:**
- `src/services/github_integration_service.py` — GitHubIntegrationService

**Modified Entry Point:**
- `src/__main__.py` — Initialize github_service, pass to CLI/menu

**Modified CLI:**
- `src/cli/workflow_cli.py` — Add `fetch` subcommand with runs/attempts subcommands

**Modified Interactive Menu:**
- `src/cli/interactive_menu.py` — Add "Fetch from GitHub" menu option with _github_fetch_menu()

**Modified Exports:**
- `src/services/__init__.py` — Export GitHubIntegrationService

**New Tests:**
- `tests/test_github_integration_service.py` — Unit tests for service

---

## Design Principles Applied

1. **Layered Architecture:** GitHub service sits at service layer, independent of CLI/menu
2. **Dependency Injection:** Service passed to CLI/menu at initialization
3. **Converter Pattern:** github_service handles GitHub API data → domain models conversion
4. **Facade Pattern:** WorkflowRunTracker used to create WorkflowRun instances with automatic UUID/timestamp generation
5. **Error Handling:** Graceful degradation (skip invalid records, retry token prompt)
6. **Security:** Token not persisted unless explicitly configured
7. **Testability:** Service methods are pure functions (except I/O), easy to mock
