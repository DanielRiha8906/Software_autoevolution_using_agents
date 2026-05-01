# Implementation Design: Duration Tracking for WorkflowRun

## Executive Summary

Add `duration_seconds: float` attribute to the `WorkflowRun` dataclass with:
- Non-negative validation via `__post_init__()`
- Default value of 0.0 for backward compatibility
- Integration across model, service, CLI, and test layers
- Safe deserialization from existing JSON files that lack the field

## Implementation Order (Dependency Tree)

```
1. WorkflowRun model (base)
   ├── 2a. WorkflowJsonStorage (inherits serialization)
   ├── 2b. WorkflowRunTracker (accepts parameter)
   ├── 2c. WorkflowRunService (no changes, uses existing model)
   └── 3. CLI layers
       ├── WorkflowCLI (accepts and displays)
       └── InteractiveMenu (accepts and displays)
       └── 4. Tests (verify all changes)
```

## Phase 1: Model Layer (No dependencies)

**File:** `src/models/workflow_run.py`

Changes:
1. Add field to dataclass: `duration_seconds: float = 0.0` (after `commit_sha`)
2. Add `__post_init__()` method to validate non-negative:
   ```python
   def __post_init__(self):
       if self.duration_seconds < 0:
           raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}")
   ```
3. Update `to_dict()` method: add line `"duration_seconds": self.duration_seconds,`
4. Update `from_dict()` classmethod: add parameter to constructor call
   `duration_seconds=data.get("duration_seconds", 0.0),`

**Rationale:**
- `__post_init__()` is the standard dataclass pattern for validation
- Using `data.get()` with default 0.0 ensures old JSON files without the field load safely
- Field placement after optional fields maintains compatibility with positional instantiation

## Phase 2: Storage Layer (Depends on Phase 1)

**File:** `src/storage/workflow_json_storage.py`

Changes: **None required**

Rationale:
- The storage layer generically calls `to_dict()` and `from_dict()` on WorkflowRun
- Once WorkflowRun includes `duration_seconds` in its serialization methods, storage automatically persists and loads it
- No hardcoding of field names in storage layer

## Phase 2: Service Layer (Depends on Phase 1)

**File:** `src/services/workflow_run_service.py`

Changes: **None required**

Rationale:
- WorkflowRunService operates on WorkflowRun instances without assumptions about specific attributes
- No changes needed to add_workflow_run(), list_runs(), filter_by_*() methods

## Phase 2: WorkflowRunTracker (Depends on Phase 1)

**File:** `src/services/workflow_run_tracker.py`

Changes:
1. Add parameter to `track()` method signature: `duration_seconds: Optional[float] = None,`
2. Pass to WorkflowRun constructor:
   `duration_seconds=duration_seconds if duration_seconds is not None else 0.0,`

**Method signature (full):**
```python
def track(
    self,
    workflow_name: str,
    branch: str,
    status: WorkflowStatus,
    conclusion: Optional[WorkflowConclusion] = None,
    run_number: Optional[int] = None,
    commit_sha: Optional[str] = None,
    run_id: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> WorkflowRun:
```

