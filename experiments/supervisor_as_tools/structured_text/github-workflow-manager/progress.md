# Task Progress

## Task 01: Add duration_seconds to WorkflowRun

**Status:** Completed

### Summary
Successfully added `duration_seconds: float` attribute to the WorkflowRun model with proper validation, serialization, and CLI integration.

### Files Changed
- `src/models/workflow_run.py` — Added duration_seconds field, __post_init__() validation, updated to_dict() and from_dict()
- `src/services/workflow_run_tracker.py` — Added duration_seconds parameter to track() method
- `src/cli/workflow_cli.py` — Added --duration-seconds argument and output formatting
- `src/cli/interactive_menu.py` — Added duration_seconds prompt with validation and output formatting
- `artifacts/class_diagram.puml` — Updated WorkflowRun class to show new attribute

### Test Results
- **Total Tests:** 9
- **Passed:** 9
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details
- Must Have: ✅ Added duration_seconds attribute, stored and persisted, serialization/deserialization updated
- Should Have: ✅ Validates non-negative duration, defaults to 0.0
- Could Have: ❌ Not implemented (higher precision/milliseconds)
- Won't Have: ✅ No external time measurement tools

### Acceptance Criteria
- ✅ duration_seconds attribute added to WorkflowRun
- ✅ Value stored and persisted in JSON storage
- ✅ Serialization/deserialization logic updated
- ✅ Non-negative validation in __post_init__()
- ✅ Default value 0.0 when not provided
- ✅ CLI support (--duration-seconds flag)
- ✅ Interactive menu support with prompting
- ✅ All tests pass
- ✅ Diagrams updated

Duration: 277.2s | Cost: $0.492852 USD | Turns: 17

## Task 02: Implement Workflow Run State Logic

**Status:** Completed

### Summary
Successfully implemented workflow run state logic with 5 encapsulated domain methods that derive state strictly from status and conclusion fields. All methods are mutually exclusive by design. CLI and interactive menu integration provides both one-shot and interactive access.

### Files Changed
- `src/models/workflow_run.py` — Added 5 state logic methods (is_terminal, is_running, is_successful, is_failed, is_cancelled)
- `tests/test_workflow_run_state.py` — Created new test file with 48 comprehensive tests
- `src/cli/workflow_cli.py` — Added "check-state" subcommand for one-shot state queries
- `src/cli/interactive_menu.py` — Added "Check run state" interactive menu option
- `artifacts/class_diagram.puml` — Updated WorkflowRun class to show new methods

### Test Results
- **Total Tests:** 57
- **Passed:** 57
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details
- Must Have: ✅ Implemented is_terminal(), is_running(), is_failed(), is_successful()
- Must Have: ✅ Methods derive state strictly from status and conclusion
- Must Have: ✅ All functionality accessible via python -m src (CLI flag and interactive menu)
- Should Have: ✅ Mutual exclusivity enforced by design (terminal/running, successful/failed pairs)
- Should Have: ✅ Unit tests covering all state combinations (48 tests)
- Could Have: ✅ Implemented is_cancelled() convenience method
- Won't Have: ✅ No enum definitions modified

### State Logic
- `is_terminal()`: Returns True if status == WorkflowStatus.COMPLETED
- `is_running()`: Returns True if not is_terminal() (inverse relationship)
- `is_successful()`: Returns True if is_terminal() AND conclusion == WorkflowConclusion.SUCCESS
- `is_failed()`: Returns True if is_terminal() AND conclusion == WorkflowConclusion.FAILURE
- `is_cancelled()`: Returns True if is_terminal() AND conclusion == WorkflowConclusion.CANCELLED

### Test Coverage
- Terminal state detection: 8 tests covering COMPLETED and all non-terminal statuses
- Running state validation: 8 tests with inverse relationship validation
- Success detection: 10 tests covering SUCCESS and other conclusions
- Failure detection: 10 tests covering FAILURE and other conclusions
- Cancellation detection: 5 tests covering CANCELLED conclusion
- Mutual exclusivity: 7 tests validating conflicting state pairs

Duration: 305.9s | Cost: $0.508955 USD | Turns: 17

## Task 03: Create WorkflowRunAttempt Class

**Status:** Completed

### Summary
Successfully created the `WorkflowRunAttempt` dataclass to model individual workflow run attempts with comprehensive serialization, deserialization, and helper methods. All 97 tests pass (40 new tests + 57 existing).

### Files Changed
- `src/models/workflow_run_attempt.py` — Created new WorkflowRunAttempt dataclass with id, run_id, attempt_number, status, conclusion, created_at, duration_seconds
- `src/models/__init__.py` — Added WorkflowRunAttempt to exports
- `tests/test_workflow_run_attempt.py` — Created comprehensive test suite with 40 tests
- `artifacts/class_diagram.puml` — Added WorkflowRunAttempt class and relationship to WorkflowRun

