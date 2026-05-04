# Progress Report

## Task 01: Duration Tracking for WorkflowRun

### Task Summary
Added explicit duration tracking to the WorkflowRun model. The system now tracks workflow execution time via a `duration_seconds: float` attribute that is stored, persisted, and displayed.

### Files Changed
- `src/models/workflow_run.py` — Added duration_seconds field, updated to_dict() and from_dict() methods with validation
- `src/services/workflow_run_tracker.py` — Added duration_seconds parameter to track() method signature
- `src/cli/workflow_cli.py` — Added --duration-seconds CLI argument, updated _fmt_run() display
- `src/cli/interactive_menu.py` — Added duration prompt, updated _fmt_run() display
- `tests/test_workflow_json_storage.py` — Added 3 tests for serialization, deserialization, and validation
- `tests/test_workflow_run_service.py` — Updated _make_run() helper, added 1 persistence test
- `tests/test_workflow_cli.py` — Created 7 new tests for CLI integration
- `tests/test_interactive_menu.py` — Created 5 new tests for interactive menu
- `artifacts/class_diagram.puml` — Added duration_seconds field to WorkflowRun class
- `artifacts/activity_diagram_main.puml` — Added duration-seconds argument to CLI flow
- `artifacts/activity_diagram_interactive.puml` — Added duration prompt step to interactive flow

### Test Result
✓ **25 tests passed** (0.07s)

All tests pass. Coverage includes:
- WorkflowRun dataclass construction with new field
- Serialization/deserialization with duration_seconds
- Validation of non-negative values
- Backward compatibility with old JSON files missing duration_seconds
- CLI argument parsing with --duration-seconds flag
- Interactive menu prompt for duration input
- Default value behavior (0.0)
- Display formatting in both CLI and interactive modes

### Implementation Details

**Must Have (All Completed):**
- ✓ Added attribute `duration_seconds: float` to `WorkflowRun`
- ✓ Stored and persisted in JSON storage layer
- ✓ Value represents total execution time in seconds
- ✓ Updated serialization/deserialization logic

**Should Have (Completed):**
- ✓ Validate that duration is non-negative (ValueError raised in from_dict)
- ✓ Default to `0.0` if not provided (field default and from_dict default)

**Could Have (Not Implemented):**
- Higher precision (milliseconds) — out of scope for this task

**Won't Have (Not Applicable):**
- External time measurement tools — out of scope

Duration: 340.0s | Cost: $0.569500 USD | Turns: 18

## Task 02: Workflow Run State Query Methods

### Task Summary
Implemented encapsulated domain logic for workflow run states. The WorkflowRun model now provides query methods (`is_terminal()`, `is_running()`, `is_successful()`, `is_failed()`, `is_cancelled()`) that derive state strictly from `status` and `conclusion` fields. All functionality is accessible via both interactive menu and CLI with a new `query-state` command.

### Files Changed
- `src/models/workflow_run.py` — Added 5 state query methods (is_terminal, is_running, is_successful, is_failed, is_cancelled)
- `src/cli/workflow_cli.py` — Added query-state subparser command with run_id positional argument
- `src/cli/interactive_menu.py` — Added _query_run_state() function and menu option "Query workflow state"
- `tests/test_workflow_run_state_queries.py` — Created new test file with 15 comprehensive test cases
- `artifacts/use_case_diagram.puml` — Added "Query workflow state" use case for both CLI and interactive modes
- `artifacts/activity_diagram_main.puml` — Added query-state command handler to CLI activity flow
- `artifacts/activity_diagram_interactive.puml` — Added query workflow state option to interactive menu flow

### Test Result
✓ **40 tests passed** (0.10s)

All tests pass including:
- 5 running state tests (QUEUED, IN_PROGRESS, WAITING, REQUESTED, PENDING)
- 1 successful state test (COMPLETED + SUCCESS)
- 3 failed state tests (COMPLETED + FAILURE, TIMED_OUT, ACTION_REQUIRED)
- 4 other terminal state tests (COMPLETED + CANCELLED, SKIPPED, NEUTRAL, STALE)
- 2 mutual exclusivity constraint tests (is_terminal/is_running, is_successful/is_failed)

### Implementation Details

**Must Have (All Completed):**
- ✓ Implemented methods: is_terminal(), is_successful(), is_failed(), is_running()
- ✓ Methods derive state strictly from status and conclusion fields
- ✓ All functionality accessible via python -m src (both interactive menu and CLI flag)