Rationale:
- Optional parameter preserves backward compatibility (existing code that doesn't pass duration still works)
- Explicit None check ensures 0.0 is the default for the model

## Phase 3a: WorkflowCLI (Depends on Phase 2)

**File:** `src/cli/workflow_cli.py`

Changes:

1. **Update `_fmt_run()` function**:
   - Add line after `updated = ...` line:
     ```python
     duration = f"{run.duration_seconds:.1f}s" if run.duration_seconds else "—"
     ```
   - Add to formatted output:
     ```python
     f"  duration    : {duration}\n"
     ```
     Insert after the "updated_at" line

2. **Update `build_parser()` argument parser** (add subcommand):
   - Add after the `--commit-sha` argument:
     ```python
     add_p.add_argument(
         "--duration",
         type=float,
         default=None,
         help="Duration in seconds (non-negative)",
     )
     ```

3. **Update `run_cli()` function**:
   - Add `duration_seconds=ns.duration,` parameter to `tracker.track()` call

**Rationale:**
- `_fmt_run()` formats duration with 1 decimal place for readability; uses "—" if zero
- `type=float` in argparse ensures user input is validated as numeric
- Adding to `tracker.track()` call passes user input through to the model

## Phase 3b: InteractiveMenu (Depends on Phase 2)

**File:** `src/cli/interactive_menu.py`

Changes:

1. **Update `_fmt_run()` function**:
   - After line for `conclusion = ...`, add:
     ```python
     duration = f"{run.duration_seconds:.1f}s" if run.duration_seconds else "—"
     ```
   - Add to formatted output string after "updated_at" line:
     ```python
     f"  duration    : {duration}\n"
     ```

2. **Update `_add_run()` function**:
   - After the `commit_sha = ...` line, add:
     ```python
     duration_raw = _prompt("Duration in seconds (leave blank for 0)", "0")
     duration = float(duration_raw) if duration_raw and duration_raw != "0" else 0.0
     ```
   - Add `duration_seconds=duration,` to `tracker.track()` call

**Rationale:**
- Interactive menu uses `_prompt()` helper for input; default "0" makes it optional
- User-friendly prompt text explains the field
- Duration formatting matches `workflow_cli.py` for consistency

## Phase 4: Test Layer (Depends on Phase 1-3)

**File:** `tests/test_workflow_json_storage.py`

Changes:

1. **Update `_sample_run()` helper**:
   - Add field to the WorkflowRun instance:
     ```python
     duration_seconds=45.5,
     ```

2. **Add new tests**:
   ```python
   def test_save_and_load_duration_roundtrip(tmp_storage):
       run = _sample_run()
       tmp_storage.save([run])
       loaded = tmp_storage.load()
       assert loaded[0].duration_seconds == 45.5


   def test_duration_in_json(tmp_storage):
       run = _sample_run()
       tmp_storage.save([run])
       raw = json.loads(Path(tmp_storage.filepath).read_text())
       assert raw[0]["duration_seconds"] == 45.5


   def test_load_json_without_duration_defaults_to_zero(tmp_storage):
       # Simulate old JSON file without duration_seconds field
       old_format = [
           {
               "id": "r1",
               "workflow_name": "Deploy",
               "branch": "main",
               "status": "completed",
               "conclusion": "success",
               "created_at": "2024-01-01T00:00:00+00:00",
               "updated_at": None,
               "run_number": 42,
               "commit_sha": "deadbeef",
           }
       ]
       Path(tmp_storage.filepath).parent.mkdir(parents=True, exist_ok=True)
       Path(tmp_storage.filepath).write_text(json.dumps(old_format))
       loaded = tmp_storage.load()
       assert loaded[0].duration_seconds == 0.0
   ```

**File:** `tests/test_workflow_run_service.py`

Changes:

1. **Update `_make_run()` helper**:
   - Add field to the WorkflowRun instance:
     ```python
     duration_seconds=0.0,
     ```

2. **Add test for non-negative validation**:
   ```python
   def test_workflow_run_rejects_negative_duration():
       with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
           WorkflowRun(
               id="r1",
               workflow_name="Test",
               branch="main",
               status=WorkflowStatus.COMPLETED,
               conclusion=WorkflowConclusion.SUCCESS,
               created_at=datetime.now(timezone.utc),
               updated_at=None,
               run_number=1,
               commit_sha="abc",
               duration_seconds=-1.0,
           )
   ```

**Rationale:**
- Tests verify the new field persists through save/load
- JSON persistence test confirms the field appears in serialized format
- Backward compatibility test proves old files load with default value
- Validation test ensures negative values are caught at instantiation time

## Validation Strategy

**Location:** `WorkflowRun.__post_init__()` method

**Approach:** Dataclass post-initialization validation
- Simple, built-in to dataclass pattern
- Executes immediately after all fields are set
- Raises `ValueError` with clear message for non-negative constraint

**Validation Logic:**
```python
if self.duration_seconds < 0:
    raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}")
```

## Backward Compatibility Approach

**JSON Files Without `duration_seconds` Field:**

The `from_dict()` method uses:
```python
duration_seconds=data.get("duration_seconds", 0.0),
```

This ensures:
1. Old JSON files missing the field use default 0.0
2. Existing code that serializes old WorkflowRun instances loads without errors
3. New instances always have a valid duration_seconds value

**No Migration Required:**
- Storage layer calls `from_dict()` automatically when loading
- Default value in `data.get()` handles missing fields seamlessly
- Existing JSON files remain valid and readable

## File Changes Summary

| File | Change Type | Dependencies | Status |
|------|------------|--------------|--------|
| `src/models/workflow_run.py` | Add field, validation, serialization | None | Implement first |
| `src/storage/workflow_json_storage.py` | None (inherits from WorkflowRun) | Phase 1 | No code changes |
| `src/services/workflow_run_service.py` | None | Phase 1 | No code changes |
| `src/services/workflow_run_tracker.py` | Add parameter | Phase 1 | Implement second |
| `src/cli/workflow_cli.py` | Add argument, update display | Phase 2 | Implement third |
| `src/cli/interactive_menu.py` | Add prompt, update display | Phase 2 | Implement fourth |
| `tests/test_workflow_json_storage.py` | Update helper, add tests | Phase 1 | Implement fifth |
| `tests/test_workflow_run_service.py` | Update helper, add tests | Phase 1 | Implement fifth |

## Implementation Checklist

- [ ] Phase 1: `src/models/workflow_run.py` — add field, `__post_init__()`, update `to_dict()`, `from_dict()`
- [ ] Phase 2a: `src/services/workflow_run_tracker.py` — add parameter to `track()`
- [ ] Phase 2b: Update test helpers `_sample_run()` and `_make_run()`
- [ ] Phase 3a: `src/cli/workflow_cli.py` — add --duration argument, update `_fmt_run()`, pass to tracker
- [ ] Phase 3b: `src/cli/interactive_menu.py` — add duration prompt, update `_fmt_run()`, pass to tracker
- [ ] Phase 4a: `tests/test_workflow_json_storage.py` — add serialization and backward compatibility tests
- [ ] Phase 4b: `tests/test_workflow_run_service.py` — add validation test
- [ ] Verify: Run `pytest tests/ -q` — all tests pass
- [ ] Verify: Run CLI commands with and without --duration
- [ ] Verify: Backward compatibility with existing JSON files

## Notes for Implementer

1. **Dataclass field ordering:** The new field must come after `commit_sha` because all required fields must precede optional fields with defaults.

2. **`__post_init__()` placement:** Add it immediately after the field definitions in the class body, before `to_dict()`.

3. **Test helper updates:** Both `_sample_run()` and `_make_run()` must include `duration_seconds` to ensure new instances match the updated model.

4. **CLI formatting consistency:** Both `workflow_cli.py` and `interactive_menu.py` have nearly identical `_fmt_run()` functions. Update both to match.

5. **Backward compatibility testing:** The test `test_load_json_without_duration_defaults_to_zero` is critical to verify old files load correctly.

6. **No new dependencies:** This change uses only Python standard library. No new packages needed.