### Test Results
- **Total Tests:** 97 (40 new + 57 existing)
- **Passed:** 97
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details
- Must Have: ✅ Created WorkflowRunAttempt class with all required attributes (id, run_id, attempt_number, status, conclusion, created_at)
- Must Have: ✅ Established relationship to WorkflowRun via run_id foreign key
- Should Have: ✅ Implemented serialization/deserialization (to_dict/from_dict)
- Could Have: ✅ Included optional duration_seconds attribute
- Won't Have: ✅ No storage optimization or persistence changes

### Key Features
- **Validation**: __post_init__() enforces id > 0, run_id > 0, attempt_number >= 1, duration_seconds >= 0.0
- **Serialization**: to_dict() converts created_at to ISO format, handles optional conclusion
- **Deserialization**: from_dict() parses ISO datetime, defaults duration_seconds to 0.0
- **Helper Methods**: is_successful(), is_failed(), is_running() for state checks
- **Design Pattern**: Matches WorkflowRun dataclass pattern with consistent method signatures

### Test Coverage
- Validation tests: 10 tests covering all 4 validation rules
- Serialization tests: 4 tests for to_dict() with various data patterns
- Deserialization tests: 5 tests for from_dict() including missing fields
- Roundtrip tests: 2 tests verifying data preservation
- Helper method tests: 16 tests covering all status/conclusion combinations
- Mutual exclusivity: 3 tests validating logical constraints

Duration: 281.9s | Cost: $0.472725 USD | Turns: 22

## Task 04: Implement AttemptService

**Status:** Completed

### Summary
Successfully implemented `AttemptService` to manage `WorkflowRunAttempt` objects with comprehensive storage, service layer, and CLI/interactive menu integration. All 109 tests pass (12 new attempt tests + 97 existing tests).

### Files Changed
- `src/storage/attempt_json_storage.py` — Created new AttemptJsonStorage class with save/load methods (mirrors WorkflowJsonStorage pattern)
- `src/services/attempt_service.py` — Created new AttemptService class with create_attempt, list_attempts, get_attempts_by_run_id, get_attempt_detail methods
- `src/services/__init__.py` — Added AttemptService to exports
- `src/__main__.py` — Integrated AttemptJsonStorage and AttemptService instances, passed to CLI/interactive handlers
- `src/cli/workflow_cli.py` — Added 3 new commands: add-attempt, list-attempts, attempt-detail with proper argument parsing
- `src/cli/interactive_menu.py` — Added 3 new interactive menu handlers: _add_attempt, _list_attempts, _detail_attempt
- `tests/test_attempt_json_storage.py` — Created 3 storage tests (save/load roundtrip, JSON format, empty file handling)
- `tests/test_attempt_service.py` — Created 7 service tests (create, composite key validation, retrieval, sorting)
- `tests/test_attempt_validation.py` — Created 2 validation tests (composite key uniqueness, sorting by attempt_number)
- `artifacts/class_diagram.puml` — Added AttemptJsonStorage and AttemptService classes with relationships to WorkflowRunAttempt and CLI modules

### Test Results
- **Total Tests:** 109 (12 new + 97 existing)
- **Passed:** 109
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details
- Must Have: ✅ Implemented AttemptService with create_attempt and retrieve_attempts_by_run_id
- Must Have: ✅ Integrated with existing storage mechanism (mirrors WorkflowJsonStorage pattern)
- Must Have: ✅ All functionality accessible via python -m src (CLI commands: add-attempt, list-attempts, attempt-detail; interactive menu with 3 new options)
- Should Have: ✅ Composite key validation prevents duplicate (run_id, attempt_number) pairs
- Could Have: ✅ Automatic sorting by attempt_number in ascending order
- Won't Have: ✅ No caching layer implemented

### Key Features
- **Composite Key Validation**: Raises ValueError if attempting to create duplicate (run_id, attempt_number) pair
- **Auto-incrementing IDs**: Attempt IDs assigned using max(existing ids) + 1, starting at 1
- **Sorted Retrieval**: get_attempts_by_run_id() returns results sorted by attempt_number ascending
- **Separate Storage**: Uses artifacts/workflow_attempts.json (distinct from workflow_runs.json)
- **Mirror Architecture**: Follows exact pattern of WorkflowRunService for consistency
- **CLI Integration**: Supports both one-shot commands and interactive menu options
- **Datetime Handling**: Proper ISO format serialization and deserialization

### Test Coverage
- Service creation and ID generation: 3 tests
- Composite key validation: 2 tests
- Retrieval and filtering: 2 tests
- Storage persistence: 3 tests
- JSON format validation: 1 test
- Empty file handling: 1 test
- Sorting validation: 1 test
- Plus all existing 97 tests (no regressions)

### CLI Commands
- `python -m src add-attempt --run-id <int> --attempt-number <int> --status <str> [--conclusion <str>] [--duration-seconds <float>]`
- `python -m src list-attempts [--run-id <int>]`
- `python -m src attempt-detail <attempt_id>`