**Should Have (Completed):**
- ✓ is_terminal() and is_running() are mutually exclusive (logical complements)
- ✓ is_successful() and is_failed() are mutually exclusive
- ✓ Comprehensive unit tests covering all state combinations

**Could Have (Completed):**
- ✓ Convenience method is_cancelled() derived from conclusion

**Won't Have (Not Applicable):**
- Enum modifications — working with existing definitions

Duration: 371.8s | Cost: $0.673735 USD | Turns: 17

## Task 03: Workflow Run Attempts

### Task Summary
Implemented a new `WorkflowRunAttempt` entity to model individual execution attempts of a workflow run. The system now tracks multiple attempts per workflow with independent status, conclusion, timing, and logs. Full service layer, persistence, and CLI/menu integration are complete.

### Files Changed
- `src/models/workflow_run_attempt.py` — NEW: WorkflowRunAttempt dataclass with 9 attributes and state query methods
- `src/storage/workflow_attempt_json_storage.py` — NEW: JSON persistence for attempts
- `src/services/workflow_attempt_service.py` — NEW: CRUD and filtering service for attempts
- `src/services/workflow_attempt_tracker.py` — NEW: Facade for attempt creation
- `src/services/workflow_run_tracker.py` — Modified: Added create_attempt() method, integrated with attempt service
- `src/cli/workflow_cli.py` — Modified: Added 4 attempt subcommands (add, list, detail, query-state)
- `src/cli/interactive_menu.py` — Modified: Added 5 attempt operations (add, list, detail, filter, query-state)
- `src/__main__.py` — Modified: Initialize WorkflowAttemptService and wire to CLI/menu
- `src/models/__init__.py` — Modified: Export WorkflowRunAttempt
- `tests/test_workflow_run_attempt.py` — NEW: 29 tests for serialization and state queries
- `tests/test_workflow_attempt_json_storage.py` — NEW: 20 tests for storage layer
- `tests/test_workflow_attempt_service.py` — NEW: 20 tests for CRUD and filtering
- `tests/test_workflow_run_tracker_attempt.py` — NEW: 36 tests for tracker method
- `artifacts/class_diagram.puml` — Modified: Added attempt classes and 1-to-many relationship
- `artifacts/component_diagram.puml` — Modified: Added attempt components and persistence
- `artifacts/activity_diagram_interactive.puml` — Modified: Added attempt menu options
- `artifacts/activity_diagram_main.puml` — Modified: Added attempt CLI commands
- `artifacts/state_diagram_attempt_execution.puml` — NEW: State lifecycle for attempts

### Test Result
✓ **105 tests passed** (0.45s)

All tests pass including:
- 29 WorkflowRunAttempt serialization and state query tests
- 20 storage layer persistence and roundtrip tests
- 20 service CRUD and filtering operation tests
- 36 WorkflowRunTracker.create_attempt() integration tests with parametrization

### Implementation Details

**Must Have (All Completed):**
- ✓ Created class `WorkflowRunAttempt` with dataclass pattern
- ✓ Attributes: id, run_id, attempt_number, status, conclusion, started_at, completed_at, duration_seconds, logs_url
- ✓ Established relationship to `WorkflowRun` (1-to-many via run_id foreign key)
- ✓ JSON persistence via WorkflowAttemptJsonStorage

**Should Have (Completed):**
- ✓ Support serialization/deserialization (to_dict/from_dict following WorkflowRun pattern)
- ✓ Validation (duration_seconds >= 0, all status/conclusion enums work)
- ✓ State query methods (is_terminal, is_running, is_successful, is_failed, is_cancelled)
- ✓ Full CLI integration (add, list, detail, query-state commands)
- ✓ Full interactive menu integration (all operations accessible via menu)

**Could Have (Completed):**
- ✓ duration_seconds field included with validation

**Won't Have (Not Applicable):**
- Performance optimization — out of scope

Duration: 654.8s | Cost: $1.246197 USD | Turns: 13

## Task 04: Attempt Management Service

### Task Summary
Enhanced `AttemptService` with duplicate validation and sorting. The system now ensures no duplicate attempt numbers per run via composite key validation on (run_id, attempt_number), and returns filtered attempts sorted by attempt number. All functionality is already accessible via both CLI and interactive menu.

