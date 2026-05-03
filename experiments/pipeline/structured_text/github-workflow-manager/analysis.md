# Task 05 - Filtering Capabilities for Workflow Runs: Analysis Report

## Task Summary

Implement advanced filtering capabilities for workflow runs and attempts. Users must be able to:

1. **Duration range filtering** — by min/max `duration_seconds`
2. **Timestamp filtering** — by `created_at`/`updated_at` before/after (CEST/UTC+2 timezone support)
3. **Attempts presence filtering** — runs with/without attempts
4. **Return filtered collections** (both CLI and interactive menu)
5. **Combine multiple filters** simultaneously
6. **Optional:** partial string matching on fields (e.g., workflow name, branch)

All functionality must be accessible via `python -m src` (interactive menu + CLI flags).

---

## Current Architecture Overview

### Three-Tier Layered Architecture

```
Application Entrypoint (__main__.py)
    ↓
Interface Layer (workflow_cli.py, interactive_menu.py)
    ├── CLI: argparse-driven one-shot commands
    └── Interactive: multi-step menu-driven interface
    ↓
Service Layer (WorkflowRunService, WorkflowAttemptService, Trackers)
    ├── WorkflowRunService — CRUD + existing filters
    ├── WorkflowAttemptService — CRUD + existing filters
    ├── WorkflowRunTracker — high-level run facade
    └── WorkflowAttemptTracker — high-level attempt facade
    ↓
Storage Layer (WorkflowJsonStorage, WorkflowAttemptJsonStorage)
    ├── JSON file persistence
    └── Load/save operations
    ↓
Domain Models (WorkflowRun, WorkflowRunAttempt, enums)
    ├── Dataclasses with serialization
    ├── State query methods
    └── Type-safe enums
```

### Artifacts Documentation

- **class_diagram.puml** — Full domain model with relationships
- **component_diagram.puml** — Layered architecture and dependencies
- **activity_diagram_main.puml** — CLI workflow and command flow
- **activity_diagram_interactive.puml** — Interactive menu navigation
- **use_case_diagram.puml** — User interactions (runs and attempts)

---

## Domain Model: Workflow Runs and Attempts

### WorkflowRun (src/models/workflow_run.py)

**Current Fields (10):**
- `id: str` — Unique identifier (UUID)
- `workflow_name: str` — Workflow name
- `branch: str` — Git branch name
- `status: WorkflowStatus` — Enum (queued, in_progress, completed, waiting, requested, pending)
- `conclusion: Optional[WorkflowConclusion]` — Enum or None (success, failure, cancelled, skipped, timed_out, action_required, neutral, stale)
- `created_at: datetime` — UTC creation timestamp (required)
- `updated_at: Optional[datetime]` — UTC update timestamp (can be None)
- `run_number: Optional[int]` — GitHub run number
- `commit_sha: Optional[str]` — Commit SHA
- `duration_seconds: float` — Duration in seconds (default 0.0, non-negative)

**Key Methods:**
- `to_dict()` / `from_dict()` — JSON serialization
- `is_terminal()`, `is_running()`, `is_successful()`, `is_failed()`, `is_cancelled()` — State queries

**Timezone Notes:**
- Stored as UTC (via `datetime.fromisoformat()` and `isoformat()`)
- Deserialized from ISO 8601 strings (no explicit timezone handling in current code)
- No timezone conversion logic exists yet

### WorkflowRunAttempt (src/models/workflow_attempt.py)

**Current Fields (9):**
- `id: str` — Unique identifier (UUID)
- `run_id: str` — Foreign key to WorkflowRun
- `attempt_number: int` — Attempt sequence number (1, 2, 3...)
- `status: WorkflowStatus` — Same enum as runs
- `conclusion: Optional[WorkflowConclusion]` — Same enum as runs
- `started_at: datetime` — UTC start timestamp (required)
- `completed_at: Optional[datetime]` — UTC completion timestamp (can be None)
- `duration_seconds: float` — Duration in seconds (default 0.0, non-negative)
- `logs_url: Optional[str]` — URL to logs

**Key Methods:**
- `to_dict()` / `from_dict()` — JSON serialization
- State query methods (identical to WorkflowRun)

