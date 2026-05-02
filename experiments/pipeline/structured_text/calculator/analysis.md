# Task 04 Analysis: Add MemoryService for managing MemoryEntry

## Task Summary

Implement `MemoryService` to manage `MemoryEntry` objects with basic operations (store, retrieve), ensuring integration with the calculation flow. The service must:

**Must:**
- Implement MemoryService to manage MemoryEntry objects with basic operations (store, retrieve)
- Ensure integration with calculation flow
- Service responsibilities limited to MemoryEntry lifecycle management (store/retrieve)
- Keep storage implementation separate from service

**Should:**
- Service responsibilities limited to MemoryEntry lifecycle management
- Storage implementation must stay separate

**Could:**
- Add filtering/querying capabilities (later task)

**Won't:**
- Place persistence implementation inside service class

---

## Current State: Existing Architecture

### 1. Domain Models

#### MemoryEntry (src/models/memory_entry.py)
**Status:** Already implemented in Task 03

A dataclass representing a stored calculation attempt (successful or failed):
- Fields: `operation` (str), `operand_a` (float), `operand_b` (float), `result` (float | None), `success` (bool), `error_message` (str | None), `timestamp` (str, ISO 8601), `execution_time_ms` (float), `entry_id` (str)
- Auto-generates timestamp if missing
- Auto-generates entry_id (UUID) if not provided
- Validates state consistency: if `success=True`, result must not be None; if `success=False`, error_message must not be None
- Methods: `to_dict()` and `from_dict()` with backward compatibility (treats missing success/error_message as success=True/None)
- `__str__()` for debugging (not display)

#### CalculationResult (src/models/calculation_result.py)
**Status:** Pre-existing, represents only successful calculations
- Fields: `operation` (str), `operand_a` (float), `operand_b` (float), `result` (float), `timestamp` (str), `execution_time_ms` (float)
- Does NOT support error state
- Used by existing code (CLI, storage, tests)

#### Operation (src/models/operation.py)
**Status:** Existing enum with 8 operations: ADD, SUBTRACT, MULTIPLY, DIVIDE, SQUARE, SQRT, POWER, MODULO

### 2. Services (Current)

#### Calculator (src/services/calculator.py)
**Status:** Pre-existing, pure arithmetic engine
- Methods: `add()`, `subtract()`, `multiply()`, `divide()`, `square()`, `sqrt()`, `power()`, `modulo()`, `calculate(operation, a, b)`
- Raises ValueError on error (division by zero, negative sqrt, modulo by zero)

#### CalculatorService (src/services/calculator_service.py)
**Status:** Pre-existing orchestration layer
- Current responsibilities:
  - Measures execution time with `time.perf_counter()`
  - Delegates arithmetic to Calculator
  - Creates CalculationResult
  - Persists via JsonStorage
  - Retrieves history via JsonStorage
- Current signature:
  - `__init__(calculator: Calculator, storage: JsonStorage)`
  - `perform(operation: Operation, a: float, b: float) -> CalculationResult`
  - `get_history() -> list[CalculationResult]`
- **Critical gap:** Does NOT catch exceptions; errors propagate to CLI and are never persisted

### 3. Storage

#### JsonStorage (src/storage/json_storage.py)
**Status:** Pre-existing, handles persistence
- Persists to artifacts/calculations.json
- Methods: `save(result: CalculationResult)`, `load_all() -> list[CalculationResult]`
- Handles missing files, corrupted JSON, backward compatibility
- Current contract: accepts CalculationResult, returns list[CalculationResult]

### 4. CLI Integration

#### CalculatorCLI (src/cli/calculator_cli.py)
**Status:** Pre-existing user interface
- `run_interactive()` → Interactive menu
- `run_command(operation_str, a, b)` → Single calculation
- `_show_history()` → Displays results from CalculatorService.get_history()
- Does NOT display error states (because CalculationService never persists them)

---

## Key Findings: What Must Change

### 1. MemoryService Does NOT Yet Exist
**Finding:** There is no `src/services/memory_service.py` file.
- MemoryService must be created with basic operations for MemoryEntry lifecycle.

### 2. No Service Manages MemoryEntry Currently
**Finding:** MemoryEntry dataclass exists but is never instantiated or persisted by any service.
- MemoryEntry is a well-designed domain model but unused
- No service bridges MemoryEntry and storage

### 3. Parallel Class Hierarchy Exists
**Finding:** Two separate result classes designed to coexist:
- **CalculationResult** → represents successful calculations (existing, legacy)
- **MemoryEntry** → represents all calculations including failures (new capability)
- Both have similar fields but different semantics
- Both have serialization support

### 4. Storage Abstraction Needed
**Finding:** JsonStorage is tightly coupled to CalculationResult.
- Current: `save(result: CalculationResult)` expects CalculationResult
- Current: `load_all()` returns list[CalculationResult]
- Task requires storage to remain separate from service
- **Decision point:** Does MemoryService use JsonStorage directly, or a new MemoryEntryStorage?