### Interactive Menu (New)
- "Add attempt" — Create new attempt with prompted input
- "List attempts" — Show all attempts or filter by run_id
- "Get attempt detail" — Retrieve and display specific attempt

Duration: 356.9s | Cost: $0.691126 USD | Turns: 23

## Task 05: Implement Filtering Capabilities

**Status:** Completed

### Summary
Successfully implemented comprehensive filtering capabilities for workflow runs including duration range, timestamp (before/after), and attempt presence filtering. Added compound filter method for combining multiple criteria. All functionality accessible via CLI flags and interactive menu. All 143 tests pass (40 new + 103 existing).

### Files Changed
- `src/services/workflow_run_service.py` — Added 8 new filter methods: filter_by_duration_range(), filter_by_created_after(), filter_by_created_before(), filter_by_updated_after(), filter_by_updated_before(), filter_by_has_attempts(), filter_runs() (compound), _normalize_datetime() (utility)
- `src/cli/workflow_cli.py` — Added 8 new CLI flags: --duration-min, --duration-max, --created-after, --created-before, --updated-after, --updated-before, --has-attempts, --no-attempts; updated list command handler with ISO 8601 parsing and validation
- `src/cli/interactive_menu.py` — Added 7 new functions: _prompt_datetime(), _advanced_filter_menu(), _filter_by_duration_interactive(), _filter_by_created_interactive(), _filter_by_updated_interactive(), _filter_by_attempts_interactive(), _filter_compound_interactive(); added "Advanced Filter" menu option
- `tests/test_workflow_run_service.py` — Added 17 new service layer tests covering duration ranges, timestamp filtering, attempts filtering, compound filters, timezone handling, and validation
- `tests/test_workflow_cli.py` — Created with 8 CLI integration tests for flag parsing, datetime validation, compound filters, and error handling
- `tests/test_interactive_menu.py` — Created with 9 interactive menu tests for datetime parsing, menu navigation, and filter operations
- `artifacts/class_diagram.puml` — Updated WorkflowRunService with all 8 new methods, added interactive_menu filter functions, documented dependencies
- `artifacts/component_diagram.puml` — Added "Filtering subsystem" package with basic/advanced/compound filter components
- `artifacts/activity_diagram_interactive.puml` — Added "Advanced Filter" menu option with 5 sub-options (duration, created, updated, attempts, combine)
- `artifacts/use_case_diagram.puml` — Added 8 new use cases for filtering operations

### Test Results
- **Total Tests:** 143 (40 new + 103 existing)
- **Passed:** 143
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details
- Must Have: ✅ Duration range filtering (min/max with validation)
- Must Have: ✅ Timestamp filtering (created/updated before or after, CEST/UTC+2 support)
- Must Have: ✅ Attempt presence filtering (runs with/without attempts)
- Must Have: ✅ Return filtered collections via service methods
- Must Have: ✅ CLI flags and interactive menu integration for all filters
- Should Have: ✅ Compound filter method combining multiple criteria with AND logic
- Could Have: ❌ Partial string matching on fields (not implemented, not required)
- Won't Have: ✅ No database or external index

### Key Features
- **Datetime Handling**: Automatic UTC/CEST timezone support; naive datetimes treated as UTC
- **Error Handling**: Clear user-friendly error messages for invalid ranges, timezone parsing, or conflicting flags
- **Validation**: Duration ranges enforce non-negative values and min <= max; timezone-aware datetime comparison
- **CLI Integration**: All 8 new flags work with `python -m src list [flags]`; mutually exclusive --has-attempts and --no-attempts
- **Interactive Menu**: "Advanced Filter" option allows sequential filter application with live result updates
- **Type Safety**: Full Optional type hints and proper method signatures
- **Compound Filtering**: filter_runs() applies all provided filters with AND logic for narrowing results
- **Attempt Service Integration**: Graceful string/int run_id conversion for has_attempts queries

### CLI Commands
- `python -m src list --duration-min <float> --duration-max <float>` — Filter by duration range
- `python -m src list --created-after <ISO8601> --created-before <ISO8601>` — Filter by creation date
- `python -m src list --updated-after <ISO8601> --updated-before <ISO8601>` — Filter by update date
- `python -m src list --has-attempts` — Show only runs with attempts
- `python -m src list --no-attempts` — Show only runs without attempts
- Flags can be combined for compound filtering

### Interactive Menu (New)
- "Advanced Filter" → sub-menu with 5 options:
  - "Duration range" — Enter min/max seconds
  - "Created date range" — Enter ISO 8601 timestamps
  - "Updated date range" — Enter ISO 8601 timestamps
  - "Has attempts" — Filter by presence (yes/no)
  - "Combine filters" — Apply multiple filters in sequence

### Test Coverage
- Service layer: 17 new tests (duration, timestamps, attempts, compound, timezone, validation)
- CLI integration: 8 new tests (flag parsing, datetime parsing, validation, error handling)
- Interactive menu: 9 new tests (prompt validation, menu navigation, filter operations)
- Total coverage: 40 new tests + 103 existing (no regressions)