**Relationship:**
- One-to-many: 1 WorkflowRun → N WorkflowRunAttempts
- Linked via `run_id` foreign key
- No back-reference in WorkflowRun model (data model is unidirectional)

### Enums (src/models/)

**WorkflowStatus (workflow_status.py):**
```python
enum: queued, in_progress, completed, waiting, requested, pending
```

**WorkflowConclusion (workflow_conclusion.py):**
```python
enum: success, failure, cancelled, skipped, timed_out, action_required, neutral, stale
```

---

## Service Layer: Current Filtering Capabilities

### WorkflowRunService (src/services/workflow_run_service.py)

**Existing Methods:**
- `add_workflow_run(run: WorkflowRun) → WorkflowRun` — Add run (with id uniqueness validation)
- `list_runs() → List[WorkflowRun]` — Get all runs
- `get_run_detail(run_id: str) → Optional[WorkflowRun]` — Fetch single run by id
- `filter_by_branch(branch: str) → List[WorkflowRun]` — Exact match on branch
- `filter_by_status(status: WorkflowStatus) → List[WorkflowRun]` — Exact match on status
- `filter_by_conclusion(conclusion: WorkflowConclusion) → List[WorkflowRun]` — Exact match on conclusion
- `_persist() → None` — Sync to storage

**Current Architecture:**
- In-memory list `_runs` cached on init from storage
- Filters return new lists (no mutation)
- All operations call `_persist()` after modifications
- No composite filtering (filters are mutually exclusive in CLI usage)

### WorkflowAttemptService (src/services/workflow_attempt_service.py)

**Existing Methods:**
- `add_attempt(attempt: WorkflowRunAttempt) → WorkflowRunAttempt` — Add attempt (with dual uniqueness validation: id + (run_id, attempt_number) pair)
- `list_attempts() → List[WorkflowRunAttempt]` — Get all attempts
- `get_attempt_detail(attempt_id: str) → Optional[WorkflowRunAttempt]` — Fetch single attempt by id
- `filter_by_run_id(run_id: str) → List[WorkflowRunAttempt]` — Get all attempts for a run (sorted by attempt_number ascending)
- `filter_by_status(status: WorkflowStatus) → List[WorkflowRunAttempt]` — Exact match on status
- `filter_by_conclusion(conclusion: WorkflowConclusion) → List[WorkflowRunAttempt]` — Exact match on conclusion
- `_persist() → None` — Sync to storage

**Current Architecture:**
- Same pattern as WorkflowRunService: in-memory list, immutable filters, manual persistence

### Tracker Classes

**WorkflowRunTracker (src/services/workflow_run_tracker.py):**
- High-level facade for creating runs with automatic UUID generation and UTC timestamping
- `track(...)` — Creates WorkflowRun and delegates to service.add_workflow_run()
- `create_attempt(...)` — Creates WorkflowRunAttempt and delegates to attempt_service.add_attempt()

**WorkflowAttemptTracker (src/services/workflow_attempt_tracker.py):**
- Similar facade for attempts (if separate file exists)

---

## CLI and Interactive Menu: Current Structure

### CLI Interface (src/cli/workflow_cli.py)

**Architecture:**
- `build_parser()` — Creates argparse.ArgumentParser with subcommands
- `run_cli(service, attempt_service, args)` — Dispatch handler

**Current Subcommands (workflow runs):**
1. `add` — Add new run (flags: --name, --branch, --status, --conclusion, --run-number, --commit-sha, --duration-seconds, --id)
2. `list` — List runs with optional filters (flags: --branch, --status, --conclusion)
   - Currently mutually exclusive: picks first non-None filter
3. `detail <run_id>` — Fetch single run by id
4. `query-state <run_id>` — Query state flags (terminal, running, successful, failed, cancelled)

**Current Subcommands (attempts):**
1. `attempt add` — Add new attempt
2. `attempt list` — List attempts with optional filters (flags: --run-id, --status, --conclusion)
3. `attempt detail <attempt_id>` — Fetch single attempt
4. `attempt query-state <attempt_id>` — Query state flags

