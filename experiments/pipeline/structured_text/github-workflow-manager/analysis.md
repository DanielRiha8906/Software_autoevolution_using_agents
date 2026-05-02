# TASK 01 - Duration Tracking: Analysis Report

## Task Summary
Add explicit duration tracking to the `WorkflowRun` class as a new required attribute (`duration_seconds: float`). The value must be stored, persisted, serialized/deserialized, and default to `0.0` if not provided. Must validate that duration is non-negative.

---

## Current WorkflowRun Structure

### Definition Location
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/models/workflow_run.py`

### Current Attributes (9 total)
1. `id: str` — unique identifier
2. `workflow_name: str` — name of the workflow
3. `branch: str` — git branch name
4. `status: WorkflowStatus` — enum (QUEUED, IN_PROGRESS, COMPLETED, WAITING, REQUESTED, PENDING)
5. `conclusion: Optional[WorkflowConclusion]` — optional enum (SUCCESS, FAILURE, CANCELLED, SKIPPED, TIMED_OUT, ACTION_REQUIRED, NEUTRAL, STALE)
6. `created_at: datetime` — timestamp when run was created
7. `updated_at: Optional[datetime]` — optional timestamp when run was last updated
8. `run_number: Optional[int]` — optional run number (e.g., GitHub Actions run count)
9. `commit_sha: Optional[str]` — optional commit SHA

### Implementation Details
- Implemented as a **dataclass** (using `@dataclass` decorator)
- No field defaults currently defined
- Has two methods: `to_dict()` for serialization and `from_dict()` classmethod for deserialization

---

## Storage Implementation

### Storage Layer
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/storage/workflow_json_storage.py`

### Storage Technology: JSON File-Based
- **Serialization format:** JSON text file
- **Default file path:** `artifacts/workflow_runs.json`
- **File location is configurable** via constructor parameter

### Storage Methods
1. **`save(runs: List[WorkflowRun]) -> None`**
   - Converts list of WorkflowRun objects to list of dicts using `run.to_dict()`
   - Writes as JSON with indent=2 to file
   - Path parent directories created if missing

2. **`load() -> List[WorkflowRun]`**
   - Returns empty list if file doesn't exist
   - Loads JSON and reconstructs WorkflowRun objects using `WorkflowRun.from_dict(item)`

---

## Serialization/Deserialization Approach

### Current Implementation (JSON)

#### `to_dict()` serialization pattern:
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "workflow_name": self.workflow_name,
        "branch": self.branch,
        "status": self.status.value,                    # enum.value
        "conclusion": self.conclusion.value if self.conclusion else None,  # optional enum
        "created_at": self.created_at.isoformat(),      # datetime to ISO string
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,  # optional datetime
        "run_number": self.run_number,
        "commit_sha": self.commit_sha,
    }
```

#### `from_dict()` deserialization pattern:
```python
@classmethod
def from_dict(cls, data: dict) -> "WorkflowRun":
    return cls(
        id=data["id"],
        workflow_name=data["workflow_name"],
        branch=data["branch"],
        status=WorkflowStatus(data["status"]),          # string to enum
        conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
        created_at=datetime.fromisoformat(data["created_at"]),  # ISO string to datetime
        updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        run_number=data.get("run_number"),
        commit_sha=data.get("commit_sha"),
    )
```

### Key Serialization Patterns
- **Enums:** Stored as string `.value`, reconstructed from string
- **Datetimes:** Stored as ISO format strings, reconstructed from ISO format
- **Optional fields:** Checked with conditional or `.get()`, stored as `None` if absent
- **Simple types:** Stored directly (int, str, float)

---

## Data Flow for WorkflowRun

### Creation Flow
1. **WorkflowRunTracker.track()** creates a new WorkflowRun instance
   - File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/services/workflow_run_tracker.py`
   - Constructor receives all parameters and defaults `created_at` to current UTC time
   - Passes constructed run to `WorkflowRunService.add_workflow_run()`