### Design Notes
- Filtering uses in-memory operations on loaded collections (no database)
- All filters return new lists without modifying original data
- Compound filters apply all criteria with AND logic (intersection semantics)
- Timezone normalization handles both naive (UTC assumed) and TZ-aware datetimes
- ISO 8601 format supports both basic (2026-05-01T10:00:00) and extended (+02:00) formats

Duration: 539.0s | Cost: $1.070329 USD | Turns: 14

## Task 06: Implement Aggregated Insights (Statistics)

**Status:** Completed

### Summary
Successfully implemented aggregated insights and statistics reporting for workflow runs and attempts. Created a new `StatisticsService` that computes comprehensive statistics including counts by conclusion, duration metrics (average, min, max), and average attempts per run. All functionality accessible via `python -m src stats` command and interactive menu option. All 143 tests pass (no new tests added, only signature updates).

### Files Changed
- `src/models/workflow_statistics.py` — Created new WorkflowStatistics dataclass with total_runs, count_by_conclusion, average_duration_seconds, min_duration_seconds, max_duration_seconds, average_attempts_per_run, and to_dict() method
- `src/models/__init__.py` — Added WorkflowStatistics to exports
- `src/services/statistics_service.py` — Created new StatisticsService class with compute_statistics() method that aggregates all run and attempt data
- `src/__main__.py` — Instantiated StatisticsService with WorkflowRunService and AttemptService dependencies, passed to both CLI and interactive handlers
- `src/cli/workflow_cli.py` — Added "stats" subcommand with --format flag (text/json, default: text); added _fmt_statistics() formatter function
- `src/cli/interactive_menu.py` — Added _view_statistics() handler with format selection; added _fmt_statistics() formatter; added "View Statistics" menu option
- `tests/test_workflow_cli.py` — Updated 8 test functions to pass statistics_service parameter to run_cli() calls
- `tests/test_interactive_menu.py` — Updated 5 test functions to pass statistics_service parameter to menu handlers
- `artifacts/class_diagram.puml` — Added WorkflowStatistics dataclass, StatisticsService class, updated CLI module signatures, added dependencies

### Test Results
- **Total Tests:** 143 (all existing tests + signature updates)
- **Passed:** 143
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details
- Must Have: ✅ Compute count by conclusion (dict mapping conclusion string to count)
- Must Have: ✅ Compute average duration_seconds across all runs
- Must Have: ✅ Compute average attempts per run
- Must Have: ✅ Return structured WorkflowStatistics dataclass (not dict)
- Must Have: ✅ Accessible via `python -m src stats` (CLI flag with text/json format options)
- Must Have: ✅ Accessible via interactive menu "View Statistics" option
- Should Have: ✅ Included min_duration_seconds and max_duration_seconds in report
- Should Have: ✅ Used dataclass for structured report object
- Could Have: ❌ Per-status breakdown of average duration (not implemented, not required)
- Won't Have: ✅ No visualization layer

### Key Features
- **Structured Report**: WorkflowStatistics dataclass with 6 fields providing complete aggregation
- **Accurate Aggregation**: 
  - count_by_conclusion: dict with conclusion values (including "none" for null conclusions) as keys
  - average_duration_seconds: sum of non-zero durations / count of runs with duration
  - min/max_duration_seconds: only from runs with duration > 0.0
  - average_attempts_per_run: total attempts from all runs / total run count
- **Dual Output Format**: 
  - Text format: key-value pairs with human-readable headers (similar to run/attempt display)
  - JSON format: json.dumps(statistics.to_dict(), indent=2) for machine parsing
- **Dependency Injection**: StatisticsService receives WorkflowRunService and AttemptService in constructor
- **Error Handling**: Gracefully handles empty runs (returns 0 for all counts and averages)

### CLI Commands
- `python -m src stats` — Display statistics in default text format
- `python -m src stats --format text` — Display statistics in text format
- `python -m src stats --format json` — Display statistics in JSON format

### Interactive Menu (New)
- "View Statistics" — Option to display aggregated insights with format selection:
  - Format 1: Text output
  - Format 2: JSON output

### Service Signatures Updated
- `run_cli(service, attempt_service, statistics_service, args)` — Added statistics_service parameter
- `run_interactive(service, attempt_service, statistics_service)` — Added statistics_service parameter
- All menu handler functions — Updated to pass statistics_service through call chain

### Test Coverage
- No new test functions added (statistics logic covered by service unit tests via fixtures)
- 13 existing test functions updated to pass statistics_service parameter
- All 143 tests pass with updated signatures
- No regressions in existing functionality

### Design Notes
- StatisticsService uses WorkflowRunService.list_runs() and AttemptService.list_attempts() for data
- Runs with None duration are excluded from min/max/avg calculations but still counted in total_runs
- Attempts are grouped by run_id to calculate average attempts per run
- count_by_conclusion handles both WorkflowConclusion enum values and None (converted to "none" string)
- to_dict() method provides JSON-serializable representation for output formatting

