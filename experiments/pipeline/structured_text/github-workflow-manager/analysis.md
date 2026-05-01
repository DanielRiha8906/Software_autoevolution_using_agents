# Analysis: Add Duration Tracking to WorkflowRun

## What the Task Is Asking For

Add duration tracking capability to the `WorkflowRun` class that captures how long a workflow execution takes in seconds. This requires:
- Adding a `duration_seconds: float` attribute to the WorkflowRun dataclass
- Ensuring it persists through the JSON storage layer
- Supporting serialization/deserialization
- Validating non-negative values with a default of 0.0
- Optionally supporting higher precision (milliseconds)

## Current State of WorkflowRun

**File:** `src/models/workflow_run.py`

The `WorkflowRun` class is a Python dataclass with 9 attributes:
- `id: str` — unique identifier
- `workflow_name: str` — name of the workflow
- `branch: str` — git branch
- `status: WorkflowStatus` — current status (enum)
- `conclusion: Optional[WorkflowConclusion]` — final result (enum)
- `created_at: datetime` — creation timestamp
- `updated_at: Optional[datetime]` — last update timestamp
- `run_number: Optional[int]` — sequential run identifier
- `commit_sha: Optional[str]` — commit reference

The class includes:
- `to_dict()` method that converts all attributes to serializable format (enums to values, datetimes to ISO format)
- `from_dict()` classmethod that reconstructs instances from dictionaries (converts string values back to enums, ISO strings back to datetimes)

## Files Requiring Changes

### 1. Model Layer
**File:** `src/models/workflow_run.py`

Changes needed:
- Add `duration_seconds: float = 0.0` attribute to the dataclass
- Update `to_dict()` to include `duration_seconds` in the returned dictionary
- Update `from_dict()` to read `duration_seconds` from the input dict with a default of 0.0

### 2. Storage Layer
**File:** `src/storage/workflow_json_storage.py`

Impact:
- No code changes required — the layer generically calls `to_dict()`/`from_dict()` on WorkflowRun instances
- Changes to WorkflowRun serialization/deserialization will automatically propagate here
- When `save()` is called, the new `duration_seconds` field will be included in JSON
- When `load()` is called, the new field will be deserialized automatically

### 3. Service Layer
**File:** `src/services/workflow_run_service.py`

Impact:
- No changes required — it operates on WorkflowRun instances without assumptions about specific attributes

**File:** `src/services/workflow_run_tracker.py`

Changes needed:
- Add `duration_seconds: Optional[float] = None` parameter to the `track()` method signature
- Pass `duration_seconds` (defaulting to 0.0 if None) when creating the WorkflowRun instance

### 4. CLI Layer
**File:** `src/cli/workflow_cli.py`

Changes needed:
- Update `_fmt_run()` function to display `duration_seconds` in the formatted output
- Add `--duration` argument to the `add` subcommand parser to allow users to specify duration in seconds
- Pass `duration_seconds` parameter when calling `tracker.track()`

**File:** `src/cli/interactive_menu.py`

Changes needed:
- Update `_fmt_run()` function to display `duration_seconds` in the formatted output
- Update `_add_run()` to prompt for duration input and pass it to `tracker.track()`

### 5. Test Layer
**File:** `tests/test_workflow_json_storage.py`

Changes needed:
- Update `_sample_run()` helper to include `duration_seconds` in the sample WorkflowRun instance
- Add tests to verify `duration_seconds` persists through save/load roundtrip
- Test JSON serialization includes the duration_seconds field

**File:** `tests/test_workflow_run_service.py`

Changes needed:
- Update `_make_run()` helper to include `duration_seconds` in test instances
- Optionally add tests for non-negative validation (if validation is implemented)

## Key Constraints and Dependencies

1. **Dataclass defaults:** The `duration_seconds: float = 0.0` must be a required or defaulted field. Since it comes after `commit_sha` (optional), it should also be optional or have a default to maintain proper dataclass field ordering.

2. **Serialization format:** The `from_dict()` method uses `data.get()` for optional fields with defaults. For `duration_seconds`, use `data.get("duration_seconds", 0.0)` to maintain backward compatibility with existing JSON files that don't have this field.

3. **Validation:** No code currently validates field constraints. If non-negative validation is required (Should Have requirement), add logic either in:
   - A `__post_init__()` method on the dataclass, or
   - A validation method in the model

4. **CLI integration:** Both CLI modules have identical `_fmt_run()` functions — changes must be made in both places to keep them in sync.

5. **Backward compatibility:** Existing JSON files without `duration_seconds` will need to handle missing values gracefully. The `from_dict()` approach with `data.get("duration_seconds", 0.0)` addresses this.

6. **Class diagram artifact:** The PlantUML class diagram will need to be updated to reflect the new `duration_seconds` attribute in the WorkflowRun class.

## Scope Summary

**In scope:**
- Add duration_seconds attribute to WorkflowRun dataclass with default 0.0
- Update serialization/deserialization in to_dict/from_dict
- Update CLI input (workflow_cli.py) to accept duration parameter
- Update CLI display (both workflow_cli.py and interactive_menu.py) to show duration
- Update WorkflowRunTracker.track() to accept duration parameter
- Add/update tests to verify functionality
- Non-negative validation (Should Have)

**Out of scope:**
- Millisecond precision support
- External time measurement tools
- Automatic duration calculation from timestamps
- Integration with actual GitHub workflow APIs