**Filtering Logic (list command):**
```python
# Current logic: mutually exclusive filters (elif chain)
if ns.branch:
    runs = service.filter_by_branch(ns.branch)
elif ns.status:
    runs = service.filter_by_status(WorkflowStatus(ns.status))
elif ns.conclusion:
    runs = service.filter_by_conclusion(WorkflowConclusion(ns.conclusion))
```

**Output Format:**
- `_fmt_run(run)` — Multi-line string representation
- `_fmt_attempt(attempt)` — Multi-line string representation

### Interactive Menu (src/cli/interactive_menu.py)

**Architecture:**
- `run_interactive(service, attempt_service)` — Main menu loop
- `_run_menu(service)` — Submenu for workflow runs
- `_attempt_menu(attempt_service)` — Submenu for workflow attempts
- Menu options tied to handler functions via list of tuples

**Current Run Menu Options:**
1. Add workflow run → `_add_run()`
2. List all runs → `_list_runs()`
3. Get run detail → `_detail_run()`
4. Filter runs → `_filter_menu()` (branch/status/conclusion)
5. Query workflow state → `_query_run_state()`
6. Back

**Current Attempt Menu Options:**
1. Add workflow attempt → `_add_attempt()`
2. List all attempts → `_list_attempts()`
3. Get attempt detail → `_detail_attempt()`
4. Filter attempts → `_filter_attempts_menu()` (run_id/status/conclusion)
5. Query attempt state → `_query_attempt_state()`
6. Back

**Filtering Logic (interactive):**
- `_filter_menu()` — Prompts user to choose filter type, then filters
- Currently mutually exclusive: one filter per call
- Uses `_choose()` helper to present enum values as numbered menu

**User Input Helpers:**
- `_prompt(label, default)` — Text input with optional default
- `_choose(label, options, allow_blank)` — Numbered menu selection

---

## Storage Layer

### WorkflowJsonStorage (src/storage/workflow_json_storage.py)

- File path: typically `artifacts/workflow_runs.json`
- `load()` → Reads JSON file, deserializes list of dicts to List[WorkflowRun]
- `save(runs)` → Serializes List[WorkflowRun] to JSON dicts, writes to file
- Error handling for missing/malformed JSON

### WorkflowAttemptJsonStorage (src/storage/workflow_attempt_json_storage.py)

- File path: typically `artifacts/workflow_attempts.json`
- Same pattern as WorkflowJsonStorage but for WorkflowRunAttempt

---

## Key Findings

### 1. Data Structures Support All Required Fields

**For duration range filtering:**
- Both WorkflowRun and WorkflowRunAttempt have `duration_seconds: float` field
- Field is non-negative (validated in `from_dict()`)
- Default is 0.0

**For timestamp filtering:**
- WorkflowRun has `created_at: datetime` (required) and `updated_at: Optional[datetime]`
- WorkflowRunAttempt has `started_at: datetime` (required) and `completed_at: Optional[datetime]`
- Stored as UTC via ISO 8601 strings
- **Gap:** No explicit timezone conversion logic for CEST/UTC+2 support

**For attempts presence filtering:**
- WorkflowRunAttempt.run_id points to parent run (foreign key)
- Attempts are stored separately in WorkflowAttemptService
- **Gap:** WorkflowRun has no back-reference to attempts; must query attempt service

### 2. Service Layer Needs Extension

**Current limitations:**
- Filters are mutually exclusive in CLI (elif chain)
- Filters do not support ranges (duration, timestamps)
- Filters do not support presence checks (has attempts)
- No composite filter support (combine multiple conditions)
- Filters are specific to individual fields (no generic query builder)

**Required additions:**
- `filter_by_duration_range(min_seconds, max_seconds)` on WorkflowRunService and WorkflowAttemptService
- `filter_by_created_at(before, after)` on WorkflowRunService
- `filter_by_updated_at(before, after)` on WorkflowRunService
- `filter_by_started_at(before, after)` on WorkflowAttemptService
- `filter_by_completed_at(before, after)` on WorkflowAttemptService
- `filter_by_has_attempts(run_id)` on WorkflowRunService (requires cross-service lookup)
- Composite filter support (method or builder pattern)

### 3. CLI/Menu Interface Needs Restructuring

