# Analysis: Add duration_seconds to WorkflowRun

## Current State of WorkflowRun

**File:** `src/models/workflow_run.py`

The `WorkflowRun` class is a Python dataclass with 9 fields:
- `id` (str)
- `workflow_name` (str)
- `branch` (str)
- `status` (WorkflowStatus enum)
- `conclusion` (Optional[WorkflowConclusion] enum)
- `created_at` (datetime)
- `updated_at` (Optional[datetime])
- `run_number` (Optional[int])
- `commit_sha` (Optional[str])

**Serialization methods:**
- `to_dict()` — converts all fields to a dictionary, serializing enums to their `.value` and datetimes to ISO format
- `from_dict(data: dict)` — reconstructs a WorkflowRun from a dictionary, converting strings back to enums and datetimes

**Validation:** Currently, the dataclass has no field-level validation. The class is defined with `@dataclass` decorator from the `dataclasses` module.

## Required Changes

**1. Class Definition Addition:**
Add `duration_seconds: float = 0.0` as a new field in the dataclass. Since it has a default value, it can be placed at the end after existing fields.

**Critical constraint:** The test suite expects validation to reject negative values. The dataclass decorator alone does not provide this. The solution is to use `__post_init__()` method to validate after initialization.

**2. Serialization Changes (to_dict method):**
Add `"duration_seconds": self.duration_seconds` to the returned dictionary. No special serialization is needed since float serializes directly to JSON.

**3. Deserialization Changes (from_dict method):**
Add backward compatibility using `data.get("duration_seconds", 0.0)` to handle both:
- New records with the field present
- Old records without the field — they will use the default

## Test Suite Requirements

All 9 tests must pass:

1. `test_workflow_run_has_duration_seconds` — attribute must exist
2. `test_duration_seconds_defaults_to_zero` — must be 0.0 when not specified
3. `test_duration_seconds_can_be_set` — must accept positive values
4. `test_negative_duration_raises` — must raise exception on negative input (requires `__post_init__()`)
5. `test_duration_seconds_in_to_dict` — must appear in `to_dict()` output
6. `test_duration_seconds_round_trips_via_dict` — `to_dict()` + `from_dict()` must preserve value
7. `test_old_dict_without_duration_seconds_loads_with_default` — old dicts must load with default 0.0
8. `test_existing_fields_unchanged` — existing fields must continue to work

## Backward Compatibility Requirements

The `from_dict()` method must use `data.get()` for optional fields. When loading old JSON files without `duration_seconds`, the default 0.0 will be used. No schema migration is needed.

## Validation Mechanism

The `__post_init__()` method should raise `ValueError` if `duration_seconds < 0`.

## Files to Modify

1. **`src/models/workflow_run.py`** — Add field, validation, and serialization changes

## Diagram Impact

The class diagram (`artifacts/class_diagram.puml`) must be updated to show:
- Add `+duration_seconds : float` to the WorkflowRun attributes list
