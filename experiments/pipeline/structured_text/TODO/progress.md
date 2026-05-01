# TODO Experiment Progress

## Task 01: Add due date to tasks

**Status:** ✅ Completed

**Files Changed:**
- src/models/task.py — Added due_date field, updated to_dict/from_dict, added is_overdue() method
- src/services/task_manager.py — Added due_date parameter to add() and update() methods
- src/services/todo_service.py — Added due_date parameter to add_task() and update_task() methods
- src/cli/todo_cli.py — Added --due-date argument, parse and display functions
- src/cli/interactive_menu.py — Added due_date prompts and display
- tests/test_task.py — Added 6 comprehensive tests for due_date functionality
- artifacts/class_diagram.puml — Updated Task class with due_date and is_overdue()

**Test Result:** ✅ All 47 tests passed

**Requirements Implemented:**
- ✅ MUST: due_date: Optional[datetime] = None field added
- ✅ MUST: Stored and persisted through JSON storage layer
- ✅ MUST: to_dict() and from_dict() updated
- ✅ MUST: CEST (UTC+2) timezone-aware using zoneinfo.ZoneInfo("Europe/Paris")
- ✅ SHOULD: Backward compatibility with old JSON (tasks without due_date load as None)
- ✅ SHOULD: Validate datetime values before accepting
- ✅ COULD: is_overdue() predicate implemented

Duration: PENDING | Cost: PENDING | Turns: PENDING