2. **WorkflowRunService.add_workflow_run()** validates and persists
   - File: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/github-workflow-manager/src/services/workflow_run_service.py`
   - Checks for duplicate IDs
   - Appends to internal list `_runs`
   - Calls `_persist()` which invokes `storage.save(self._runs)`

3. **WorkflowJsonStorage.save()** serializes and writes to disk
   - Calls `run.to_dict()` for each run
   - Writes JSON array to file

### Reading Flow
1. **WorkflowJsonStorage.load()** deserializes from disk
   - Loads JSON from file (or returns empty list if file missing)
   - Calls `WorkflowRun.from_dict(item)` for each item

2. **WorkflowRunService.__init__()** loads and caches in memory
   - Stores list in `self._runs`
   - All read operations work on cached list

### Display Flow
- **CLI (`workflow_cli.py`)** and **Interactive Menu (`interactive_menu.py`)** both have `_fmt_run()` function
- Displays all attributes including datetime values as ISO strings
- Currently displays 9 attributes; will display 10 after duration_seconds is added

---

## Files That Need Modification

### MUST MODIFY (5 files)

1. **`src/models/workflow_run.py`**
   - Add `duration_seconds: float` attribute to dataclass
   - Update `to_dict()` to include `"duration_seconds": self.duration_seconds`
   - Update `from_dict()` to deserialize duration_seconds with default 0.0 and validation

2. **`src/services/workflow_run_tracker.py`**
   - Update `track()` method signature to accept optional `duration_seconds` parameter
   - Pass it to WorkflowRun constructor, defaulting to 0.0 if not provided

3. **`src/cli/workflow_cli.py`**
   - Add `--duration` argument to the "add" subcommand parser (float type, optional)
   - Update the `add` command handler to pass duration_seconds to tracker.track()
   - Update `_fmt_run()` to display duration_seconds in the formatted output

4. **`src/cli/interactive_menu.py`**
   - Update `_add_run()` to prompt for duration_seconds with default 0.0
   - Pass it to tracker.track()
   - Update `_fmt_run()` to display duration_seconds in the formatted output

5. **`tests/test_workflow_json_storage.py`**
   - Update `_sample_run()` to include `duration_seconds` parameter
   - Add test to verify duration_seconds is correctly serialized/deserialized
   - Verify validation (non-negative) if applicable in tests

### SHOULD ALSO CONSIDER (2 files, non-critical for basic functionality)

6. **`tests/test_workflow_run_service.py`**
   - Update `_make_run()` helper to include `duration_seconds=0.0`
   - Optionally add test for duration_seconds validation

7. **`src/__main__.py`**
   - No changes needed; storage and service initialization will automatically handle new field

---

## Constraints & Patterns to Follow

### Dataclass Convention
- Use field defaults when appropriate
- For required fields with validation, implement in `from_dict()` or add custom `__post_init__()` if needed
- Currently no custom `__init__()`, only dataclass-generated one

### Validation Strategy
- **Non-negative check:** Best placed in `from_dict()` during deserialization
- Could also add to `__post_init__()` if validation needed on direct instantiation
- Default to 0.0 when not provided (use `.get()` pattern in from_dict)

### JSON Serialization Pattern
- Simple numeric types (float) serialize directly without transformation
- No need for special handling like enums or datetimes

### Optional vs Required Decision
- Duration is **not marked Optional** in requirements (must be present)
- Should have a default value (0.0) when not explicitly provided
- Field must be non-nullable in JSON storage

### CLI Pattern
- Arguments in "add" subcommand are named with hyphens (--duration-seconds preferred over --duration)
- Choices are provided for enums
- Optional arguments use default=None
- Types are explicit (type=float for numeric)

### Display Format
- Keep ISO format for timestamps
- Duration should display as numeric value (e.g., "123.45" seconds or "123.45 s")
- Add to both `_fmt_run()` implementations (CLI and interactive menu)

---

## Summary: What Must Change

| Component | Change Type | Details |
|-----------|------------|---------|
| WorkflowRun dataclass | Add attribute | `duration_seconds: float` |
| WorkflowRun.to_dict() | Add serialization | `"duration_seconds": self.duration_seconds` |
| WorkflowRun.from_dict() | Add deserialization | Parse float, validate non-negative, default 0.0 |
| WorkflowRunTracker.track() | Add parameter | `duration_seconds: float = 0.0` |
| workflow_cli.py add command | Add argument | `--duration-seconds` (float, optional) |
| workflow_cli.py _fmt_run() | Add display | Show duration_seconds in output |
| interactive_menu.py _add_run() | Add prompt | Ask user for duration_seconds |
| interactive_menu.py _fmt_run() | Add display | Show duration_seconds in output |
| test_workflow_json_storage.py | Update fixtures | Add duration_seconds to test data |

---

## Edge Cases & Considerations

1. **Existing JSON files:** When loading old JSON files without `duration_seconds` field, `from_dict()` should use default 0.0
2. **Backwards compatibility:** New field is optional on input, has a default, so old code creating runs still works
3. **Validation:** Non-negative check should occur in `from_dict()` when reading from storage; this catches bad data at deserialization
4. **CLI input:** User can omit --duration-seconds flag; tracker defaults to 0.0
5. **Interactive mode:** Prompt should allow empty input with 0.0 as default

