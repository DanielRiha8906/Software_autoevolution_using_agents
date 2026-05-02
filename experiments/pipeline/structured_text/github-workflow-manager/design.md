# Design Plan: Workflow Run State Logic Implementation

## State Truth Table

| Status | Conclusion | is_running() | is_terminal() | is_successful() | is_failed() | is_cancelled() |
|--------|-----------|--------------|---------------|-----------------|-------------|----------------|
| QUEUED | None | False | False | False | False | False |
| PENDING | None | False | False | False | False | False |
| WAITING | None | True | False | False | False | False |
| REQUESTED | None | True | False | False | False | False |
| IN_PROGRESS | None | True | False | False | False | False |
| COMPLETED | SUCCESS | False | True | True | False | False |
| COMPLETED | FAILURE | False | True | False | True | False |
| COMPLETED | TIMED_OUT | False | True | False | True | False |
| COMPLETED | ACTION_REQUIRED | False | True | False | True | False |
| COMPLETED | CANCELLED | False | True | False | False | True |
| COMPLETED | SKIPPED | False | True | False | False | False |
| COMPLETED | NEUTRAL | False | True | False | False | False |
| COMPLETED | STALE | False | True | False | False | False |

## Method Signatures and Logic

All methods added to `WorkflowRun` class:

```python
def is_running(self) -> bool:
    """Status in (IN_PROGRESS, WAITING, REQUESTED)."""
    return self.status in (WorkflowStatus.IN_PROGRESS, WorkflowStatus.WAITING, WorkflowStatus.REQUESTED)

def is_terminal(self) -> bool:
    """Status == COMPLETED."""
    return self.status == WorkflowStatus.COMPLETED

def is_successful(self) -> bool:
    """Status == COMPLETED and conclusion == SUCCESS."""
    return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.SUCCESS

def is_failed(self) -> bool:
    """Status == COMPLETED and conclusion in (FAILURE, TIMED_OUT, ACTION_REQUIRED)."""
    return (
        self.status == WorkflowStatus.COMPLETED 
        and self.conclusion in (
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.TIMED_OUT,
            WorkflowConclusion.ACTION_REQUIRED,
        )
    )

def is_cancelled(self) -> bool:
    """Status == COMPLETED and conclusion == CANCELLED."""
    return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.CANCELLED
```

## Files to Modify

1. **`src/models/workflow_run.py`** (MODIFY)
   - Add five state query methods to the WorkflowRun class
   - No changes to __post_init__, to_dict(), or from_dict()

2. **`tests/test_workflow_run_state.py`** (CREATE NEW)
   - Create comprehensive test module with ~60 parametrized test cases
   - Cover all enum combinations and mutual exclusivity invariants
   - Test helper to create runs with specific state combinations

## Test Coverage

Test categories:
- is_running() true cases: 3 tests (IN_PROGRESS, WAITING, REQUESTED)
- is_running() false cases: 10+ tests (QUEUED, PENDING, COMPLETED with all conclusions)
- is_terminal() true cases: 9 tests (COMPLETED with all conclusions)
- is_terminal() false cases: 5 tests (non-COMPLETED statuses)
- is_successful() true cases: 1 test (COMPLETED + SUCCESS)
- is_successful() false cases: 12+ tests (all other combinations)
- is_failed() true cases: 3 tests (FAILURE, TIMED_OUT, ACTION_REQUIRED)
- is_failed() false cases: 11+ tests (all other combinations)
- is_cancelled() true cases: 1 test (COMPLETED + CANCELLED)
- is_cancelled() false cases: 12+ tests (all other combinations)
- Mutual exclusivity: 4 tests (running ≠ terminal, successful ≠ failed, successful ≠ cancelled, failed ≠ cancelled)

## Implementation Order

1. Modify `src/models/workflow_run.py` — Add the five methods
2. Create `tests/test_workflow_run_state.py` — Implement all test cases

No validation in __post_init__ per task requirements (task says do NOT modify enum definitions and focuses on query method encapsulation).