### Files Changed
- `src/services/workflow_attempt_service.py` — Modified 2 methods: `add_attempt()` (added duplicate (run_id, attempt_number) validation), `filter_by_run_id()` (added sorting by attempt_number)
- `tests/test_workflow_attempt_service.py` — Added 18 new tests (7 for duplicate validation, 11 for sorting behavior) and fixed 11 existing tests to respect new validation
- `artifacts/class_diagram.puml` — Updated WorkflowAttemptService note to document validation and sorting behavior
- `artifacts/activity_diagram_main.puml` — Enhanced create-attempt and list-attempts flows with validation error paths and sorting documentation
- `artifacts/activity_diagram_interactive.puml` — Enhanced Create workflow attempt and List attempts by run flows

### Test Result
✓ **43 tests passed** (0.38s)

All tests pass including:
- 7 duplicate (run_id, attempt_number) validation tests
- 11 sorting by attempt_number tests
- 25 existing tests (all updated to work with new validation)

### Implementation Details

**Must Have (All Completed):**
- ✓ Implemented `AttemptService` with create and retrieve by run_id
- ✓ Integrated with existing JSON storage mechanism
- ✓ Duplicate attempt numbers per run prevented via composite key validation
- ✓ All functionality accessible via `python -m src` (both CLI and interactive menu)

**Should Have (All Completed):**
- ✓ Ensure no duplicate attempt numbers per run (validated in add_attempt)
- ✓ All edge cases covered (same run_id + different attempt_numbers allowed, same attempt_number + different run_ids allowed)

**Could Have (Completed):**
- ✓ Sorting by attempt number (filter_by_run_id now returns sorted results)

**Won't Have (Not Applicable):**
- Caching layer — out of scope

Duration: 421.9s | Cost: $0.829924 USD | Turns: 21

## Task 05: Filtering Capabilities for Workflow Runs

### Task Summary
Implemented comprehensive filtering capabilities for workflow runs and attempts. The system now supports filtering by duration range (min/max seconds), timestamp range (created/updated before/after using CEST/UTC+2 timezone support), and attempts presence (with/without attempts). All filters can be combined using AND logic, and are accessible via both interactive menu and CLI flags.

### Files Changed

**New Files:**
- `src/utils/timezone_converter.py` — Timezone conversion utility with parse_datetime_with_timezone(), datetime_to_utc(), format_datetime_for_display()
- `tests/test_timezone_converter.py` — 25 tests for timezone conversion functionality
- `tests/test_workflow_run_service_filters.py` — 41 tests for run filtering (duration, timestamps, attempts, composite)
- `tests/test_workflow_attempt_service_filters.py` — 35 tests for attempt filtering (duration, timestamps, composite)
- `tests/test_workflow_cli_filters.py` — 32 tests for CLI filter flag integration
- `tests/test_workflow_interactive_menu_filters.py` — 22 tests for interactive menu filtering

**Modified Files:**
- `src/services/workflow_run_service.py` — Added filter_by_duration_range(), filter_by_created_at(), filter_by_updated_at(), filter_by_has_attempts(), filter_runs() (composite)
- `src/services/workflow_attempt_service.py` — Added filter_by_duration_range(), filter_by_started_at(), filter_by_completed_at(), filter_attempts() (composite)
- `src/cli/workflow_cli.py` — Added CLI flags for duration (--duration-min, --duration-max), timestamps (--created-before/after, --updated-before/after, --started-before/after, --completed-before/after), attempts (--with-attempts, --without-attempts), timezone (--timezone), and composite filtering logic
- `src/cli/interactive_menu.py` — Added _build_filter_criteria_menu(), _build_attempt_filter_criteria_menu(), enhanced _filter_menu(), _filter_attempts_menu(), _run_menu(), _attempt_menu() with multi-filter support
- `artifacts/class_diagram.puml` — Added timezone_converter module, new filter methods to services
- `artifacts/component_diagram.puml` — Added utilities layer with timezone_converter component
- `artifacts/activity_diagram_main.puml` — Enhanced list and attempt-list flows with composite filtering
- `artifacts/activity_diagram_interactive.puml` — Enhanced filter menu flows with multi-filter selection
- `artifacts/use_case_diagram.puml` — Added filter use cases and timezone utilities

### Test Result
✓ **313 tests passed** (1.02s)

All tests pass including:
- 25 timezone converter tests (UTC, CEST, UTC+2, error handling)
- 41 run service filter tests (duration range, timestamp ranges, attempts presence, composite filters)
- 35 attempt service filter tests (duration range, timestamp ranges, composite filters)
- 32 CLI integration tests (all filter flags, timezone support, error conditions)
- 22 interactive menu filter tests (multi-filter scenarios, edge cases)
- Pre-existing tests (158 tests still passing)

