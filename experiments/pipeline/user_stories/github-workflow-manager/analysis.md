# Task 01 Analysis: Add duration_seconds to WorkflowRun

## What the Task Is Asking For

Add a new `duration_seconds: float` attribute to the `WorkflowRun` class that:
- Represents total execution time in seconds
- Is persisted and loaded through the storage layer
- Has serialization/deserialization logic integrated
- Rejects negative values (validation)
- Defaults to 0.0 if not provided (backward compatible)
- Does not use external time measurement tools (values are supplied externally)

## Current WorkflowRun Structure

**Location:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`

**Current attributes:**
- `id: str` — unique identifier
- `workflow_name: str` — name of the workflow
- `branch: str` — git branch
- `status: WorkflowStatus` — current execution status (enum)
- `conclusion: Optional[WorkflowConclusion]` — outcome (optional enum)
- `created_at: datetime` — creation timestamp
- `updated_at: Optional[datetime]` — last update timestamp (optional)
- `run_number: Optional[int]` — GitHub run number (optional)
- `commit_sha: Optional[str]` — commit hash (optional)

**Current class form:** `@dataclass` with two methods:
- `to_dict() -> dict` — serializes to JSON-compatible dict
- `from_dict(data: dict) -> WorkflowRun` — deserializes from dict (class method)

## Storage and Serialization Architecture

**Storage Layer:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/storage/workflow_json_storage.py`

The `WorkflowJsonStorage` class:
- Saves runs by calling `run.to_dict()` on each run and serializing to JSON
- Loads runs by parsing JSON and calling `WorkflowRun.from_dict()` on each item
- File location: `artifacts/workflow_runs.json` (configurable)

**Serialization/Deserialization Flow:**
1. Save: `List[WorkflowRun]` → `to_dict()` on each → `json.dumps()` with indent 2
2. Load: JSON file → `json.loads()` → `from_dict()` on each → `List[WorkflowRun]`

**Current serialization mapping in `to_dict()`:**
- `status` → stored as `status.value` (string)
- `conclusion` → stored as `conclusion.value if conclusion else None` (string or null)
- `created_at`/`updated_at` → stored as `.isoformat()` (ISO 8601 string)
- All other fields → stored as-is

**Current deserialization in `from_dict()`:**
- Reads keys directly from dict with `.get()` for optional fields
- Reconstructs enums via `WorkflowStatus(data["status"])` and `WorkflowConclusion(data["conclusion"])`
- Reconstructs datetimes via `datetime.fromisoformat()`

## Service Layer Integration

**Location:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/services/workflow_run_service.py`

- `WorkflowRunService` holds `_runs: List[WorkflowRun]` in memory
- `_persist()` calls `self._storage.save(self._runs)`
- `add_workflow_run(run)` validates uniqueness by ID and calls `_persist()`

**Tracker Layer:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/services/workflow_run_tracker.py`

- `WorkflowRunTracker.track()` method creates new `WorkflowRun` instances
- Currently does NOT set `duration_seconds` — will need to accept it as optional parameter with default 0.0

## CLI Integration Points

Two CLI entry points need updates to expose `duration_seconds`:

### 1. Command-line interface
**Location:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/workflow_cli.py`

- `build_parser()` defines argparse subcommands
- `add` subcommand should accept `--duration-seconds` flag
- `_fmt_run()` formats output for display

### 2. Interactive menu
**Location:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/interactive_menu.py`

- `_add_run()` prompts user for workflow details
- `_fmt_run()` formats output for display

## Testing Patterns

**Existing test locations:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/tests/test_workflow_json_storage.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/tests/test_workflow_run_service.py`

**Patterns observed:**
- `_sample_run()` / `_make_run()` helper functions create test instances
- Storage tests verify round-trip serialization/deserialization
- Service tests verify business logic (filtering, deduplication)
- Tests use `MagicMock` for storage layer
- Tests check both in-memory state and persisted JSON format

## Files That Will Need Changes

1. **Model class:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`
     - Add `duration_seconds: float` attribute to dataclass
     - Update `to_dict()` to include `duration_seconds`
     - Update `from_dict()` to deserialize `duration_seconds` with default 0.0
     - Add validation to reject negative values

2. **Service layer:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/services/workflow_run_tracker.py`
     - Add optional `duration_seconds` parameter to `track()` method
     - Pass it to `WorkflowRun` constructor with default 0.0

3. **CLI layer:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/workflow_cli.py`
     - Add `--duration-seconds` argument to `add` subcommand (type=float)
     - Pass it to `tracker.track()` call
     - Update `_fmt_run()` to display duration_seconds in output

   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/interactive_menu.py`
     - Add prompt for duration_seconds in `_add_run()` with default "0.0"
     - Parse float value with validation
     - Pass it to `tracker.track()` call
     - Update `_fmt_run()` to display duration_seconds in output

4. **Test files:**
   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/tests/test_workflow_json_storage.py`
     - Update `_sample_run()` to include `duration_seconds`
     - Add tests for negative value rejection
     - Add test for default value (backward compatibility)
     - Add round-trip serialization test for the new field

   - `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/tests/test_workflow_run_service.py`
     - Update `_make_run()` to include `duration_seconds`
     - Add test for negative value rejection
     - Add test for default value during creation

## Existing Validation Patterns

**No explicit validation in WorkflowRun currently** — the dataclass does not validate field values in `__post_init__`. The code relies on consumers providing correct types.

**Validation opportunities:**
- Could add `__post_init__()` method to validate `duration_seconds >= 0`
- Alternatively, add validation in `from_dict()` to handle corrupt JSON gracefully
- Should decide whether to raise `ValueError` for negative values or silently clamp/default

**Assumption:** Add validation in `__post_init__()` with a `ValueError` if duration_seconds < 0, following defensive programming principle. This ensures the constraint is enforced at object construction time, regardless of entry point (CLI, tracker, direct instantiation).

## Backward Compatibility

**JSON file compatibility:** Old files without `duration_seconds` field will need `from_dict()` to handle missing keys gracefully.

**Recommendation:** Use `.get("duration_seconds", 0.0)` in `from_dict()` to default to 0.0 for missing fields, ensuring old workflow_runs.json files can still be loaded.

## Architecture Diagram Impact

Class diagram (`artifacts/class_diagram.puml`) shows `WorkflowRun` attributes. Need to add:
```
+duration_seconds : float
```
to the WorkflowRun class box.

---

**Summary:** The change is localized to the model layer (single attribute + validation + serialization logic) and CLI/tracker layers (input handling + display). Storage layer requires no changes to implementation—only to handle the new field in existing `to_dict()` and `from_dict()` flows. Tests need updates to cover the new attribute and negative-value rejection.