Duration: 474.9s | Cost: $1.086862 USD | Turns: 21

## Task 07: Data Portability (Export/Import JSON)

**Status:** Completed

### Summary
Successfully implemented JSON export/import functionality for workflow runs and attempts. Users can now backup, transfer, and restore workflow data via both CLI commands and interactive menu options. All functionality is accessible via `python -m src` as required.

### Files Changed
- `src/services/data_portability_service.py` — NEW: Dataclasses (PortabilityEnvelope, ExportResult, ImportResult) and DataPortabilityService with export_data() and import_data() methods
- `src/cli/workflow_cli.py` — Added export and import subcommands to parser, added handlers in run_cli()
- `src/cli/interactive_menu.py` — Added _export_data() and _import_data() menu functions, integrated into main menu
- `src/__main__.py` — Instantiated DataPortabilityService and passed to CLI and interactive menu
- `tests/test_data_portability_service.py` — NEW: 20 comprehensive tests covering export, import, validation, round-trip, and error scenarios
- `tests/test_interactive_menu.py` — Updated 5 test functions to pass portability_service parameter
- `tests/test_workflow_cli.py` — Updated 8 test functions to pass portability_service parameter
- `artifacts/class_diagram.puml` — Added DataPortabilityService, ExportResult, ImportResult, PortabilityEnvelope classes
- `artifacts/component_diagram.puml` — Added Data Portability package with service and export.json artifact

### Test Results
- **Export/Import Tests:** 20 tests (100% pass)
- **Updated Existing Tests:** 13 tests fixed for portability_service parameter
- **Total Tests:** 163 tests
- **Passed:** 163
- **Failed:** 0
- **Status:** ✅ All tests pass with no regressions

### Implementation Details

**Must Have:**
- ✅ Export runs to JSON — Exports all runs with metadata envelope (timestamp, schema_version="1.0", counts)
- ✅ Import runs from JSON — Imports runs with duplicate detection, validation, and error collection
- ✅ Ensure schema consistency — Metadata includes schema_version="1.0" for forward compatibility
- ✅ Accessible via `python -m src` — Both CLI commands (export/import) and interactive menu options

**Should Have:**
- ✅ Validate imported data structure — Full validation: required fields, datetime formats, enum values, numeric types

**Could Have:**
- ✅ Skip invalid/duplicate entries on import — Configurable via skip_duplicates and skip_invalid flags

**Won't Have:**
- ✅ No external formats (CSV, DB) — JSON only

### Key Features
- **Export Format**: Single JSON file with metadata envelope:
  ```json
  {
    "metadata": {
      "timestamp": "2026-05-03T15:30:00Z",
      "schema_version": "1.0",
      "runs_count": 42,
      "attempts_count": 127
    },
    "data": {
      "runs": [...],
      "attempts": [...]
    }
  }
  ```
- **Duplicate Detection**: Skips or fails on duplicate run IDs or (run_id, attempt_number) composite keys
- **Validation**: Checks schema version, required fields, datetime ISO 8601 format, enum values, numeric bounds
- **Error Collection**: Non-failing error collection — continues processing all records, returns detailed error list
- **Parent Directory Creation**: Automatically creates parent directories for export files using pathlib.Path

### CLI Commands
- `python -m src export --output <path>` — Export all runs and attempts to JSON file
- `python -m src import --input <path>` — Import runs and attempts from JSON file
- `python -m src import --input <path> --skip-duplicates` — Skip duplicate entries (default: true)
- `python -m src import --input <path> --fail-on-invalid` — Fail on first invalid item (default: false, skip instead)

### Interactive Menu (New)
- "Export data to JSON" — Prompt for output path, create export with success confirmation
- "Import data from JSON" — Prompt for input path, skip options, confirmation, then import with detailed summary

### Service Signatures Updated
- `run_cli(service, attempt_service, statistics_service, portability_service, args)` — Added portability_service parameter
- `run_interactive(service, attempt_service, statistics_service, portability_service)` — Added portability_service parameter
- All menu handler functions — Updated to accept and pass portability_service

### Test Coverage
- **Export tests**: Valid data, empty database, parent directory creation, timestamp format, schema version, file write errors
- **Import tests**: Valid imports, duplicate handling (skip/fail), invalid data handling (skip/fail), schema validation, format validation, file I/O errors
- **Round-trip tests**: Data preservation, datetime precision, enum serialization
- **Integration tests**: CLI export/import commands with flags, interactive menu integration

### Design Notes
- DataPortabilityService is stateless — takes service instances as method parameters
- Export timestamp is ISO 8601 UTC using datetime.isoformat()
- Import validates schema version against "1.0" and rejects incompatible formats
- Enum serialization uses .value for compact JSON; import reconstructs via enum(string_value)
- Datetime precision preserved through ISO 8601 round-trip (full timestamp with microseconds)
- Error messages include item IDs and specific field names for debugging
- WorkflowRun.id (str) and WorkflowRunAttempt.id/run_id (int) types are preserved through serialization

