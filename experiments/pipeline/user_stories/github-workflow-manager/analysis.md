# Analysis: Add State-Checking Methods to WorkflowRun (Task 02)

## Task Summary

Implement encapsulated methods on the `WorkflowRun` class to check its execution state. Currently, state logic is scattered across potential consumers (services, CLI) who must directly inspect `status` and `conclusion` fields. This task consolidates state-checking logic into consistent, testable methods on the model itself.

## Current Implementation

### WorkflowRun Class Structure
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_run.py`

Current attributes:
- `status: WorkflowStatus` — current execution status (enum)
- `conclusion: Optional[WorkflowConclusion]` — final result (optional enum)

Current methods:
- `__post_init__()` — validates duration_seconds >= 0
- `to_dict()` — serializes to dictionary
- `from_dict()` — deserializes from dictionary

### WorkflowStatus Enum Values
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_status.py`

```
QUEUED = "queued"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
WAITING = "waiting"
REQUESTED = "requested"
PENDING = "pending"
```

### WorkflowConclusion Enum Values
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/github-workflow-manager/src/models/workflow_conclusion.py`

```
SUCCESS = "success"
FAILURE = "failure"
CANCELLED = "cancelled"
SKIPPED = "skipped"
TIMED_OUT = "timed_out"
ACTION_REQUIRED = "action_required"
NEUTRAL = "neutral"
STALE = "stale"
```

### Execution Lifecycle (from state diagram)

**Running states:** REQUESTED, PENDING, QUEUED, WAITING, IN_PROGRESS
- Characterization: Execution is active or queued, not yet terminal

**Terminal states:** COMPLETED
- Characterization: Execution has finished; a conclusion is available or will be set
- Subcases via conclusion:
  - SUCCESS → is_successful() = True
  - FAILURE → is_failed() = True
  - CANCELLED → is_cancelled() = True
  - SKIPPED → neither successful nor failed
  - TIMED_OUT → is_failed() = True (timeout is a failure mode)
  - ACTION_REQUIRED → neither successful nor failed
  - NEUTRAL → neither successful nor failed
  - STALE → neither successful nor failed

**Incomplete states (status not COMPLETED, conclusion is None):**
- REQUESTED, PENDING, QUEUED, WAITING, IN_PROGRESS → running or queued
- is_terminal() = False, is_running() = True

## Existing State-Checking Patterns in Codebase

### Search Results
Grep for "status" and related checks in src/:

1. **workflow_run_service.py:34** — `filter_by_status(status: WorkflowStatus)` method
   - Direct comparison: `r.status == status`
   - No encapsulated logic, just filters by exact enum match

2. **workflow_cli.py:90, 103** — Status/conclusion enum construction
   - `WorkflowStatus(ns.status)` and `WorkflowConclusion(ns.conclusion)`
   - No state derivation logic, only enum construction

3. **interactive_menu.py:53, 100, 104** — Similar enum construction
   - Menu displays status/conclusion choices; no state logic

**Finding:** No existing state-checking logic was found in the codebase. No duplication to consolidate, but logic may exist implicitly in future consumers.

## Acceptance Criteria Analysis

### Must Have (Task-Critical)
1. **Implement four methods:**
   - `is_terminal()` → True if status == COMPLETED
   - `is_successful()` → True if status == COMPLETED and conclusion == SUCCESS
   - `is_failed()` → True if status == COMPLETED and conclusion == FAILURE or TIMED_OUT
   - `is_running()` → True if status in (REQUESTED, PENDING, QUEUED, WAITING, IN_PROGRESS)

2. **Derive state strictly from status and conclusion fields**
   - No external parameters or dependencies
   - Pure functions based on enum values
   - No I/O or side effects

### Should Have (Quality Assurance)
1. **is_terminal() and is_running() mutually exclusive**
   - If is_terminal() is True, is_running() must be False
   - If is_running() is True, is_terminal() must be False
   - Only one can be True at any time

2. **is_successful() and is_failed() mutually exclusive**
   - If is_successful() is True, is_failed() must be False
   - If is_failed() is True, is_successful() must be False
   - A COMPLETED run can have conclusion values that make both False (SKIPPED, NEUTRAL, etc.)

3. **Unit tests covering all state combinations**
   - Test all status enum values
   - Test all conclusion enum values in COMPLETED state
   - Test None conclusion in non-COMPLETED states
   - Verify mutual exclusivity constraints

### Could Have (Optional/Bonus)
1. **is_cancelled() convenience method**
   - Derived from conclusion only: `conclusion == WorkflowConclusion.CANCELLED`
   - Independent of status field
   - Useful for clients checking cancellation specifically

### Won't Have (Out of Scope)
- Do not modify WorkflowStatus enum
- Do not modify WorkflowConclusion enum

## Proposed Implementation Details

### State Logic Definition

**is_terminal():**
```python
def is_terminal(self) -> bool:
    return self.status == WorkflowStatus.COMPLETED