### Implementation Details

**Must Have (All Completed):**
- ✓ Duration range filtering (min/max duration_seconds) for runs and attempts
- ✓ Timestamp filtering (created/updated before/after using CEST/UTC+2) for runs
- ✓ Timestamp filtering (started/completed before/after) for attempts
- ✓ Attempts presence filtering (runs with/without attempts)
- ✓ Return filtered collections from service methods
- ✓ All functionality accessible via `python -m src` (interactive menu + CLI flags)

**Should Have (All Completed):**
- ✓ Combine multiple filters in single query call with AND logic
- ✓ Timezone conversion for CEST/UTC+2 support in timestamp inputs
- ✓ All filters composable and chainable

**Could Have (Not Completed):**
- Partial string matching on string fields (not required for Task 05 scope)

**Won't Have (Not Applicable):**
- External database or indexing — all filtering in-memory on service collections

Duration: 826.8s | Cost: $1.795939 USD | Turns: 13

## Task 06: Aggregated Statistics and Insights

### Task Summary
Implemented aggregated statistics reporting for workflow runs and attempts. The system now computes structured statistics including conclusion counts, duration averages/min/max, and per-run attempt statistics. Results are returned as a typed dataclass report and accessible via both interactive menu and CLI with optional JSON output format.

### Files Changed

**New Files:**
- `src/models/workflow_statistics_report.py` — NEW: WorkflowStatisticsReport dataclass with 11 fields and to_dict() serialization method
- `src/services/workflow_statistics_service.py` — NEW: WorkflowStatisticsService class with compute_report() method and 5 private calculation helpers
- `tests/test_workflow_statistics_report.py` — NEW: 14 tests for dataclass construction and serialization
- `tests/test_workflow_statistics_service.py` — NEW: 30 tests for statistics computation and edge cases

**Modified Files:**
- `src/models/__init__.py` — Added export for WorkflowStatisticsReport
- `src/services/__init__.py` — Added export for WorkflowStatisticsService
- `src/__main__.py` — Initialize WorkflowStatisticsService and wire to CLI/menu
- `src/cli/workflow_cli.py` — Added report subcommand with --format flag (text/json), handler with formatted output
- `src/cli/interactive_menu.py` — Added "View Statistics" menu option and _view_statistics() handler
- `tests/test_workflow_cli.py` — Fixed 5 test calls to use new run_cli() signature with args keyword parameter
- `artifacts/class_diagram.puml` — Added WorkflowStatisticsReport and WorkflowStatisticsService classes with relationships
- `artifacts/component_diagram.puml` — Added statistics service to Service layer and report to Domain model
- `artifacts/activity_diagram_main.puml` — Added report CLI command flow with format selection
- `artifacts/activity_diagram_interactive.puml` — Added View Statistics menu option flow

### Test Result
✓ **362 tests passed** (0.52s)

All tests pass including:
- 14 WorkflowStatisticsReport tests (dataclass creation, serialization, None handling)
- 30 WorkflowStatisticsService tests (computation, edge cases, all calculation methods)
- 318 pre-existing tests (maintained backward compatibility with signature updates)

### Implementation Details

**Must Have (All Completed):**
- ✓ Compute statistics: count by conclusion, average duration_seconds, average attempts per run
- ✓ Return structured report object (WorkflowStatisticsReport dataclass, not plain dict)
- ✓ All new functionality accessible via `python -m src` (interactive menu "View Statistics" + CLI `report` command)

**Should Have (All Completed):**
- ✓ Use dataclass/named object for report structure
- ✓ Include min/max duration_seconds in report

**Could Have (Not Implemented):**
- Per-status breakdown of average duration — deferred for future enhancement

**Won't Have (Not Applicable):**
- Visualization layer — out of scope

**Computation Algorithms:**
- **Conclusion counts:** Group runs by conclusion.value (or None for non-terminal), count occurrences
- **Duration statistics:** Average across all runs; min/max from all durations; per-conclusion average of runs with that conclusion
- **Attempt statistics:** Count total attempts by querying attempt_service.filter_by_run_id() for each run; average per run; count runs with/without attempts
- **Edge cases handled:** Zero runs (returns 0/None values), all None conclusions (grouped as "incomplete"), runs without attempts properly counted
- **Report generation:** Generated with UTC timestamp via datetime.now(timezone.utc)

