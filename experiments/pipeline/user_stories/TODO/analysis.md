# Task 02 Analysis: Task Status Transition Methods

## Task Summary

Acceptance Criteria require that the `Task` class provide five status-mutating methods (`mark_in_progress()`, `mark_done()`, `reopen()`) and two status-checking predicates (`is_completed()`, `is_overdue()`, `is_pending()`, `is_in_progress()`), with specific state transition rules and timezone handling for CEST.

## Current Task Class Structure

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task.py`

### Attributes
- `id: str` (UUID, auto-generated)
- `title: str` (required)
- `description: Optional[str]` (default: None)
- `status: TaskStatus` (enum: PENDING, IN_PROGRESS, DONE; default: PENDING)
- `created_at: datetime` (UTC timezone-aware, auto-generated)
- `updated_at: datetime` (UTC timezone-aware, auto-generated)
- `due_date: Optional[datetime]` (optional, must be timezone-aware if provided)

### Current Methods
- `__post_init__()` — validates `due_date` is timezone-aware
- `to_dict()` — serializes to dictionary with ISO 8601 datetime strings
- `from_dict(data: dict)` — deserializes from dictionary

### TaskStatus Enum
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task_status.py`

Three states:
- `PENDING = "pending"`
- `IN_PROGRESS = "in_progress"`
- `DONE = "done"`

## State Diagram (from artifacts/state_diagram.puml)

```
[*] → PENDING
PENDING → IN_PROGRESS (via "start")
IN_PROGRESS → DONE (via "complete")
DONE → IN_PROGRESS (via "reopen")
```

**Critical constraint:** The diagram shows no transition FROM PENDING to DONE directly, and no transition FROM DONE back to PENDING. The `reopen()` method should transition DONE → IN_PROGRESS, not DONE → PENDING.

## Missing Methods — Required by Task 02

### Status Transition Methods (Task class)

1. **`mark_in_progress() -> Task`**
   - Transition: PENDING → IN_PROGRESS or IN_PROGRESS → IN_PROGRESS (idempotent or no-op)
   - Updates `updated_at` to current CEST time
   - Returns the task object for chaining

2. **`mark_done() -> Task`**
   - Transition: IN_PROGRESS → DONE (or PENDING → DONE?)
   - Updates `updated_at` to current CEST time
   - Returns the task object for chaining

3. **`reopen() -> Task`**
   - Transition: DONE → IN_PROGRESS
   - Updates `updated_at` to current CEST time
   - Returns the task object for chaining
   - Note: Current code has `reopen_task()` in `TodoService` that sets status to PENDING, but the state diagram shows DONE → IN_PROGRESS

### Status Predicate Methods (Task class)

4. **`is_completed() -> bool`**
   - Returns `True` if status == TaskStatus.DONE

5. **`is_pending() -> bool`**
   - Returns `True` if status == TaskStatus.PENDING
   - Not explicitly required but mentioned in criteria for "symmetry"

6. **`is_in_progress() -> bool`**
   - Returns `True` if status == TaskStatus.IN_PROGRESS
   - Not explicitly required but mentioned in criteria for "symmetry"

7. **`is_overdue() -> bool`**
   - Returns `True` if `due_date` is set AND `due_date` is in the past (relative to now in CEST)
   - Returns `False` if no `due_date` is set
   - Must compare against current CEST time, not UTC

## State Transition Rules

From the acceptance criteria and state diagram:

| From | To | Method | Allowed? | Notes |
|------|-----|--------|----------|-------|
| PENDING | IN_PROGRESS | `mark_in_progress()` | Yes | Valid transition |
| IN_PROGRESS | DONE | `mark_done()` | Yes | Valid transition |
| DONE | IN_PROGRESS | `reopen()` | Yes | Valid transition (per state diagram) |
| PENDING | DONE | `mark_done()` | No? | Not shown in state diagram; accept/reject? |
| PENDING | PENDING | `mark_in_progress()` | No-op or error? | Invalid transition |
| IN_PROGRESS | IN_PROGRESS | `mark_in_progress()` | No-op or error? | Invalid transition |
| DONE | DONE | `mark_done()` | No-op or error? | Invalid transition |
| PENDING | IN_PROGRESS | `reopen()` | No? | Invalid transition |
| IN_PROGRESS | IN_PROGRESS | `reopen()` | No? | Invalid transition |

