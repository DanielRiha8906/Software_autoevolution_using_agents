# Task 01: Add optional `due_date` field to Task model

## Broadcast Evaluation Results

### Candidate A - SELECTED
**Test Score:** 48/48 ✓
**Approach:** Dataclass field with `__post_init__()` validation

**Implementation Details:**
- Added `due_date: Optional[datetime] = None` field to Task dataclass
- Defined CEST timezone constant: `timezone(timedelta(hours=2))`
- Used `__post_init__()` to validate:
  - Type-checking: must be datetime or None
  - Timezone requirement: must be CEST (rejects naive datetimes)
  - Timezone enforcement: rejects non-CEST timezones
- Updated `to_dict()` to conditionally serialize due_date as ISO 8601
- Updated `from_dict()` to parse due_date and handle backward compatibility

**Why Selected:**
All three candidates produced identical implementations with identical test results. Candidate A was selected as the winner because it completed first in the parallel evaluation phase. The implementation is clean, well-structured, and maintains full backward compatibility.

### Candidate B
**Test Score:** 48/48 ✓
**Approach:** Identical to Candidate A

### Candidate C
**Test Score:** 48/48 ✓
**Approach:** Identical to Candidate A

## Files Changed
- `src/models/task.py`: Added due_date field, CEST constant, __post_init__ validation, updated serialization methods
- `tests/test_task.py`: Added 7 test cases covering all due_date functionality

## Test Results
**All Tests Passing:** 48/48
- 7 new due_date-specific tests
- 41 existing tests (all backward compatible)

## Backward Compatibility
✓ Tasks without due_date in stored data load without error
✓ Serialization omits due_date field when None
✓ Existing Task deserialization works unchanged
✓ No breaking changes to Task constructor or API

Duration: PENDING | Cost: PENDING | Turns: PENDING