**CLI Features:**
- `python -m src report` — Human-readable formatted text output
- `python -m src report --format json` — Valid JSON serialization for programmatic use
- `python -m src` → menu option 3 → View Statistics display with same formatting

**Service Design:**
- Dependency injection of WorkflowRunService and WorkflowAttemptService
- Public methods: compute_report() (all runs), compute_report_for_runs() (filtered subset)
- Private calculation methods encapsulate each statistic computation
- Dataclass.to_dict() handles None → "incomplete" mapping and datetime → ISO format

Duration: 660.3s | Cost: $1.423226 USD | Turns: 25

## Task 07: Data Portability (Export/Import JSON)

### Task Summary
Implemented data portability functionality enabling users to export workflow runs and attempts to JSON files, and import them back with schema validation and duplicate detection. All functionality is accessible via both interactive menu and CLI with support for gracefully skipping invalid/duplicate entries on import.

### Files Changed

**New Files:**
- `src/services/workflow_data_portability_service.py` — NEW: WorkflowDataPortabilityService class with export/import methods and schema validation
- `tests/test_workflow_data_portability_service.py` — NEW: 42 comprehensive tests for service methods
- `tests/test_export_import_cli.py` — NEW: 29 CLI integration and argument parsing tests

**Modified Files:**
- `src/__main__.py` — Initialize WorkflowDataPortabilityService and wire to CLI/menu
- `src/cli/workflow_cli.py` — Added export/import subcommands with --output/-o (export) and --input/-i (import) flags, --skip-duplicates flag for imports
- `src/cli/interactive_menu.py` — Added _portability_menu() submenu with _export_runs_menu(), _import_runs_menu(), _export_attempts_menu(), _import_attempts_menu() functions
- `src/services/__init__.py` — Added export for WorkflowDataPortabilityService
- `artifacts/class_diagram.puml` — Added WorkflowDataPortabilityService class with all methods and relationships
- `artifacts/component_diagram.puml` — Added portability service component and JSON export artifacts
- `artifacts/use_case_diagram.puml` — Added 4 data portability use cases (export/import runs/attempts)
- `artifacts/activity_diagram_main.puml` — Added export/import CLI command flows
- `artifacts/activity_diagram_interactive.puml` — Added portability submenu flows

### Test Result
✓ **433 tests passed** (1.18s)

All tests pass including:
- 42 WorkflowDataPortabilityService tests (export/import, schema validation, duplicate handling, error cases)
- 29 CLI integration tests (command parsing, output formatting, error handling)
- 362 pre-existing tests (maintained backward compatibility)

### Implementation Details

**Must Have (All Completed):**
- ✓ Export runs to JSON file (WorkflowDataPortabilityService.export_runs())
- ✓ Import runs from JSON file (WorkflowDataPortabilityService.import_runs())
- ✓ Export attempts to JSON file (WorkflowDataPortabilityService.export_attempts())
- ✓ Import attempts from JSON file (WorkflowDataPortabilityService.import_attempts())
- ✓ Schema consistency validation (_validate_run_schema(), _validate_attempt_schema())
- ✓ All functionality accessible via `python -m src` (interactive menu + CLI flags)

**Should Have (All Completed):**
- ✓ Validate imported data structure (schema validation with required field checking)
- ✓ Duplicate detection by ID (skip_duplicates flag prevents re-adding existing IDs)

**Could Have (Completed):**
- ✓ Skip invalid or duplicate entries on import rather than failing entire operation (--skip-duplicates flag)

**Won't Have (Not Applicable):**
- Support external formats (CSV, DB) — out of scope

**Service Methods:**
- `export_runs(runs: List[WorkflowRun], filepath: str) -> int` — Exports runs to JSON file, returns count
- `import_runs(filepath: str, skip_duplicates: bool = False) -> Dict[str, int]` — Imports runs with validation, returns {imported, skipped, failed}
- `export_attempts(attempts: List[WorkflowRunAttempt], filepath: str) -> int` — Exports attempts to JSON file, returns count
- `import_attempts(filepath: str, skip_duplicates: bool = False) -> Dict[str, int]` — Imports attempts with validation, returns {imported, skipped, failed}
- `_validate_run_schema(data: dict)` — Validates required fields: id, workflow_name, branch, status, created_at
- `_validate_attempt_schema(data: dict)` — Validates required fields: id, run_id, attempt_number, status, started_at

**JSON Schema:**
- Runs: id, workflow_name, branch, status, conclusion, created_at, updated_at, run_number, commit_sha, duration_seconds
- Attempts: id, run_id, attempt_number, status, conclusion, started_at, completed_at, duration_seconds, logs_url

