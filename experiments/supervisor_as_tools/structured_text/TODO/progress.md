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