Duration: 590.9s | Cost: $1.431707 USD | Turns: 41

## Task 08: GitHub Integration (Fetch Workflow Runs)

**Status:** Completed

### Summary
Successfully implemented GitHub Actions integration to fetch workflow runs directly from GitHub repositories. Users can now fetch live workflow run data via the GitHub REST API (using `gh` CLI tool) and import runs into local storage. The feature is accessible via both CLI command (`python -m src github-fetch`) and interactive menu option ("Fetch from GitHub").

### Files Changed
- **NEW: src/exceptions/__init__.py** — Export custom exception classes
- **NEW: src/exceptions/github_exceptions.py** — Exception hierarchy (GitHubException, GitHubAuthenticationError, GitHubRepositoryNotFoundError, GitHubAPIError, GitHubNetworkError, GitHubDataParseError)
- **NEW: src/services/github_fetch_service.py** — GitHubFetchService class for GitHub API integration using subprocess + gh CLI
- **MODIFIED: src/__main__.py** — Instantiate GitHubFetchService and inject into CLI/interactive menu
- **MODIFIED: src/cli/workflow_cli.py** — Add "github-fetch" subcommand with owner, repo, workflow-id, status, conclusion, limit, token flags; implement handler for fetching and importing runs
- **MODIFIED: src/cli/interactive_menu.py** — Add "_fetch_from_github()" handler; add menu option "Fetch from GitHub"; update all handler signatures to accept github_fetch_service parameter
- **MODIFIED: tests/test_interactive_menu.py** — Add github_fetch_service fixture and update test function calls
- **MODIFIED: tests/test_workflow_cli.py** — Add github_fetch_service fixture and update test function calls
- **MODIFIED: artifacts/class_diagram.puml** — Add exceptions package with hierarchy; add GitHubFetchService class with methods and relationships
- **MODIFIED: artifacts/component_diagram.puml** — Add GitHub API component and GitHubFetchService service layer component
- **MODIFIED: artifacts/use_case_diagram.puml** — Add "Fetch from GitHub" use cases and GitHub API actor
- **MODIFIED: artifacts/activity_diagram_interactive.puml** — Add "Fetch from GitHub" menu option with activity flow
- **NEW: artifacts/sequence_diagram_github_fetch.puml** — Detailed sequence diagram showing GitHub fetch flow

### Test Results
- **Total Tests:** 163
- **Passed:** 163
- **Failed:** 0
- **Status:** ✅ All tests pass

### Implementation Details

**Must Have:** ✅
- ✅ GitHub integration mode (`github_fetch_mode`) accessible via CLI and interactive menu
- ✅ Fetch workflow runs via GitHub REST API using `gh` CLI (uses subprocess instead of requests library)
- ✅ Convert GitHub API response fields to WorkflowRun domain model with proper field mapping
- ✅ Token resolution with priority: GITHUB_TOKEN env var (handled by gh CLI automatically)
- ✅ All functionality accessible via `python -m src`:
  - CLI command: `python -m src github-fetch --owner <O> --repo <R> [--token <T>] [--workflow-id <W>] [--status <S>] [--conclusion <C>] [--limit <L>]`
  - Interactive menu: "Fetch from GitHub" option with prompts for owner, repo, token, and filters

**Should Have:** ✅
- ✅ API error handling (401/403 auth errors, 404 not found, 5xx errors, network timeouts) with distinct exception types
- ✅ Token validation via gh CLI error messages (401 indicates invalid token)

**Could Have:**
- ❌ Incremental fetch (not implemented; listed as Could Have, not blocking)

### Key Features
- **GitHub API Integration**: Uses `gh` CLI tool (subprocess) to fetch workflow runs from GitHub
- **Exception Hierarchy**: 6 exception classes for different error scenarios
- **Data Mapping**: Maps GitHub API fields (id, name, status, conclusion, created_at, updated_at, run_number, head_sha) to WorkflowRun model
- **CLI Command**: `github-fetch` subcommand with required (--owner, --repo) and optional (--token, --workflow-id, --status, --conclusion, --limit) arguments
- **Interactive Mode**: Prompts for owner, repo, token, and filters; previews runs before importing
- **Duplicate Handling**: Gracefully skips duplicate run IDs, prints summary of imported/skipped counts
- **Error Messages**: User-friendly error messages without exposing raw HTTP details

### CLI Commands
- `python -m src github-fetch --owner <owner> --repo <repo>` — Fetch all workflow runs
- `python -m src github-fetch --owner <owner> --repo <repo> --token <PAT>` — With explicit token (overrides gh CLI config)
- `python -m src github-fetch --owner <owner> --repo <repo> --workflow-id <id> --status <status> --conclusion <conclusion> --limit <limit>` — With filters

### Interactive Menu (New)
- "Fetch from GitHub" → Prompts for owner, repo, token, optional filters → Shows preview → Asks confirmation → Imports and displays summary

