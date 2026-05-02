# Design Plan: Status Methods on Task Model

## Overview

Add 7 new methods to the `Task` class in `src/models/task.py`:
- 3 mutation methods: `mark_in_progress()`, `mark_done()`, `reopen()`
- 4 query methods: `is_completed()`, `is_overdue()`, `is_pending()`, `is_in_progress()`

All mutation methods must update the `updated_at` timestamp to current CEST time (UTC+2). Query methods are read-only.

## Method Specifications

### Mutation Methods (update status and updated_at to CEST now)

#### mark_in_progress()
```python
def mark_in_progress(self) -> None:
    self.status = TaskStatus.IN_PROGRESS
    self.updated_at = datetime.now(tz=CEST)
```

#### mark_done()
```python
def mark_done(self) -> None:
    self.status = TaskStatus.DONE
    self.updated_at = datetime.now(tz=CEST)
```

#### reopen()
```python
def reopen(self) -> None:
    self.status = TaskStatus.PENDING
    self.updated_at = datetime.now(tz=CEST)
```

### Query Methods (read-only state checks)

#### is_completed()
```python
def is_completed(self) -> bool:
    return self.status == TaskStatus.DONE
```

#### is_pending()
```python
def is_pending(self) -> bool:
    return self.status == TaskStatus.PENDING
```

#### is_in_progress()
```python
def is_in_progress(self) -> bool:
    return self.status == TaskStatus.IN_PROGRESS
```

#### is_overdue()
```python
def is_overdue(self) -> bool:
    if self.due_date is None:
        return False
    if self.status == TaskStatus.DONE:
        return False
    now_cest = datetime.now(tz=CEST)
    return self.due_date < now_cest
```

## Key Implementation Details

1. **No new imports needed** — CEST constant already defined, TaskStatus already imported
2. **No dataclass field changes** — only add new methods
3. **No state validation** — all transitions are permissive
4. **Timezone handling** — mutations use `datetime.now(tz=CEST)`, is_overdue uses same for comparison
5. **Insertion point** — add methods at end of Task class, after existing methods

## Files Changed
- `src/models/task.py` — add 7 methods to Task class

## Constraints
- All state derives from existing attributes
- Mutations update updated_at to current CEST time
- updated_at must remain timezone-aware (tzinfo=CEST)
- No modifications to existing fields or methods
