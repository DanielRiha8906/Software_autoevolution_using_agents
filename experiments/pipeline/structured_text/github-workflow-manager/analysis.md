# Task 01 Analysis: Add duration_seconds to WorkflowRun

## Task Summary

Add a new attribute `duration_seconds: float` to the `WorkflowRun` dataclass to track the total execution time of workflow runs in seconds. The attribute must be:
- Stored and persisted in the JSON storage layer
- Included in serialization/deserialization logic
- Non-negative with a default of 0.0 if not provided

## Current Architecture

### WorkflowRun Class Definition
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/models/workflow_run.py`

Current fields (lines 11-19):
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
```

Methods:
- `to_dict()` (lines 21-32): Converts dataclass to dictionary, serializing enums and datetimes to strings
- `from_dict(cls, data: dict)` (lines 34-46): Class method to reconstruct from dictionary with deserialization of enums and datetimes

### Storage Layer
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/storage/workflow_json_storage.py`

- `save(runs: List[WorkflowRun])` (lines 13-15): Calls `run.to_dict()` on each run and writes to JSON file using `json.dumps()`
- `load()` (lines 17-21): Reads JSON file and calls `WorkflowRun.from_dict()` to reconstruct instances
- Default filepath: `artifacts/workflow_runs.json`

Current serialization format (based on `to_dict()`):
```json
[
  {
    "id": "...",
    "workflow_name": "...",
    "branch": "...",
    "status": "queued|in_progress|completed|waiting|requested|pending",
    "conclusion": "success|failure|...|null",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00|null",
    "run_number": 42|null,
    "commit_sha": "deadbeef|null"
  }
]
```

### Key Usage Points

**WorkflowRunTracker** (`src/services/workflow_run_tracker.py`, lines 17-38):
- Creates new `WorkflowRun` instances via the `track()` method
- Does not currently provide a `duration_seconds` parameter
- Automatically sets `created_at` to current UTC time

**WorkflowRunService** (`src/services/workflow_run_service.py`):
- Manages in-memory run list and persists via `_persist()` (calls `storage.save()`)
- Does not validate or manipulate duration values

**CLI Modules** (two formatting functions):
- `workflow_cli.py::_fmt_run()` (lines 12-25): Displays run details in text format
- `interactive_menu.py::_fmt_run()` (lines 32-44): Similar display logic for interactive mode
- Neither module currently displays duration information

### Existing Tests
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/tests/test_workflow_json_storage.py`

- `test_save_and_load_roundtrip()` (lines 35-45): Verifies all fields survive save/load cycle
- `test_save_persists_json()` (lines 48-53): Checks actual JSON file content

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/tests/test_workflow_run_service.py`

- Helper `_make_run()` (lines 11-22): Creates test fixtures with all current fields

## Files That Must Change

### Must Have (Core Implementation)

1. **src/models/workflow_run.py**
   - Add `duration_seconds: float = 0.0` field to dataclass (after line 19)
   - Update `to_dict()` to include `"duration_seconds": self.duration_seconds`
   - Update `from_dict()` to handle `data.get("duration_seconds", 0.0)` for backwards compatibility

2. **src/services/workflow_run_tracker.py**
   - Add `duration_seconds: Optional[float] = None` parameter to `track()` method signature (around line 17)
   - Pass `duration_seconds=duration_seconds or 0.0` to WorkflowRun constructor

3. **tests/test_workflow_json_storage.py**
   - Update `_sample_run()` helper to include `duration_seconds=0.0` or appropriate test value
   - Add test case for duration_seconds roundtrip persistence
   - Add test case for JSON format includes duration_seconds

4. **tests/test_workflow_run_service.py**
   - Update `_make_run()` helper to include `duration_seconds` parameter with test value

### Should Have (Validation & UX)

5. **src/models/workflow_run.py** (enhanced)
   - Add optional validation logic or use field with validation (consider dataclass post_init if needed)

6. **src/cli/workflow_cli.py**
   - Add `--duration` argument to the `add` subcommand parser (around line 52)
   - Update `run_cli()` to pass duration to `tracker.track()`
   - Update `_fmt_run()` to display duration in output (around line 24)

7. **src/cli/interactive_menu.py**
   - Update `_add_run()` to prompt for duration input (around line 54)
   - Pass duration to `tracker.track()`
   - Update `_fmt_run()` to display duration (around line 43)

## Dependencies & Constraints

### Data Type Choice
- Using `float` (not int) allows for sub-second precision without additional complexity
- JSON serialization/deserialization handles float natively

### Backwards Compatibility
- Existing persisted JSON files won't have `duration_seconds` field
- `from_dict()` must use `.get("duration_seconds", 0.0)` to handle both old and new formats
- Default value of 0.0 is safe for existing data

### Validation Scope
- Task says "should validate non-negative" but doesn't specify error handling strategy
- Options: raise ValueError, clamp to 0.0, or log warning
- Assumption: Use dataclass field validation (post_init or validator) to raise ValueError if < 0

### CLI Integration
- No existing CLI arguments for duration currently
- `--duration` flag for CLI add command should be optional with default 0.0
- Interactive menu should prompt but allow blank/zero

### UML Diagram Update Required
- Class diagram (artifacts/class_diagram.puml) shows WorkflowRun without duration_seconds
- Will need update to reflect the new attribute (line 28-36 in class definition)

## Implementation Order

1. Add field to WorkflowRun dataclass with default value
2. Update to_dict() and from_dict() for serialization
3. Update WorkflowRunTracker.track() to accept and pass duration parameter
4. Update storage tests to verify roundtrip
5. Update CLI and interactive menu to accept/display duration
6. Update class diagram artifact

## Ambiguities & Assumptions

1. **No explicit source of duration data**: Task doesn't specify where duration_seconds values come from. Assumption: tracked externally and passed to `track()` method or provided via CLI.

2. **Sub-second precision**: Task says "could have higher precision (milliseconds)" as optional. Assumption: using `float` (seconds) is sufficient for MVP; millisecond tracking can be added later without breaking the field.

3. **Validation strategy**: "Validate non-negative" is stated. Assumption: raise ValueError on negative values in dataclass post_init or a custom validator.

4. **Default behavior**: No explicit default mentioned. Assumption: 0.0 is sensible (unknown/unmeasured duration).

5. **Existing CLI behavior**: Currently `tracker.track()` is called without duration_seconds. Assumption: making it optional with default 0.0 in track() method maintains backwards compatibility.

## Summary of Changes

**6 files to modify:**
- 1 model file (core): add field, update serialization
- 1 service file: add parameter to track method
- 2 test files: update fixtures and add duration tests
- 2 CLI files: add input/output support for duration

**Key invariants to maintain:**
- JSON roundtrip must preserve float precision
- Backwards compatibility with old JSON files (missing duration_seconds)
- All existing tests continue to pass after adding default values