**CLI Usage:**
- `python -m src export runs --output <file.json>` — Export all runs
- `python -m src export attempts --output <file.json>` — Export all attempts
- `python -m src import runs --input <file.json> [--skip-duplicates]` — Import runs
- `python -m src import attempts --input <file.json> [--skip-duplicates]` — Import attempts

**Interactive Menu:**
- Main menu → "Export/Import Data" → Options: Export runs, Import runs, Export attempts, Import attempts
- Prompts user for file paths and duplicate handling preferences
- Displays import/export statistics (count, skipped, failed)

**Error Handling:**
- File I/O errors (file not found, permission denied) → IOError
- Invalid JSON format → ValueError
- Missing required fields → ValueError
- Invalid enum values → ValueError
- Negative duration → ValueError (existing model validation)
- Duplicate ID (when skip_duplicates=False) → ValueError
- Graceful degradation: With skip_duplicates=True, import continues and reports skipped/failed counts

Duration: 714.4s | Cost: $1.675553 USD | Turns: 14

## Task 08: GitHub Integration (Fetch Workflow Runs and Attempts)

### Task Summary
Implemented optional GitHub integration to fetch workflow runs and attempts from GitHub via REST API or `gh` CLI, with secure token resolution and conversion to domain models. All functionality is accessible via both interactive menu and CLI with comprehensive error handling.

### Files Changed

**New Files:**
- `src/services/github_integration_service.py` — NEW: GitHubIntegrationService class with token resolution, validation, and GitHub API/CLI integration
- `tests/test_github_integration_service.py` — NEW: 81 comprehensive tests for all service methods and error scenarios

**Modified Files:**
- `src/__main__.py` — Initialize GitHubIntegrationService with fetch_mode="api" and wire to CLI/menu
- `src/cli/workflow_cli.py` — Added `fetch` subcommand with `runs` and `attempts` sub-subcommands, argument parsing, handlers with duplicate detection
- `src/cli/interactive_menu.py` — Added "Fetch from GitHub" menu option and _github_fetch_menu() function with interactive prompts
- `src/services/__init__.py` — Export GitHubIntegrationService
- `artifacts/class_diagram.puml` — Added GitHubIntegrationService class with all methods and relationships
- `artifacts/component_diagram.puml` — Integrated GitHubIntegrationService into Service layer
- `artifacts/activity_diagram_interactive.puml` — Added complete "Fetch from GitHub" interactive flow
- `artifacts/use_case_diagram.puml` — Added GitHub Integration package with 5 use cases
- `artifacts/sequence_github_integration.puml` — NEW: End-to-end sequence diagram for fetch flows
- `artifacts/activity_token_resolution.puml` — NEW: Detailed token resolution flow diagram

### Test Result
✓ **514 tests passed** (1.32s)

All tests pass including:
- 10 token resolution tests (env var → secrets file → prompt priority)
- 9 token validation tests (API and CLI modes, error handling)
- 6 timestamp parsing tests (Z suffix, microseconds, timezone handling)
- 9 API run conversion tests (field mapping, enum validation, duration calculation)
- 9 API attempt conversion tests (field mapping, missing fields, duration calculation)
- 9 REST API fetch tests (success, filtering, error handling)
- 4 gh CLI fetch tests (success, invalid JSON, command failures)
- 7 REST API attempts fetch tests (success, network errors, invalid data)
- 4 gh CLI attempts fetch tests (success, invalid JSON, missing keys)
- 4 gh CLI command execution tests
- 2 token override tests
- 8 edge case tests (enum variations, special characters, long durations)
- 433 pre-existing tests (maintained backward compatibility)

### Implementation Details

**Must Have (All Completed):**
- ✓ Added mode: `github_fetch_mode` accessible via CLI and interactive menu
- ✓ Fetch workflow runs via GitHub REST API (using `requests` library)
- ✓ Fetch workflow runs via `gh` CLI (subprocess calls)
- ✓ Convert fetched GitHub API data into WorkflowRun and WorkflowRunAttempt domain models
- ✓ Token resolution priority:
  1. `GITHUB_TOKEN` environment variable
  2. `secrets/.env` file in project root (format: GITHUB_TOKEN=...)
  3. Interactive prompt (user input via getpass, not persisted)
- ✓ All functionality accessible via `python -m src` (both CLI `fetch` command and interactive menu)

