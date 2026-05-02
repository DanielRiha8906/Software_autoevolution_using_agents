# Experiment Progress: Broadcast / Structured Text / TODO

## Task 01: Add due date to tasks

### Broadcast Fan-out Results

Three independent implementations were created on separate branches:

| Candidate | Approach | Test Results | Notes |
|-----------|----------|--------------|-------|
| **A** | Full-stack: Model + Services + CLI | 41/41 ✓ | Added --due-date CLI args, service layer support, overdue display |
| **B** | Full-stack: Model + Services + CLI | 41/41 ✓ | **Selected** - Robust validation, error handling, ISO 8601 format |
| **C** | Model-only | 41/41 ✓ | Minimal approach, no service/CLI extensions |

### Selected Solution: Implementer-B (broadcast-candidate-b)

**Rationale**: While all three solutions passed all 41 tests, Implementer-B provided the most complete implementation. According to CLAUDE.md, "All functionality must be reachable via `python -m src` — a feature is not complete until it has a CLI entry point." Implementer-B included:
- Full CLI support with `--due-date` arguments for `add` and `update` commands
- Service layer integration (TaskManager and TodoService)
- Robust validation and user-friendly error messages
- Overdue status display in the `show` command

### Files Changed

1. **src/models/task.py**
   - Added `due_date: Optional[datetime] = None` attribute
   - Added CEST timezone constant (UTC+2)
   - Updated `to_dict()` to serialize due_date in ISO 8601 format
   - Updated `from_dict()` with backward compatibility for legacy JSON
   - Added `is_overdue()` method

2. **src/services/task_manager.py**
   - Extended `add()` method to accept optional `due_date` parameter
   - Extended `update()` method to accept optional `due_date` parameter

3. **src/services/todo_service.py**
   - Extended `add_task()` method to accept optional `due_date` parameter
   - Extended `update_task()` method to accept optional `due_date` parameter

4. **src/cli/todo_cli.py**
   - Added `--due-date` argument to `add` command
   - Added `--due-date` argument to `update` command
   - Implemented ISO 8601 date parsing and validation
   - Display due date and overdue status in `show` command

### Requirements Compliance

**Must:**
- ✓ Add attribute `due_date: Optional[datetime]` to Task
- ✓ Allow tasks without a due date (None by default)
- ✓ Ensure due_date is stored and persisted through storage layer
- ✓ Update to_dict() and from_dict() accordingly
- ✓ Use CEST (UTC+2) timezone-aware datetime (ISO 8601)

**Should:**
- ✓ Preserve backward compatibility with stored JSON data
- ✓ Validate that provided due dates are valid datetime values

**Could:**
- ✓ Added `is_overdue()` predicate

**Won't:**
- ✗ External calendar integration (not required)

### Test Results

- Baseline tests: 41/41 passing ✓
- No test modifications were needed
- Full backward compatibility verified

Duration: PENDING | Cost: PENDING | Turns: PENDING