### 5. Error Handling Not Yet Integrated
**Finding:** Calculator throws errors; CalculatorService does not catch them.
- Example: `test_perform_divide_by_zero_does_not_save()` verifies errors don't persist
- This is intentional design (current system = success-only)
- MemoryService would enable error persistence but integration comes later

---

## Integration Points: How MemoryService Fits

### Current Calculation Flow
```
User Input (CLI)
  ↓
CalculatorCLI.run_interactive() / run_command()
  ↓
CalculatorService.perform(operation, a, b)
  ↓
Calculator.calculate(operation, a, b) → float (may raise ValueError)
  ↓
Creates CalculationResult
  ↓
JsonStorage.save(CalculationResult)
  ↓
artifacts/calculations.json
```

### Proposed MemoryService Role (Task 04)
**MemoryService will manage MemoryEntry lifecycle:**
- Store MemoryEntry objects (delegate persistence to storage)
- Retrieve stored MemoryEntry objects (delegate loading to storage)
- NOT responsible for: arithmetic, error catching, timestamp generation (those stay where they are)

### Future Integration (Not in Task 04 but visible in code structure)
Future tasks will likely:
1. CalculatorService catches errors from Calculator.calculate()
2. CalculatorService creates MemoryEntry (success or failed state)
3. MemoryService stores it via storage
4. CLI displays error entries from MemoryService history

---

## Requirements Analysis: MoSCoW Breakdown

### Must (Non-negotiable)

1. **MemoryService class exists**
   - File: `src/services/memory_service.py`
   - Can be instantiated
   
2. **Basic store operation**
   - Method: `store(entry: MemoryEntry) -> None` (or similar name)
   - Accepts a MemoryEntry
   - Delegates to storage layer

3. **Basic retrieve operation**
   - Method: `get_all() -> list[MemoryEntry]` (or similar name)
   - Returns list of MemoryEntry objects
   - Delegates to storage layer

4. **Integration with calculation flow**
   - Must be ready to accept MemoryEntry objects from CalculatorService (in future)
   - Must work with existing storage infrastructure
   - Tests must pass

### Should (Strongly Expected)

1. **Limited responsibilities**
   - Service ONLY manages MemoryEntry lifecycle (create/retrieve patterns)
   - Does NOT implement persistence logic
   - Does NOT implement business logic (arithmetic, validation)
   - Clear separation of concerns

2. **Storage stays separate**
   - Persistence logic in storage layer (JsonStorage or new MemoryEntryStorage)
   - MemoryService depends on storage abstraction
   - Service injects storage via constructor

3. **Backward compatibility**
   - MemoryEntry.from_dict() already handles old CalculationResult format
   - Storage layer must load old JSON correctly
   - Existing tests must still pass

### Could (Enhancement, Out of Scope)

1. **Filtering/querying** → Later task
2. **Get by ID** → Later task
3. **Delete/update** → Later task

### Won't

1. Persistence implementation inside MemoryService
2. Business logic inside MemoryService

---

## Ambiguities & Working Assumptions

### 1. Storage Abstraction Question
**Ambiguity:** Should MemoryService use JsonStorage directly or a new MemoryEntryStorage?

**Evidence:**
- JsonStorage is type-hinted for CalculationResult
- Task says "storage implementation must stay separate" (implies new abstraction)
- MemoryEntry and CalculationResult are separate classes

**Working Assumption:** 
- Either:
  - (A) Create MemoryEntryStorage class (new file, parallel to JsonStorage)
  - (B) Make JsonStorage generic/overloaded to accept both types
  - (C) Create a shared base class or interface
- Most likely: (A) or (C) to maintain clean separation
- Will be clarified by system-architect design

### 2. Method Naming
**Ambiguity:** What should basic operations be called?

**Evidence:**
- Task says "store, retrieve" (generic)
- CalculatorService uses `perform()` (domain-specific)
- JsonStorage uses `save()` and `load_all()` (low-level)

**Working Assumption:**
- Likely names: `store(entry: MemoryEntry)` and `get_all()` or `retrieve_all()` or `load_all()`
- More specific query methods (get_by_id, filter_by_success) come later

### 3. Constructor Signature
**Ambiguity:** What dependencies does MemoryService take?

**Evidence:**
- CalculatorService: `__init__(calculator, storage)`
- Pattern: receive dependencies via constructor

**Working Assumption:**
- MemoryService takes storage as a dependency:
  - `__init__(self, storage: JsonStorage)` or
  - `__init__(self, storage: MemoryEntryStorage)` or
  - `__init__(self, storage: StorageInterface)`
- Constructor injection pattern already established

### 4. Error Handling in Service
**Ambiguity:** Should MemoryService catch storage exceptions?

**Evidence:**
- JsonStorage handles missing files gracefully (returns [])
- JsonStorage handles corrupted JSON (returns [])
- Existing code doesn't explicitly handle exceptions from storage