**Current behavior:**
- `list` command uses mutually exclusive filters (elif chain)
- Interactive `_filter_menu()` forces user to choose one filter type per call
- User must call filter multiple times to apply multiple conditions

**Required changes:**
- Support multiple filter flags simultaneously (e.g., `--duration-min 10 --duration-max 100 --branch main`)
- Composite filtering logic in CLI handler
- Interactive menu to support multi-step filter selection
- Timezone input handling for timestamp filters (allow user to specify CEST or UTC+2)

### 4. Timezone Handling Gap

**Current state:**
- All timestamps stored as UTC (via Python datetime.fromisoformat)
- No explicit timezone conversion in code
- No timezone specification in CLI or menu prompts

**Task requirement:** Support "CEST/UTC+2" timezone
- **Ambiguity:** Should user input be in CEST and converted to UTC for storage?
- **Assumption:** Yes — accept user input in CEST/UTC+2, convert to UTC for filtering/storage

### 5. Attempts Presence Filtering

**Challenge:**
- WorkflowRun and WorkflowRunAttempt are separate data structures
- WorkflowRun has no back-reference to attempts
- Must query WorkflowAttemptService to check if run has attempts

**Design choice:**
- Add method to WorkflowRunService: `filter_by_has_attempts(has_attempts: bool, attempt_service: WorkflowAttemptService)`
- Or: Add helper method on WorkflowRunTracker to enrich runs with attempt count/presence

---

## Ambiguities and Working Assumptions

### Timezone Handling

**Ambiguity:** Task mentions "CEST/UTC+2" but doesn't clarify:
- Should user input times in CEST and be converted to UTC?
- Should filtering results be shown in CEST?
- Are timestamps in stored JSON already UTC or CEST?

**Working Assumption:**
- All stored timestamps are UTC (current code pattern)
- User input timestamps can be specified in CEST (UTC+2)
- Convert user input CEST → UTC for filtering/storage
- Display timestamps in ISO 8601 (currently UTC; could be enhanced to show CEST)
- Pytz or zoneinfo library may be needed for timezone conversions

### Filter Combination Semantics

**Ambiguity:** How should multiple filters combine?
- Should `--duration-min 10 --branch main` mean "AND" (duration >= 10 AND branch == 'main')?
- Or "OR" (duration >= 10 OR branch == 'main')?

**Working Assumption:**
- Filters combine with AND logic (all conditions must be true)
- Most user-friendly for narrowing results

### Partial String Matching

**Task note:** "Could support partial string matching on fields"

**Ambiguity:** Which fields? Which pattern syntax? Glob? Regex? Case-sensitive?

**Working Assumption:**
- Optional "could have" feature
- If implemented: case-insensitive substring matching on `workflow_name` and `branch`
- Can be deferred to later; not blocking for "must have" requirements

### Attempts Presence Filter

**Ambiguity:** Should filter be:
1. "runs WITH attempts" (run_id exists in attempts list)?
2. "runs WITHOUT attempts" (run_id not in attempts list)?
3. Both (toggle)?

**Working Assumption:**
- Support both directions via boolean flag: `filter_by_has_attempts(has_attempts: bool)`
- In CLI: `--with-attempts` and `--without-attempts` (mutually exclusive or combined)
- In menu: user chooses "has attempts" or "has no attempts"

---

## Scope In/Out/Borderline

### IN: Must Implement

1. Duration range filtering (min/max)
2. Timestamp filtering (created/updated before/after for runs; started/completed for attempts)
3. Presence of attempts filtering (with/without)
4. Return filtered collections (both CLI and menu)
5. Support combining multiple filters
6. Timezone support (CEST/UTC+2)
7. CLI flags and interactive menu entry points
8. `python -m src` accessibility for all new features

### OUT: Explicitly Excluded

- GUI or graphical interface
- Database back-end (JSON storage is requirement)
- Real-time workflow integration (local tracking only)
- Filtering by HTTP request (no API mode)

### BORDERLINE: Could Have

- Partial string matching (task says "could support")
- Additional export formats (XML, CSV)
- Filter presets/saved filters
- Regex pattern matching on fields

---

## Suggested Implementation Priorities

