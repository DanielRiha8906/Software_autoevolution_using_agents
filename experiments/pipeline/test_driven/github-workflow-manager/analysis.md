# Analysis: Adding duration_seconds to WorkflowRun

## Task Summary
Add a `duration_seconds: float` attribute to the `WorkflowRun` dataclass to track how long each workflow run takes. The field must default to `0.0`, reject negative values, and support full serialization/deserialization round-tripping with backward compatibility for old records.

## Current Implementation

### WorkflowRun Class (src/models/workflow_run.py)
**Location**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/github-workflow-manager/src/models/workflow_run.py`

**Current fields**:
- `id: str` — Unique identifier
- `workflow_name: str` — Name of the workflow
- `branch: str` — Git branch name
- `status: WorkflowStatus` — Enum (queued, in_progress, completed, waiting, requested, pending)
- `conclusion: Optional[WorkflowConclusion]` — Optional enum (success, failure, cancelled, skipped, timed_out, action_required, neutral, stale)
- `created_at: datetime` — UTC timestamp
- `updated_at: Optional[datetime]` — Optional UTC timestamp
- `run_number: Optional[int]` — GitHub run number
- `commit_sha: Optional[str]` — Commit SHA

**Current methods**:
- `to_dict() -> dict` — Serializes to dictionary, converting enums to string values and datetimes to ISO format strings
- `from_dict(cls, data: dict) -> WorkflowRun` — Class method deserializes from dictionary

### Serialization Behavior (to_dict)
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "workflow_name": self.workflow_name,
        "branch": self.branch,
        "status": self.status.value,  # Converts enum to string
        "conclusion": self.conclusion.value if self.conclusion else None,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        "run_number": self.run_number,
        "commit_sha": self.commit_sha,
    }
```

### Deserialization Behavior (from_dict)
```python
@classmethod
def from_dict(cls, data: dict) -> "WorkflowRun":
    return cls(
        id=data["id"],
        workflow_name=data["workflow_name"],
        branch=data["branch"],
        status=WorkflowStatus(data["status"]),  # Converts string to enum
        conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        run_number=data.get("run_number"),
        commit_sha=data.get("commit_sha"),
    )
```

**Note**: `from_dict` uses `data.get()` for optional fields, providing graceful defaults for missing keys.

## Test Requirements

**Test file location**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/prompts/strategies/test_driven/github-workflow-manager/01_add_domain_attribute/prompt.txt`

**Tests to satisfy**:
1. `test_workflow_run_has_duration_seconds` — Attribute must exist
2. `test_duration_seconds_defaults_to_zero` — Default value must be 0.0
3. `test_duration_seconds_can_be_set` — Must accept custom values (e.g., 42.5)
4. `test_negative_duration_raises` — Must reject negative values (raise an Exception)
5. `test_duration_seconds_in_to_dict` — Must appear in to_dict() output
6. `test_duration_seconds_round_trips_via_dict` — Must survive from_dict(to_dict())
7. `test_old_dict_without_duration_seconds_loads_with_default` — Old records without the field must deserialize with default 0.0
8. `test_existing_fields_unchanged` — Existing fields must not be affected

## What Needs to Change

### 1. WorkflowRun Dataclass Definition
**File**: `src/models/workflow_run.py`

**Change required**:
- Add `duration_seconds: float = 0.0` field to the dataclass
- Position it after existing fields (recommended: after `commit_sha`)
- Must use `field()` from dataclasses module to add validation if using `__post_init__`

**Implementation option**:
Use dataclass `__post_init__` method to validate that duration_seconds >= 0.0, raising a ValueError (or any Exception) if negative.

### 2. Serialization (to_dict method)
**File**: `src/models/workflow_run.py`

**Change required**:
- Add `"duration_seconds": self.duration_seconds` to the returned dictionary
- Place it alongside other numeric fields (e.g., after `run_number`)

### 3. Deserialization (from_dict classmethod)
**File**: `src/models/workflow_run.py`

**Change required**:
- Add `duration_seconds=data.get("duration_seconds", 0.0)` to the constructor call
- Must use `.get()` with default 0.0 to support backward compatibility with old records
- This ensures records stored before this feature was added will load with duration_seconds=0.0

## Backward Compatibility Considerations

**Key requirement**: Old records in workflow_runs.json that do not have a "duration_seconds" key must deserialize without errors.

**Storage flow**:
1. `WorkflowJsonStorage.save()` calls `run.to_dict()` and writes JSON
2. `WorkflowJsonStorage.load()` reads JSON and calls `WorkflowRun.from_dict()`
3. Old JSON records will not have "duration_seconds" key
4. `data.get("duration_seconds", 0.0)` in from_dict provides safe default

**No database migrations needed**: JSON storage is file-based, and from_dict gracefully handles missing keys.

## Validation Strategy

**Negative value rejection**:
- Use `__post_init__` method in the dataclass to validate
- Raise an Exception (e.g., ValueError) if `self.duration_seconds < 0`
- This is called automatically after __init__ completes

```python
def __post_init__(self):
    if self.duration_seconds < 0:
        raise ValueError("duration_seconds cannot be negative")
```

## Impact on Other Components

**Services** (workflow_run_service.py, workflow_run_tracker.py):
- No changes needed if duration_seconds is always passed or defaults correctly
- If WorkflowRunTracker.track() is called without duration_seconds, dataclass default (0.0) applies
- Consider: Should tracker accept duration_seconds parameter? (Not required for tests, but useful feature)

**Storage** (workflow_json_storage.py):
- No code changes needed
- Works automatically via to_dict/from_dict

**Existing tests**:
- All existing tests should pass without modification
- They create WorkflowRun instances without duration_seconds, relying on the default

## Summary of Changes

| Component | File | Changes |
|---|---|---|
| WorkflowRun class | src/models/workflow_run.py | Add field, add __post_init__ validation, update to_dict(), update from_dict() |
| None (no code changes) | src/services/ | No changes required |
| None (no code changes) | src/storage/ | No changes required |

## Constraints

- Do not modify test files
- Do not use external time measurement tools
- Preserve all existing WorkflowRun fields and behavior
- Must handle both positive floats and zero
- Must reject negative floats at construction time (before object is fully created)

## Success Criteria

1. All 8 new tests pass
2. All 9 existing tests still pass
3. Code compiles without syntax or import errors
4. Backward compatibility with old JSON records (missing duration_seconds) works
5. No modifications to test files or governance files