```
Meaning: Execution has finished (status is COMPLETED), regardless of outcome.

**is_running():**
```python
def is_running(self) -> bool:
    return self.status in (
        WorkflowStatus.REQUESTED,
        WorkflowStatus.PENDING,
        WorkflowStatus.QUEUED,
        WorkflowStatus.WAITING,
        WorkflowStatus.IN_PROGRESS,
    )
```
Meaning: Execution is active, queued, or awaiting resources; not yet terminal.

**is_successful():**
```python
def is_successful(self) -> bool:
    return (
        self.status == WorkflowStatus.COMPLETED
        and self.conclusion == WorkflowConclusion.SUCCESS
    )
```
Meaning: Execution completed with a successful outcome.

**is_failed():**
```python
def is_failed(self) -> bool:
    return (
        self.status == WorkflowStatus.COMPLETED
        and self.conclusion in (
            WorkflowConclusion.FAILURE,
            WorkflowConclusion.TIMED_OUT,
        )
    )
```
Meaning: Execution completed with a failure outcome (including timeout).

**is_cancelled() (bonus):**
```python
def is_cancelled(self) -> bool:
    return self.conclusion == WorkflowConclusion.CANCELLED
```
Meaning: Execution was cancelled. Can be checked independently of status.

## Files That Need Modification

### Core Implementation (Required)
1. **`src/models/workflow_run.py`**
   - Add `is_terminal()` method
   - Add `is_running()` method
   - Add `is_successful()` method
   - Add `is_failed()` method
   - Add `is_cancelled()` method (bonus)
   - All methods are type-hinted to return `bool`
   - No parameters except self

### Tests (For Validation)
2. **`tests/test_workflow_run_service.py`** or new test file **`tests/test_workflow_run_state.py`**
   - Test is_terminal() across all status values
   - Test is_running() across all status values
   - Test is_successful() with COMPLETED + SUCCESS
   - Test is_failed() with COMPLETED + (FAILURE or TIMED_OUT)
   - Test is_cancelled() with all conclusion values
   - Verify mutual exclusivity of is_terminal() and is_running()
   - Verify mutual exclusivity of is_successful() and is_failed()
   - Edge case: COMPLETED with None conclusion (should not occur in practice)
   - Edge case: Non-COMPLETED with non-None conclusion (should not occur in practice)

### Optional Updates (For Integration)
3. **`src/cli/workflow_cli.py`** (optional enhancement)
   - Could use `run.is_terminal()` or `run.is_running()` in filtering/display logic
   - Not required by acceptance criteria but would demonstrate utility

4. **`artifacts/class_diagram.puml`** (documentation)
   - Update WorkflowRun class box to list new methods
   - Essential for keeping architecture diagram current

## State Transition Truth Table

| Status | Conclusion | is_terminal | is_running | is_successful | is_failed | is_cancelled |
|--------|-----------|-----------|-----------|---------------|-----------|--------------|
| REQUESTED | None | False | True | False | False | False |
| PENDING | None | False | True | False | False | False |
| QUEUED | None | False | True | False | False | False |
| WAITING | None | False | True | False | False | False |
| IN_PROGRESS | None | False | True | False | False | False |
| COMPLETED | SUCCESS | True | False | True | False | False |
| COMPLETED | FAILURE | True | False | False | True | False |
| COMPLETED | TIMED_OUT | True | False | False | True | False |
| COMPLETED | CANCELLED | True | False | False | False | True |
| COMPLETED | SKIPPED | True | False | False | False | False |
| COMPLETED | ACTION_REQUIRED | True | False | False | False | False |
| COMPLETED | NEUTRAL | True | False | False | False | False |
| COMPLETED | STALE | True | False | False | False | False |

**Key observations:**
- is_terminal and is_running are always opposite (mutually exclusive)
- is_successful and is_failed are mutually exclusive (both False for SKIPPED, ACTION_REQUIRED, NEUTRAL, STALE)
- is_cancelled is independent and orthogonal to other checks

## Summary

**Task scope:** Add 4 required + 1 bonus state-checking method to WorkflowRun

**Affected files:**
- Core: 1 file (src/models/workflow_run.py)
- Tests: 1 file (tests/test_workflow_run_state.py, new or append to existing)
- Diagrams: 1 file (artifacts/class_diagram.puml, optional but recommended)

**Implementation complexity:** Low
- Simple boolean logic based on enum comparisons
- No new dependencies or external state
- Pure functions, fully testable

**Risk level:** Very Low
- Adding new methods to existing class
- No modifications to enums or existing methods
- Backward compatible (purely additive)

**Test coverage needs:**
- All 5 status values + is_running test cases (5 tests)
- 8 possible conclusion values in COMPLETED state + is_successful/is_failed tests (8 tests)
- Mutual exclusivity verification (2 tests)
- is_cancelled bonus coverage (1 test)
- Edge cases (2 tests)
- Estimated: 12-15 test cases minimum

