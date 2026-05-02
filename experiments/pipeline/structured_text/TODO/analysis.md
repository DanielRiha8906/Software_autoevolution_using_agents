# Task 02: Add Status and Due Date Methods to Task — Analysis Report

**Date:** 2026-05-02  
**Status:** Analysis complete

---

## Task Overview

Task 02 requires implementing status-mutating methods on the Task class to encapsulate state transitions with automatic timestamp updates in CEST timezone. This builds on Task 01 which added the `due_date` attribute.

## Current Task Class State

**Location:** `src/models/task.py`

**Current attributes:**
- `id: str` (UUID)
- `title: str` (required)
- `description: Optional[str]`
- `status: TaskStatus` (enum: PENDING, IN_PROGRESS, DONE)
- `created_at: datetime` (UTC timezone)
- `updated_at: datetime` (UTC timezone)
- `due_date: Optional[datetime]` (CEST timezone, added in Task 01)

**Existing methods:**
- `is_overdue()` — already exists, returns True if due_date < current CEST time
- `to_dict()` / `from_dict()` — serialization

## What Must Be Added

1. **`mark_in_progress()`** — transitions status to IN_PROGRESS, updates `updated_at` to CEST
2. **`mark_done()`** — transitions status to DONE, updates `updated_at` to CEST
3. **`reopen()`** — transitions status to PENDING, updates `updated_at` to CEST
4. **`is_completed()`** — returns True if status == DONE
5. `is_overdue()` already exists

## What Should Be Added

- Validate state transitions to prevent invalid changes (e.g., PENDING → DONE directly)
- Unit tests covering all transitions and overdue combinations

## What Could Be Added

- `is_pending()` — returns True if status == PENDING
- `is_in_progress()` — returns True if status == IN_PROGRESS

## Valid State Transitions

According to state_diagram.puml:
- PENDING → IN_PROGRESS only
- IN_PROGRESS → DONE only
- DONE → PENDING only

## Key Constraints

1. **Timezone:** `updated_at` must be set to CEST time on mutations (though `created_at` remains UTC)
2. **Exception handling:** Need to handle invalid transitions (raise ValueError or custom exception)
3. **Task Status:** Currently status changes handled by service layer; need to add encapsulated methods on Task class

## Files to Modify

- **Core:** `src/models/task.py` — add methods to Task class
- **Tests:** `tests/test_task.py` — add tests for new methods
- **Diagrams:** `artifacts/class_diagram.puml` — update to show new methods