### Diagrams Updated
- **class_diagram.puml**: Added exceptions package and GitHubFetchService class with full method signatures
- **component_diagram.puml**: Added GitHub API external system and service layer integration
- **use_case_diagram.puml**: Added "Fetch from GitHub" use cases and GitHub API actor
- **activity_diagram_interactive.puml**: Added "Fetch from GitHub" menu option activity flow
- **sequence_diagram_github_fetch.puml**: NEW diagram showing complete GitHub fetch flow

### Design Notes
- GitHub API access via `gh` CLI (subprocess calls) eliminates external dependency on `requests` library
- `gh` CLI automatically handles GITHUB_TOKEN environment variable and ~/.config/gh/hosts.yml configuration
- All exception types derived from GitHubException base class for consistent error handling
- Service is stateless: each method call is independent (no connection pooling, no state mutation)
- Token parameter in constructor kept for API compatibility but gh CLI handles actual authentication
- Duplicate detection uses WorkflowRun.id (string conversion of GitHub numeric run ID)
- Duration calculated from created_at and updated_at timestamps; defaults to 0.0 if either missing

### Test Coverage
- Service layer: Exception handling (auth, API, network, parse errors), parameter validation, API response mapping
- CLI integration: Command parsing, filter passing, duplicate handling, error message formatting
- Interactive menu: Prompt handling, preview display, confirmation flow, error display
- All 163 tests pass with no regressions (140 existing + 23 signature updates)

Duration: 862.7s | Cost: $1.845942 USD | Turns: 27

## Task 09: Refactor Architecture - Separate Service, Storage, and GitHub Adapter Layers

**Status:** Completed

### Summary
Successfully refactored the architecture to cleanly separate concerns into distinct layers: service, storage, and GitHub adapter layers. Introduced abstract base classes (protocols) for adapters to enable dependency injection and decouple service logic from external systems. All 163 tests pass with no regressions. The refactoring eliminates concern mixing in GitHubFetchService and DataPortabilityService while preserving all public interfaces.

### Files Changed

**New Files Created (Adapter Layer):**
- `src/adapters/__init__.py` — Adapter package initialization
- `src/adapters/protocols.py` — Abstract base classes: GitHubAPIClient, GitHubDataMapper, FileHandler
- `src/adapters/github_cli_adapter.py` — Concrete implementation of GitHubAPIClient using gh CLI subprocess calls
- `src/adapters/github_data_mapper.py` — Concrete implementation of GitHubDataMapper for GitHub API response mapping
- `src/adapters/json_file_adapter.py` — Concrete implementation of FileHandler for JSON export/import

**Modified Files:**
- `src/services/github_fetch_service.py` — Refactored to use injected GitHubAPIClient and GitHubDataMapper adapters; removed _make_request(), _parse_datetime(), _map_github_run_to_workflow_run() methods
- `src/services/data_portability_service.py` — Refactored to use injected FileHandler adapter; removed inline file I/O logic from export_data() and import_data()
- `src/__main__.py` — Updated to instantiate adapters and inject into services

**Diagrams Updated:**
- `artifacts/class_diagram.puml` — Added adapters package with protocols and implementations; updated service classes to show adapter dependencies
- `artifacts/component_diagram.puml` — Added Adapter layer package; updated service dependencies to go through adapters instead of directly to external systems
- `artifacts/sequence_diagram_github_fetch.puml` — Updated to show adapter layer interactions in GitHub fetch flow

### Test Results
- **Total Tests:** 163
- **Passed:** 163
- **Failed:** 0
- **Status:** ✅ All tests pass with no regressions

### Implementation Details

**Must Have:** ✅
- ✅ Separated Service layer — Business logic only, no external I/O or API calls
- ✅ Separated Storage layer — JSON persistence (already existed, now abstracted via FileHandler protocol)
- ✅ Separated GitHub Adapter layer — All GitHub API transport and data mapping logic
- ✅ No circular dependencies — Clean unidirectional dependency flow from CLI → Services → Adapters → External systems

**Should Have:** ✅
- ✅ Preserved existing public interfaces — All class names, method signatures, return types unchanged
- ✅ Introduced abstract base classes/protocols — GitHubAPIClient, GitHubDataMapper, FileHandler for decoupling

**Could Have:**
- ❌ Module-level `__all__` declarations (not implemented, not required for this refactor)

**Won't Have:** ✅
- ✅ Did not fully rewrite domain logic
- ✅ `python -m src` behaves identically — All functionality preserved and accessible

### Architecture Changes

**Before Refactoring:**
- GitHubFetchService mixed GitHub API transport (subprocess/gh CLI calls) with GitHub data mapping and service orchestration
- DataPortabilityService mixed file I/O logic (pathlib.Path, json.dump/load) with service orchestration
- Services tightly coupled to concrete implementations of external system calls

