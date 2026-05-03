# Task Progress

## Task 01: Add due date to tasks

### Status: COMPLETED ✓

### Files Changed
- `src/models/task.py` — Added due_date attribute, is_overdue() method, serialization
- `src/services/task_manager.py` — Added set_due_date() and _validate_due_date() methods
- `src/services/todo_service.py` — Added set_due_date() wrapper method
- `src/cli/todo_cli.py` — Added due-date subcommand and display logic
- `src/cli/interactive_menu.py` — Added menu option 6 for setting due dates
- `tests/test_task.py` — Added 6 new tests for due date functionality
- `tests/test_task_manager.py` — Added 6 new tests for service layer
- `artifacts/class_diagram.puml` — Updated UML to reflect due_date feature

### Test Results
- **Total tests: 53**
- **Passed: 53**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Add attribute `due_date: Optional[datetime]` to `Task`
✓ MUST: Allow tasks without a due date (`None` by default)
✓ MUST: Ensure `due_date` is stored and persisted through storage layer
✓ MUST: Update `to_dict` and `from_dict` accordingly
✓ MUST: Use CEST (UTC+2) timezone-aware datetime representation (ISO 8601)
✓ SHOULD: Preserve backward compatibility with stored JSON data
✓ SHOULD: Validate that a provided due date is a valid datetime before accepting
✓ COULD: Add `is_overdue()` predicate to `Task` returning True when past due

### Implementation Summary
- Due dates stored internally as UTC (ISO 8601), displayed as CEST (Europe/Paris timezone)
- User input interpreted as CEST time ("YYYY-MM-DD HH:MM" format)
- Validation prevents setting past due dates
- Backward compatibility: old tasks without due_date field load without error
- Two CLI modes: interactive (option 6) and one-shot (`due-date` subcommand)
- UML diagrams updated to reflect new classes and methods

Duration: 367.9s | Cost: $0.723867 USD | Turns: 18

---

## Task 02: Add status and due date methods to Task

### Status: COMPLETED ✓

### Files Changed
- `src/models/task.py` — Added mark_in_progress(), mark_done(), reopen(), is_completed() methods
- `tests/test_task_transitions.py` — New file with 27 unit tests for Task status methods
- `tests/test_todo_service_transitions.py` — New file with 17 service integration tests
- `tests/test_cli_transitions.py` — New file with 22 CLI command tests
- `artifacts/class_diagram.puml` — Updated UML to reflect new Task methods

### Test Results
- **Total tests: 119**
- **Passed: 119**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: mark_in_progress() — transitions status to IN_PROGRESS
✓ MUST: mark_done() — transitions status to DONE
✓ MUST: reopen() — transitions status to PENDING
✓ MUST: is_completed() — returns True when status is DONE
✓ MUST: is_overdue() — returns True when due_date is earlier than current CEST time
✓ MUST: Each status-mutating method updates updated_at to current CEST time
✓ MUST: Methods derive state strictly from existing Task attributes
✓ MUST: All functionality accessible via python -m src (interactive menu + CLI flag)
✓ SHOULD: Prevent invalid status transitions (silent no-op strategy)
✓ SHOULD: Add unit tests covering all status transitions and overdue combinations

### Implementation Summary
- Four new instance methods on Task class: mark_in_progress(), mark_done(), reopen(), is_completed()
- Invalid status transitions result in silent no-ops (idempotent behavior)
- updated_at timestamp updated only when status actually changes
- Timezone handling: datetime.now(ZoneInfo("Europe/Paris")).astimezone(timezone.utc)
- 66 new tests across three test files: unit, service integration, and CLI tests
- Existing CLI commands (start, done, reopen) already support new functionality
- Existing service layer (TodoService.start_task, complete_task, reopen_task) fully utilized
- All status mutations properly persist to storage via Task.to_dict/from_dict

Duration: PENDING | Cost: PENDING | Turns: PENDING