**Acceptance Criteria Note:** "Invalid transitions (e.g. `reopen()` on a PENDING task) are either a no-op or raise an error." This is deliberately ambiguous. Implementation must choose one strategy.

## Timezone Handling

### Current State
- `created_at` and `updated_at` are stored in UTC: `datetime.now(timezone.utc)`
- `due_date` is validated to be timezone-aware but can be any timezone
- Serialization uses ISO 8601 format (preserves timezone offset)
- Deserialization uses `datetime.fromisoformat()` (preserves timezone)

### Task 02 Requirement: CEST
- Acceptance criteria state: "updates `updated_at` to the current CEST time"
- CEST is Central European Summer Time (UTC+2)
- This conflicts with the current UTC-based approach

**Ambiguity:** Should `updated_at` be stored in CEST, or stored in UTC but calculated against CEST when updating? The acceptance criteria wording suggests the former (store in CEST), but this breaks the timezone consistency already established in the codebase.

**Working assumption:** Status transition methods will update `updated_at` to CEST time by using `datetime.now(timezone(timedelta(hours=2)))` or equivalent. However, this may break existing UTC-only tests and serialization roundtrips.

### `is_overdue()` Implementation
- Must compare `due_date` (which could be any timezone) against "now" in CEST
- Convert current CEST time to the same timezone as `due_date`, or convert `due_date` to CEST and compare

## Files That Will Need Modification

### Primary
- **`src/models/task.py`** — add the five methods to the Task dataclass

### Secondary (may require updates for consistency)
- **`src/services/task_manager.py`** — if status transition validation logic is added at the service layer (currently `set_status()` is permissive)
- **`src/services/todo_service.py`** — if new public methods are added for direct task method calls (currently routes through TaskManager)
- **`src/cli/todo_cli.py`** — may need new command flags if Task methods are to be exposed via CLI (though current CLI uses service methods, not task methods directly)
- **`src/cli/interactive_menu.py`** — same as above

### Test Files (will need new tests)
- **`tests/test_task.py`** — test all five methods, state transitions, invalid transitions, timezone handling

### Diagrams (will need updates)
- **`artifacts/class_diagram.puml`** — add the five new methods to Task class definition

## Key Constraints and Decisions Needed

1. **Invalid Transition Handling:** Choose between no-op vs. raising exception
   - Current code raises no errors for invalid `set_status()` calls
   - Decision impacts error handling in CLI and service layers

2. **CEST Storage vs. UTC Storage:**
   - Current codebase uses UTC everywhere
   - Task 02 criteria mention CEST explicitly
   - Decision impacts serialization, deserialization, and backward compatibility

3. **PENDING → DONE Transition:**
   - State diagram shows no direct path
   - Acceptance criteria don't explicitly forbid it
   - Decision: either allow it or enforce PENDING → IN_PROGRESS → DONE

4. **Idempotent vs. Error-Raising:**
   - If `mark_in_progress()` is called on an IN_PROGRESS task, should it:
     - Update `updated_at` and return (idempotent with side effect)
     - Do nothing and return (true no-op)
     - Raise an error

5. **Method Scope:**
   - Are these methods intended to be called directly on Task objects (model-layer)?
   - Or are they decorative and the actual transitions happen via TodoService/TaskManager?
   - Current architecture routes all state changes through services; adding Task methods breaks that pattern

## Summary of Findings

**What exists:**
- Task class with status attribute and full datetime support
- State diagram showing valid transitions
- Service layer (TodoService, TaskManager) already handles status changes
- Test infrastructure in place

**What's missing:**
- Five methods on Task class: `mark_in_progress()`, `mark_done()`, `reopen()`, `is_completed()`, `is_pending()`, `is_in_progress()`, `is_overdue()`
- State transition validation and error handling (currently permissive)
- CEST-specific time handling for `updated_at` updates
- Tests for new methods

**Blockers/Ambiguities:**
- CEST requirement conflicts with UTC-first architecture
- Invalid transition behavior (no-op vs. error) not specified
- PENDING → DONE transition not shown in state diagram
- `is_pending()` and `is_in_progress()` are bonus for "symmetry," not core requirement