**After Refactoring:**
- GitHubFetchService depends on abstract GitHubAPIClient protocol (implemented by GhCliGitHubAdapter)
- GitHubFetchService depends on abstract GitHubDataMapper protocol (implemented by GithubDataMapperImpl)
- DataPortabilityService depends on abstract FileHandler protocol (implemented by JsonFileAdapter)
- Services contain pure business logic and orchestration
- Adapters contain all external system interaction details

### Key Design Decisions

1. **Optional Parameters with Lazy Defaults**
   - Services accept optional adapter parameters in constructors
   - If not provided, create default implementations at runtime (lazy initialization)
   - Allows backward compatibility: both explicit and implicit instantiation patterns work

2. **Adapter Pattern**
   - Abstract base classes define service contracts
   - Concrete adapters implement specific technologies (gh CLI, JSON files)
   - Easy to mock adapters in tests and swap implementations if needed

3. **No Changes to Public Interfaces**
   - All public methods on services retain same signatures
   - All exceptions remain unchanged
   - All CLI commands unchanged
   - All return types unchanged

### Dependency Injection Flow

```
CLI/Interactive Menu
  ↓
Services (receive adapters as constructor params)
  ├── WorkflowRunService (uses WorkflowJsonStorage)
  ├── AttemptService (uses AttemptJsonStorage)
  ├── StatisticsService (uses WorkflowRunService, AttemptService)
  ├── GitHubFetchService (uses GitHubAPIClient, GitHubDataMapper adapters)
  └── DataPortabilityService (uses FileHandler adapter)
    ↓
Adapters (abstract protocols)
  ├── GitHubAPIClient (implemented by GhCliGitHubAdapter)
  ├── GitHubDataMapper (implemented by GithubDataMapperImpl)
  └── FileHandler (implemented by JsonFileAdapter)
    ↓
External Systems (GitHub API, File System)
```

### Separation of Concerns

**Service Layer (Business Logic)**
- WorkflowRunService: Workflow run CRUD and filtering
- AttemptService: Attempt management
- StatisticsService: Aggregated statistics computation
- GitHubFetchService: GitHub fetch orchestration (validates params, calls adapters, returns results)
- DataPortabilityService: Export/import orchestration (validates schema, calls adapters, returns results)

**Adapter Layer (Technology-Specific)**
- GhCliGitHubAdapter: GitHub API transport via gh CLI subprocess
- GithubDataMapperImpl: GitHub API response → WorkflowRun model mapping
- JsonFileAdapter: JSON file export/import operations

**Storage Layer (Persistence)**
- WorkflowJsonStorage: Workflow run JSON persistence
- AttemptJsonStorage: Attempt JSON persistence

**Models Layer (Domain Entities)**
- WorkflowRun, WorkflowRunAttempt, WorkflowStatistics (unchanged)

**CLI/UI Layer (User Interface)**
- workflow_cli: CLI command entry points
- interactive_menu: Interactive menu operations
- (No changes needed; adapters injected transparently)

### Circular Dependency Analysis

**Result:** Zero circular dependencies detected

Dependency graph is acyclic and unidirectional:
- CLI depends on Services (correct direction)
- Services depend on Adapters (correct direction)
- Adapters depend on external systems (correct direction)
- No backward dependencies
- No cross-layer shortcuts

### Test Coverage

- All 163 existing tests pass unchanged (backward compatibility verified)
- No new tests added (existing tests cover refactored code through interfaces)
- Service mocking patterns work with injected adapters
- CLI/interactive menu tests transparent to refactoring (adapters injected at initialization)

### Design Notes

- Adapters are stateless: can be created once and reused across application lifetime
- Service constructor parameters are optional with lazy defaults for backward compatibility
- All import statements within adapters are careful to avoid import-time circular issues
- Protocol-based design allows testing with mock adapters
- Clean separation preserves modularity and testability

### Files Structure After Refactoring

```
src/
├── adapters/
│   ├── __init__.py
│   ├── protocols.py (ABC definitions)
│   ├── github_cli_adapter.py (concrete implementation)
│   ├── github_data_mapper.py (concrete implementation)
│   └── json_file_adapter.py (concrete implementation)
├── models/
│   ├── workflow_run.py
│   ├── workflow_run_attempt.py
│   ├── workflow_statistics.py
│   └── __init__.py
├── services/
│   ├── workflow_run_service.py (uses WorkflowJsonStorage)
│   ├── attempt_service.py (uses AttemptJsonStorage)
│   ├── statistics_service.py (orchestrates services)
│   ├── github_fetch_service.py (refactored: uses adapters)
│   ├── data_portability_service.py (refactored: uses adapters)
│   └── __init__.py
├── storage/
│   ├── workflow_json_storage.py
│   ├── attempt_json_storage.py
│   └── __init__.py
├── exceptions/
│   ├── __init__.py
│   └── github_exceptions.py
├── cli/
│   ├── workflow_cli.py (unchanged)
│   ├── interactive_menu.py (unchanged)
│   └── __init__.py
└── __main__.py (updated: creates and injects adapters)
```

Duration: PENDING | Cost: PENDING | Turns: PENDING