**Working Assumption:**
- MemoryService delegates error handling to storage layer
- Storage layer returns safe defaults or raises explicitly
- Service responsibility: propagate storage state to caller

---

## Scope Signals: What's Clearly In/Out

### Clearly IN
- MemoryService class with basic operations
- Store (persist) MemoryEntry
- Retrieve (load) MemoryEntry objects
- Use dependency injection for storage
- Tests for MemoryService
- Update diagrams to show MemoryService

### Clearly OUT (Later Tasks)
- Error catching in CalculatorService
- Creating MemoryEntry from failed calculations
- Displaying error states in CLI
- Complex querying (filter by success, by date range, etc.)
- Updating CalculatorService.perform() to use MemoryService
- Integration test between CalculatorService and MemoryService

### Borderline (Need Design Input)
- New storage class vs. existing JsonStorage refactoring
- Exact method signatures and names
- Whether MemoryService updates CalculatorService constructor
- Whether new storage file or shared with CalculationResult

---

## Existing Code Dependencies

### Files that Import MemoryEntry (as of Task 03)
- `tests/test_memory_entry.py` — 22 comprehensive tests
- `src/models/__init__.py` — exports MemoryEntry

### Files that Could Depend on MemoryService (not yet)
- `src/services/__init__.py` — may export MemoryService
- Future: `src/services/calculator_service.py` (in later task)
- Future: `src/cli/calculator_cli.py` (for displaying memory)
- Tests: `tests/test_memory_service.py` (to be created)

### Files NOT to Modify (Task 03 already did this)
- `src/models/memory_entry.py` — already complete
- `tests/test_memory_entry.py` — already complete

---

## Test Coverage Expectations

Based on existing patterns (test_calculator_service.py, test_memory_entry.py), tests should cover:

### Basic Operations (Must)
1. Store a single MemoryEntry
2. Retrieve empty list when nothing stored
3. Retrieve multiple entries in order
4. Entry contents are preserved after store/retrieve

### Integration (Should)
5. Works with successful MemoryEntry
6. Works with failed MemoryEntry (success=False)
7. Works with backward-compatible old CalculationResult format
8. Entry ID is preserved
9. Timestamp is preserved

### Error Cases (Could)
10. Storage exceptions propagate (or handled gracefully)

---

## Files Involved

### To Create
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/services/memory_service.py` (NEW)
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_memory_service.py` (NEW)
- Possibly: `src/storage/memory_entry_storage.py` (if new storage abstraction is chosen)

### To Modify
- `src/services/__init__.py` — export MemoryService
- `artifacts/class_diagram.puml` — add MemoryService
- `artifacts/component_diagram.puml` — add MemoryService component
- Possibly: `src/storage/__init__.py` — export new storage if created

### To Review (but not modify yet)
- `src/storage/json_storage.py` — understand current persistence
- `src/models/memory_entry.py` — already correct, no changes needed
- `src/services/calculator_service.py` — no changes yet (integration in Task 05)

---

## Key Constraints

1. **Storage stays separate** — MemoryService must not contain JSON/file logic
2. **MemoryEntry already valid** — Don't modify Task 03 implementation
3. **Backward compatibility** — Old CalculationResult JSON must still load correctly
4. **Existing tests must pass** — 109 tests from Tasks 01-03 cannot break
5. **Clean separation** — MemoryService focuses only on lifecycle, not business logic

---

## Specific Requirements for MemoryService Based on MoSCoW

### Must: Implement MemoryService Class
**Location:** `src/services/memory_service.py`
**Minimum Interface:**
```python
class MemoryService:
    def __init__(self, storage):  # storage: JsonStorage or MemoryEntryStorage
        ...
    
    def store(self, entry: MemoryEntry) -> None:
        """Persist a MemoryEntry to storage."""
        ...
    
    def get_all(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects."""
        ...
```

### Must: Integration with Calculation Flow
**What exists:**
- CalculatorService currently persists CalculationResult to JsonStorage
- MemoryEntry is a new model designed to replace/augment this

**What's needed:**
- MemoryService must be ready to receive MemoryEntry from CalculatorService (later)
- MemoryService must persist to storage (storage layer handles format)
- MemoryService must retrieve from storage (storage layer handles parsing)

### Should: Separate Concerns
**Service responsibilities:** Lifecycle operations only (store, retrieve)
**Storage responsibilities:** Persistence logic (read/write JSON, backward compatibility)
**Business logic:** Stays with Calculator and CalculatorService

### Should: Storage Implementation Separate
**Pattern to follow:**
```python
# MemoryService delegates to storage
class MemoryService:
    def __init__(self, storage):
        self.storage = storage
    
    def store(self, entry: MemoryEntry):
        self.storage.save(entry)  # Storage knows HOW to persist
    
    def get_all(self):
        return self.storage.load_all()  # Storage knows HOW to load
```

