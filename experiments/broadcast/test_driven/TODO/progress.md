# Task Progress

## Task 01: Add optional `due_date` field to Task model

### Objective
Extend `Task` with an optional `due_date: Optional[datetime]` attribute stored as CEST (UTC+2) ISO 8601 string, with full serialisation support and backward compatibility.

### Broadcast Architecture Evaluation

All 3 implementer candidates successfully completed the task:

| Candidate | Approach | Tests Passed |
|-----------|----------|--------------|
| A | Dataclass with `__post_init__` validation, CEST timezone constant, conditional serialization | 55/55 ✓ |
| B | Dataclass with `__post_init__` validation, CEST timezone constant, conditional serialization | 55/55 ✓ |
| C | Dataclass with `__post_init__` validation, CEST timezone constant, conditional serialization | 55/55 ✓ |

**Winner: Candidate A** — selected as baseline implementation (all candidates were equivalent in functionality and test coverage).

### Files Changed
- `src/models/task.py` — Added due_date field with validation and serialization support
- `tests/test_task.py` — Added 7 new test cases for due_date functionality
- `artifacts/class_diagram.puml` — Updated to include new dueDate field

### Implementation Details

**Added to Task model:**
- Field: `due_date: Optional[datetime] = None`
- CEST timezone constant: `timezone(timedelta(hours=2))`
- Validation in `__post_init__()`:
  - Rejects non-datetime types
  - Rejects naive (timezone-unaware) datetimes
  - Enforces CEST (UTC+2) timezone
- Serialization: ISO 8601 string in `to_dict()` (None if not set)
- Deserialization: ISO 8601 parsing in `from_dict()` with backward compatibility (missing field defaults to None)

### Test Results
- **Total tests**: 55 passed (7 new + 48 existing)
- **New tests**: All 7 due_date tests passing
  - ✓ Attribute exists
  - ✓ Defaults to None
  - ✓ Can be set to datetime
  - ✓ Serializes to ISO 8601
  - ✓ Round-trips via dict
  - ✓ Backward compatible with old tasks
  - ✓ Validates invalid types
- **Existing tests**: All 48 tests remain passing (backward compatible)

### Requirements Met
- ✓ Optional `due_date` field, defaults to `None`
- ✓ Timezone-aware (CEST, UTC+2)
- ✓ Rejects naive datetimes and non-CEST timezones
- ✓ Backward compatible with stored data lacking due_date
- ✓ ISO 8601 serialization in to_dict()
- ✓ ISO 8601 deserialization in from_dict()
- ✓ No external dependencies

Duration: 168.6s | Cost: $0.434074 USD | Turns: 32
