# Analysis: Add Duration Tracking to WorkflowRun

## Task Summary

Implement a `duration_seconds: float` attribute on the `WorkflowRun` class to track the total execution time of workflow runs. This enables performance analysis and identification of slow runs over time.

## Current Implementation

### WorkflowRun Class Structure
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`

Current attributes:
- `id: str` — unique identifier
- `workflow_name: str` — name of the workflow
- `branch: str` — git branch
- `status: WorkflowStatus` — current execution status
- `conclusion: Optional[WorkflowConclusion]` — final result
- `created_at: datetime` — creation timestamp
- `updated_at: Optional[datetime]` — last update timestamp
- `run_number: Optional[int]` — run sequence number
- `commit_sha: Optional[str]` — commit hash

The class uses `@dataclass` decorator and currently has:
- `to_dict()` method: serializes all attributes to dictionary (enums to `.value`, datetimes to ISO format)
- `from_dict()` classmethod: deserializes from dictionary (reconstructs enums, parses ISO datetime strings)

### Storage Layer
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/storage/workflow_json_storage.py`

Mechanism:
- Uses JSON file storage (default: `artifacts/workflow_runs.json`)
- `save()` method: calls `to_dict()` on all runs and writes as JSON array
- `load()` method: reads JSON file and reconstructs runs via `from_dict()`

### Tracker and Creation Path
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/services/workflow_run_tracker.py`

The `WorkflowRunTracker.track()` method is the primary creation path:
- Accepts optional parameters including `workflow_name`, `branch`, `status`, `conclusion`, `run_number`, `commit_sha`, `run_id`
- Creates `WorkflowRun` instances with auto-generated UUID if `run_id` not provided
- Sets `created_at` to current UTC time
- Sets `updated_at` to `None`
- Delegates persistence to `WorkflowRunService.add_workflow_run()`

### CLI and Interactive Menu
Both CLI and interactive menu use the tracker to create runs. The formatting functions (`_fmt_run()`) display run details to users.

**Files:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/workflow_cli.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/cli/interactive_menu.py`

## Files That Need Modification

### Core Implementation (Required)
1. **`src/models/workflow_run.py`**
   - Add `duration_seconds: float = 0.0` attribute to dataclass
   - Update `to_dict()` to include `duration_seconds`
   - Update `from_dict()` to parse `duration_seconds` with default fallback to 0.0
   - Add validation to reject negative values

2. **`src/services/workflow_run_tracker.py`**
   - Add optional `duration_seconds` parameter to `track()` method signature
   - Pass `duration_seconds` to `WorkflowRun` constructor
   - Handle default value (0.0) if not provided

### UI/Formatting (For Usability)
3. **`src/cli/workflow_cli.py`**
   - Add `--duration` argument to `add` subcommand
   - Add `duration_seconds` display to `_fmt_run()` output
   - Pass parsed duration to tracker

4. **`src/cli/interactive_menu.py`**
   - Add duration input prompt in `_add_run()` function
   - Add `duration_seconds` display to `_fmt_run()` output
   - Pass parsed duration to tracker

### Tests (For Validation)
5. **`tests/test_workflow_json_storage.py`**
   - Update `_sample_run()` fixture to include `duration_seconds` parameter
   - Add test cases for roundtrip serialization with duration (including 0.0 and various float values)
   - Add test case for backward compatibility (loading JSON without duration field)

6. **`tests/test_workflow_run_service.py`**
   - Update `_make_run()` helper to include `duration_seconds`
   - Optionally add test for negative value rejection

## Changes Required by Acceptance Criterion

### Criterion 1: `WorkflowRun` has `duration_seconds: float` attribute
**File:** `src/models/workflow_run.py`
- Add field to dataclass with type annotation and default value of 0.0

### Criterion 2: Attribute stored and loaded through storage layer
**Files:** `src/models/workflow_run.py`, `src/storage/workflow_json_storage.py`
- `to_dict()` must serialize the attribute
- `from_dict()` must deserialize the attribute
- Storage layer automatically persists via existing `save()` and `load()` mechanisms

### Criterion 3: Serialization/deserialization logic updated
**File:** `src/models/workflow_run.py`
- `to_dict()`: add `"duration_seconds": self.duration_seconds`
- `from_dict()`: add `duration_seconds=data.get("duration_seconds", 0.0)` with fallback for backward compatibility

### Criterion 4: Negative values rejected
**File:** `src/models/workflow_run.py`
- Add `__post_init__()` method to dataclass
- Validate: `if self.duration_seconds < 0: raise ValueError("duration_seconds must be non-negative")`

### Criterion 5: Defaults to 0.0 if not provided
**Files:** `src/models/workflow_run.py`, `src/services/workflow_run_tracker.py`
- Dataclass field default: `duration_seconds: float = 0.0`
- Tracker parameter default: `duration_seconds: float = 0.0` in method signature

### Criterion 6: No external time measurement tools used
**Scope:** Confirmed — implementation only adds a storage field; no new imports or external dependencies needed

## Key Implementation Notes

1. **Backward Compatibility:** When loading existing JSON files without the `duration_seconds` field, `from_dict()` must use `data.get("duration_seconds", 0.0)` to provide a sensible default rather than raising a KeyError.

2. **Validation Pattern:** The dataclass does not currently have a `__post_init__()` method. This will be the first validation added to the class. The pattern should match Python dataclass conventions.

3. **CLI/Interactive Updates:** While not required by acceptance criteria, the CLI and interactive menu should be updated to display and allow input of duration values for a complete user experience.

4. **Test Coverage:** Existing test fixtures create `WorkflowRun` instances directly. All test files must be updated to include the new parameter to avoid missing positional argument errors.

5. **Float Precision:** No specific precision requirements stated. Standard Python float is appropriate (IEEE 754 double precision).

## Summary

**Total files to modify:** 6 (2 core + 2 UI + 2 test)

**Core changes:**
- Add `duration_seconds: float = 0.0` to `WorkflowRun` dataclass
- Implement validation in `__post_init__()` to reject negative values
- Update `to_dict()` and `from_dict()` for serialization/deserialization
- Add optional `duration_seconds` parameter to `WorkflowRunTracker.track()`
- Update CLI and interactive menu to support duration input
- Update all test fixtures and helper functions

**Risk level:** Low — straightforward dataclass attribute addition with existing serialization patterns.