**Should Have (All Completed):**
- ✓ Handle API errors gracefully (network errors, invalid tokens, rate limits, malformed responses)
- ✓ Validate token before making requests (shallow API call to /user endpoint)

**Could Have (Not Implemented):**
- Incremental fetch (only runs newer than latest stored) — deferred for future enhancement

**Won't Have (Not Applicable):**
- Full authentication management (OAuth flows, token refresh) — out of scope

**Key Features:**
- **Dual-mode operation**: REST API (requests library) as default for portability; gh CLI as alternative
- **Secure token handling**: Environment variable → secrets file → interactive prompt; user-entered tokens not persisted to disk
- **Comprehensive field mapping**: 
  - Workflow runs: id → id (string), name → workflow_name, head_branch → branch, status/conclusion → enums, timestamps → UTC datetime
  - Attempts: id → id (string), attempt_number, status/conclusion → enums, created_at → started_at, completed_at, logs_url constructed from run_id and attempt_number
- **Duration calculation**: (end_time - start_time).total_seconds() for completed runs/attempts; 0.0 for in-progress
- **Error handling**: Network errors, 401/403 auth failures, 403 rate limiting, invalid JSON, missing required fields, invalid enum values
- **Duplicate detection**: Skips existing run/attempt IDs on import with count reporting

**CLI Usage:**
- `python -m src fetch runs --owner <owner> --repo <repo> [--workflow <name>] [--limit <n>] [--mode api|cli] [--token <token>]`
- `python -m src fetch attempts --owner <owner> --repo <repo> --run-id <id> [--mode api|cli] [--token <token>]`

**Interactive Menu:**
- Main menu → "Fetch from GitHub" → Prompts for owner, repo, workflow name, fetch mode, token source
- Displays fetched runs and offers to fetch attempts for first run
- Reports added/skipped counts

**GitHub API Endpoints Used:**
- `GET /repos/{owner}/{repo}/actions/runs?per_page={limit}` — Fetch workflow runs
- `GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts` — Fetch attempts for a run
- `GET /user` (validation) — Test token validity

**Dependencies Added:**
- `requests` library (2.33.1) — Already a standard HTTP library, imported in github_integration_service.py

Duration: 833.2s | Cost: $1.736629 USD | Turns: 15

## Task 09: Layered Architecture Refactoring (Service, Storage, GitHub Adapter)

### Task Summary
Refactored the codebase to separate concerns into three distinct layers: Service layer, Storage layer, and GitHub adapter layer. The refactoring introduces abstract repository protocols for storage, extracts GitHub integration concerns into four focused adapter classes, and ensures no circular dependencies while preserving all existing public interfaces and backward compatibility.

### Files Changed

**New Files Created:**
- `src/storage/base.py` — Abstract repository protocols: `WorkflowRunRepository`, `WorkflowAttemptRepository`
- `src/adapters/__init__.py` — Adapter package initialization
- `src/adapters/github/__init__.py` — GitHub adapter subpackage initialization
- `src/adapters/github/token_resolver.py` — GitHubTokenResolver class for token resolution and validation
- `src/adapters/github/api_client.py` — GitHubApiClient class for REST API client operations
- `src/adapters/github/cli_adapter.py` — GitHubCliAdapter class for gh CLI wrapper operations
- `src/adapters/github/converter.py` — GitHubToWorkflowConverter class for GitHub API to domain model conversion
- `src/adapters/github/integration_service.py` — Refactored GitHubIntegrationService facade
- `tests/test_github_adapters.py` — 90 comprehensive tests for all four adapter classes

**Modified Files:**
- `src/storage/__init__.py` — Added exports for abstract protocols and updated `__all__`
- `src/storage/workflow_json_storage.py` — No code changes (already compliant with WorkflowRunRepository protocol)
- `src/storage/workflow_attempt_json_storage.py` — No code changes (already compliant with WorkflowAttemptRepository protocol)
- `src/services/workflow_run_service.py` — Constructor now accepts abstract `WorkflowRunRepository` instead of concrete `WorkflowJsonStorage`
- `src/services/workflow_attempt_service.py` — Constructor now accepts abstract `WorkflowAttemptRepository` instead of concrete `WorkflowAttemptJsonStorage`
- `src/services/github_integration_service.py` — Completely refactored to compose four adapter classes; backward-compatible deprecated private methods provided
- `src/services/__init__.py` — Updated `__all__` with new adapter exports
- `artifacts/class_diagram.puml` — Updated to show abstract storage layer, new GitHub adapter classes, and refactored service relationships
- `artifacts/component_diagram.puml` — Updated to show GitHub adapter component, abstract storage layer, and acyclic dependency graph
- `artifacts/sequence_github_integration.puml` — Updated to reflect delegation to new adapter classes