### Priority 1: Service Layer Foundation (Highest Impact)

1. Extend `WorkflowRunService` with range and timestamp filters:
   - `filter_by_duration_range(min_secs, max_secs)`
   - `filter_by_created_at_before(dt) / after(dt)`
   - `filter_by_updated_at_before(dt) / after(dt)`
   - `filter_by_has_attempts(has_attempts, attempt_service)`

2. Extend `WorkflowAttemptService` with similar methods:
   - `filter_by_duration_range(min_secs, max_secs)`
   - `filter_by_started_at_before(dt) / after(dt)`
   - `filter_by_completed_at_before(dt) / after(dt)`

3. Implement composite filtering (optional builder pattern or multi-method chaining)

**Rationale:** Services are the core logic; everything else depends on them. Range/timestamp logic is non-trivial and must be correct at this layer.

### Priority 2: Timezone Support (Unblocks User Input)

1. Add timezone conversion utility (accept CEST input, store UTC)
2. Use Python `zoneinfo` or `pytz` for CEST ↔ UTC conversions
3. Add helper functions for parsing user-supplied timestamps

**Rationale:** Without timezone support, timestamp filters are unusable for users in CEST.

### Priority 3: CLI Enhancement (User-Facing)

1. Modify `workflow_cli.py` list command to accept all filter flags
2. Update argparse parser to allow multiple simultaneous filters
3. Implement AND-logic filtering in CLI handler
4. Add timezone input support (prompt user for timezone or default to CEST)

**Rationale:** CLI is the scripting interface; must support all combinations.

### Priority 4: Interactive Menu Enhancement (User-Facing)

1. Extend `_filter_menu()` to offer all new filter types
2. Support multi-step filter construction (allow user to add multiple conditions)
3. Add prompts for duration ranges, timestamp ranges, timezone
4. Display filter summary before executing

**Rationale:** Menu should match CLI capability; iterative filter building improves UX.

### Priority 5: Attempts Presence Logic (Cross-Service)

1. Implement logic to query attempt service and check presence
2. Wire into both CLI and menu

**Rationale:** Depends on service layer to be complete first.

### Priority 6: Testing and Validation

1. Unit tests for all new filter methods
2. Integration tests for composite filters
3. CLI tests for filter combinations
4. Menu interaction tests (mock input)

### Priority 7: Documentation Updates (Optional Polish)

1. Update README with new filter examples
2. Update class diagram if filter methods warrant it
3. Add activity diagram for new filter flow

---

## Code Locations Summary

| Component | File | Key Classes/Functions |
|-----------|------|----------------------|
| **Domain Models** | `src/models/workflow_run.py` | WorkflowRun |
| | `src/models/workflow_attempt.py` | WorkflowRunAttempt |
| | `src/models/workflow_status.py` | WorkflowStatus enum |
| | `src/models/workflow_conclusion.py` | WorkflowConclusion enum |
| **Services** | `src/services/workflow_run_service.py` | WorkflowRunService (filter_by_*) |
| | `src/services/workflow_attempt_service.py` | WorkflowAttemptService (filter_by_*) |
| | `src/services/workflow_run_tracker.py` | WorkflowRunTracker |
| | `src/services/workflow_attempt_tracker.py` | WorkflowAttemptTracker |
| **Storage** | `src/storage/workflow_json_storage.py` | WorkflowJsonStorage |
| | `src/storage/workflow_attempt_json_storage.py` | WorkflowAttemptJsonStorage |
| **CLI** | `src/cli/workflow_cli.py` | build_parser(), run_cli() |
| **Menu** | `src/cli/interactive_menu.py` | run_interactive(), _filter_menu() |
| **Entry** | `src/__main__.py` | main() dispatcher |

---

## Next Steps for System Architect / Implementer

1. **Design filter composition pattern** — decide on method chaining, builder, or multi-filter method
2. **Define timezone library** — zoneinfo (Python 3.9+) or pytz
3. **Sketch CLI argument structure** — how to express duration ranges, timestamp ranges
4. **Plan menu UX** — how to guide user through multi-filter selection
5. **Mock test data** — create workflow runs and attempts with various duration/timestamp values for testing