### Test Result
✓ **604 tests passed** (1.19s)

All tests pass including:
- 90 new adapter tests (18 GitHubTokenResolver + 11 GitHubApiClient + 13 GitHubCliAdapter + 46 GitHubToWorkflowConverter + 2 integration)
- 514 pre-existing tests (maintained backward compatibility; no test modifications required)

### Implementation Details

**Must Have (All Completed):**
- ✓ Separated Service layer from Storage layer via abstract repository protocols
- ✓ Extracted GitHub adapter layer with four focused classes:
  - `GitHubTokenResolver` — Handles token resolution (env → secrets file → prompt) and validation
  - `GitHubApiClient` — Pure REST API client for GitHub
  - `GitHubCliAdapter` — Wraps `gh` CLI commands via subprocess
  - `GitHubToWorkflowConverter` — Transforms GitHub API responses to domain models
- ✓ Ensured no circular dependencies (acyclic dependency graph verified)
- ✓ Services depend on abstract repositories, not concrete implementations

**Should Have (All Completed):**
- ✓ Preserved ALL existing public interfaces (method signatures, class names, return types unchanged)
- ✓ Introduced abstract base classes and protocols for storage (`WorkflowRunRepository`, `WorkflowAttemptRepository`)
- ✓ Introduced abstract protocols for GitHub adapter components

**Could Have (Completed):**
- ✓ Module-level `__all__` declarations added to `src/storage/__init__.py` and `src/services/__init__.py`

**Won't Have (Not Applicable):**
- Full rewrite of domain logic — only refactored for separation of concerns

**Architecture Improvements:**

1. **Abstract Storage Layer** — Services now depend on protocols, not concrete storage implementations:
   - `WorkflowRunRepository` protocol defines save/load contract
   - `WorkflowAttemptRepository` protocol defines save/load contract
   - Concrete implementations (`WorkflowJsonStorage`, `WorkflowAttemptJsonStorage`) implement protocols
   - Enables testing with mock storage and future database backends

2. **Separated GitHub Adapter Layer** — Four focused classes extracted from monolithic 500+ line service:
   - **Token Management** (`GitHubTokenResolver`) — Resolves tokens from env, secrets file, or user prompt; validates via API/CLI
   - **REST API Client** (`GitHubApiClient`) — Pure HTTP client; no domain coupling; testable with mocks
   - **CLI Adapter** (`GitHubCliAdapter`) — Wraps `gh` CLI commands; subprocess isolation; independent of API client
   - **Data Conversion** (`GitHubToWorkflowConverter`) — Transforms GitHub API JSON to WorkflowRun/WorkflowRunAttempt domain models
   - Each concern is independently testable and reusable

3. **Maintained Backward Compatibility** — All existing tests pass without modification:
   - All public method signatures unchanged
   - All class names and import paths unchanged
   - Deprecated private methods still available (marked with DEPRECATED comments) for gradual migration
   - Existing code imports continue to work

4. **Acyclic Dependency Graph** — Verified clean layering:
   - Models layer → no dependencies
   - Storage/Base → Models
   - Storage/Implementations → Models + Storage/Base
   - Adapters/GitHub → Models
   - Services → Models + Storage/Base + Adapters
   - No circular imports

5. **Clear Module Organization:**
   - `src/storage/` — Persistence layer with abstract protocols and concrete implementations
   - `src/adapters/` — External system integration (currently GitHub)
   - `src/adapters/github/` — GitHub-specific adapter classes
   - `src/services/` — Business logic layer (public APIs unchanged)

**Test Coverage:**
- **GitHubTokenResolver** (18 tests) — Environment variables, secrets files, prompts, validation in API/CLI modes
- **GitHubApiClient** (11 tests) — Successful fetches, parameter handling, HTTP error conditions, JSON parsing
- **GitHubCliAdapter** (13 tests) — Command execution, JSON parsing, timeouts, missing CLI, process errors
- **GitHubToWorkflowConverter** (46 tests) — Field mapping (camelCase/snake_case), timestamp parsing, duration calculation, enum validation
- **Integration** (2 tests) — End-to-end adapter composition

Duration: PENDING | Cost: PENDING | Turns: PENDING
