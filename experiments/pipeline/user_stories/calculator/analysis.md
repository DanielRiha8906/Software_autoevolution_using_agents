# Task 09: Calculator Refactoring Analysis

## What the Task is Asking For

Refactor the calculator codebase to separate three distinct layers:
1. **Calculation Engine** — pure arithmetic logic, no side effects
2. **Memory/History Management** — persistence and retrieval of calculations
3. **Interface** — CLI and user interaction

Each layer must have clearly defined boundaries with minimal coupling, using abstract base classes or protocols to decouple them. All external behavior must be preserved (public interfaces, return types, side effects unchanged). Domain logic is reorganized, not rewritten. The refactored code must behave identically to the current code: `python -m src` must produce the same output and behavior.

---

## Current Architecture Overview

The calculator is already loosely layered, but responsibilities are mixed throughout and coupling is implicit (no protocols/abstractions).

### Current Structure (by file):

**Models (`src/models/`):**
- `operation.py` — Enum of 14 operations (add, subtract, multiply, etc.)
- `memory_entry.py` — Dataclass storing calculation result with metadata (operation, operands, result, error, timestamp, UUID, execution time)
- `calculation_result.py` — Legacy dataclass, similar to MemoryEntry but without error tracking; retained for compatibility
- `statistics.py` — Dataclass holding aggregated metrics (total_calculations, total_errors, error_rate_percent, operations_count, average_execution_time_ms)

**Services (`src/services/`):**
- `calculator.py` — **Calculation Engine**: 14 methods (add, subtract, multiply, etc.) + dispatch via `calculate(operation, a, b)`
- `calculator_service.py` — **Orchestrator**: wraps Calculator + MemoryService; performs operations and saves results via MemoryService
- `memory_service.py` — **Memory/History Layer**: abstracts JsonStorage; provides store/retrieve/filter methods
- `statistics_service.py` — **Statistics Engine**: consumes MemoryService; computes aggregated metrics
- `import_export_service.py` — **Import/Export Logic**: validates and imports/exports history via MemoryService; directly accesses MemoryService.storage._write_raw() for "replace" mode

**Storage (`src/storage/`):**
- `json_storage.py` — **Persistence Layer**: read/write MemoryEntry objects to/from JSON file

**CLI (`src/cli/`):**
- `calculator_cli.py` — **User Interface**: interactive menu + one-shot mode; depends on CalculatorService, StatisticsService, ImportExportService

**Entry Point:**
- `__main__.py` — Bootstraps services, wires dependencies, routes user commands to CLI

### Dependency Graph (Current):

```
__main__ creates:
  ├─ Calculator (calculation engine)
  ├─ JsonStorage (persistence)
  ├─ MemoryService (memory/history abstraction)
  ├─ CalculatorService (calculator + memory orchestration)
  ├─ StatisticsService (memory → statistics)
  ├─ ImportExportService (memory ↔ file I/O)
  └─ CalculatorCLI (all services)

Call chains:
  CLI → CalculatorService → Calculator + MemoryService → JsonStorage
  CLI → StatisticsService → MemoryService → JsonStorage
  CLI → ImportExportService → MemoryService → JsonStorage (+ direct _write_raw access)
```

---

## How Responsibilities Are Currently Mixed

### 1. CalculatorService (Lines 1-56 in calculator_service.py)

**Current role:** Acts as both orchestrator AND entry point for history filtering.
- Lines 12-33: Performs calculation (delegates to Calculator) and records result (delegates to MemoryService)
- Lines 38-55: Delegates filtering to MemoryService

**Problem:** CalculatorService is a facade with no clear separation of concerns:
- It knows about Calculator
- It knows about MemoryService and its filtering API
- It knows about MemoryEntry model (creates instances)
- It knows about Operation enum

If you change how calculations are persisted, CalculatorService must change.
If you change the filtering API, CalculatorService must change.

### 2. MemoryService (Lines 1-122 in memory_service.py)

**Current role:** Both memory abstraction AND filtering logic.
- Lines 9-13: Store/retrieve interface (pure abstraction)
- Lines 15-36: Single-operation filtering
- Lines 37-71: State filtering (success/error/both)
- Lines 73-121: Combined filtering (operations + state)

**Problem:** Filtering logic is tightly coupled to MemoryService:
- StatisticsService, ImportExportService, and CalculatorService all depend on MemoryService.filter() interface
- If you want to change filtering strategy (e.g., add timestamp range filtering), you modify MemoryService
- Filtering is stateless utility logic, not memory management

### 3. ImportExportService (Lines 1-281 in import_export_service.py)

**Current role:** Import/Export + Validation + Duplicate Detection + Storage Manipulation
- Lines 27-71: Export to JSON
- Lines 73-174: Import from JSON + validation + duplicate detection
- Lines 176-250: Entry validation
- Lines 252-280: Duplicate detection
- **Line 129:** Directly accesses MemoryService.storage._write_raw([]) to clear history in "replace" mode

**Problem:** High coupling to MemoryService internals:
- Direct access to private `_write_raw()` method (line 129) violates encapsulation
- Mixes validation (domain logic) with persistence (I/O)
- Duplicate detection is tightly coupled to MemoryEntry structure
- If JsonStorage changes, ImportExportService breaks

### 4. CalculatorCLI (Lines 1-324 in calculator_cli.py)

**Current role:** User interface AND business logic dispatcher
- Lines 43-96: Interactive loop + menu rendering
- Lines 98-110: One-shot command execution
- Lines 144-155: History display (formats MemoryEntry)
- Lines 157-248: Filtering UI (prompts) + display
- Lines 250-266: Statistics display (formats CalculationStatistics)
- Lines 268-313: Import/Export UI (prompts) + result display

**Problem:** CLI knows too much:
- Knows about MemoryEntry structure (formatting on lines 152, 154, 245)
- Knows about CalculationStatistics structure (display on lines 255-265)
- Knows about filtering API (operations/state parameters)
- Directly calls private CLI methods from __main__.py (e.g., `cli._show_history()`)

### 5. JsonStorage (Lines 1-33 in json_storage.py)

**Current role:** Persistence + Serialization
- Lines 11-14: Save (read all, append, write all)
- Lines 16-17: Load (read, deserialize)
- Lines 19-27: Low-level read
- Lines 29-32: Low-level write

**Problem:** No abstraction for storage strategy:
- If you want to switch to a database or cloud storage, you must rewrite all dependent code
- MemoryService and ImportExportService are tightly coupled to JsonStorage via direct `_read_raw()` / `_write_raw()` access
- No interface contract; just concrete implementation

---

## What Needs to Be Separated

### Layer 1: Calculation Engine

**Keep as-is (already isolated):**
- `src/services/calculator.py` — pure arithmetic, no I/O or state

**Status:** Already decoupled. Depends on Operation enum only. No changes needed unless you want to add a protocol for pluggable calculation strategies.

---

### Layer 2: Memory/History Management

**Current state:** Mixed across three classes:
- MemoryService (abstract interface + filtering logic)
- JsonStorage (persistence implementation)
- ImportExportService (filtering, validation, persistence manipulation)

**To be separated into:**

1. **Storage Interface (new protocol)**
   - Abstract contract: save(entry), load_all() → list[MemoryEntry]
   - Concrete: JsonStorage implements this
   - Purpose: Allow swapping storage backends without changing MemoryService

2. **Memory Service (refactored)**
   - Core responsibility: store/retrieve MemoryEntry objects
   - Remove: All filtering logic (move to a separate Filtering service)
   - Keep: store(entry), retrieve() → only those two methods
   - Delegate: Filtering to a new HistoryFilter abstraction

3. **History Filter (new abstraction)**
   - Abstract contract: filter(entries: list[MemoryEntry], ...) → list[MemoryEntry]
   - Concrete implementations:
     - OperationFilter — by operation name(s)
     - StateFilter — by success/error
     - CompositeFilter — chain multiple filters
   - Purpose: Decouple filtering from memory storage

4. **Import/Export Service (refactored)**
   - Remove: Direct access to MemoryService.storage._write_raw()
   - Add: Method to MemoryService to clear history (e.g., clear())
   - Keep: Validation, duplicate detection, file I/O
   - Depend on: MemoryService interface, not JsonStorage private methods

---

### Layer 3: Interface (CLI)

**Current state:** Mixed across CalculatorCLI and __main__.py:
- CalculatorCLI knows about MemoryEntry, CalculationStatistics structures
- __main__.py directly calls private CLI methods (_show_history, _show_statistics)

**To be separated into:**

1. **Output Formatter (new abstraction)**
   - Abstract contract: format(data: T) → str
   - Concrete implementations:
     - MemoryEntryFormatter — formats a single MemoryEntry
     - MemoryEntryListFormatter — formats a list of entries
     - StatisticsFormatter — formats CalculationStatistics
     - ImportResultFormatter — formats import result dict
   - Purpose: Decouple view logic from domain model

2. **Command Handler (new abstraction)**
   - Abstract contract: execute() → None
   - Concrete implementations:
     - CalculateCommand — perform a calculation
     - HistoryCommand — display history
     - FilterCommand — display filtered history
     - StatisticsCommand — display statistics
     - ExportCommand — export history
     - ImportCommand — import history
   - Purpose: Route CLI commands without embedding logic in CalculatorCLI

3. **CLI (refactored CalculatorCLI)**
   - Responsibility: Menu rendering + input prompts only
   - Remove: Logic for formatting, service calls, result display
   - Delegate to: Command handlers and formatters
   - Keep: Interactive loop, menu structure

---

## Proposed Layer Boundaries

### Separation Strategy:

**LAYER 1: Calculation Engine**
```
src/services/calculator.py (no changes)
  ├─ Pure functions (add, subtract, multiply, etc.)
  ├─ Dispatch logic (calculate → operation → function)
  └─ No dependencies except Operation enum
```

**LAYER 2: Memory/History Management**
```
src/storage/ (new interface + impl)
  ├─ storage.py (new): StorageBackend protocol
  │  └─ contract: save(entry), load_all()
  └─ json_storage.py (refactored): implements StorageBackend

src/services/memory/ (new package)
  ├─ memory_service.py (refactored): store/retrieve only
  ├─ history_filter.py (new): HistoryFilter protocol + implementations
  │  ├─ OperationFilter
  │  ├─ StateFilter
  │  └─ CompositeFilter
  └─ __init__.py: exports

src/services/import_export_service.py (refactored)
  ├─ Remove: MemoryService.storage._write_raw() access
  ├─ Add: Use MemoryService.clear() or similar
  └─ Depends on: MemoryService interface (not JsonStorage)
```

**LAYER 3: Interface**
```
src/cli/ (refactored)
  ├─ calculator_cli.py (refactored): Menu + prompts only
  ├─ formatters/ (new package)
  │  ├─ output_formatter.py: OutputFormatter protocol
  │  ├─ memory_entry_formatter.py: MemoryEntryFormatter
  │  ├─ statistics_formatter.py: StatisticsFormatter
  │  └─ __init__.py: exports
  ├─ commands/ (new package)
  │  ├─ command.py: Command protocol
  │  ├─ calculate_command.py: CalculateCommand
  │  ├─ history_command.py: HistoryCommand
  │  ├─ filter_command.py: FilterCommand
  │  ├─ statistics_command.py: StatisticsCommand
  │  ├─ export_command.py: ExportCommand
  │  ├─ import_command.py: ImportCommand
  │  └─ __init__.py: exports
  └─ __init__.py: exports

src/__main__.py (refactored)
  └─ Routes args to Command handlers (not directly to CLI methods)
```

---

## Coupling Points That Need Protocols/Abstractions

### 1. Storage Backend Abstraction

**Current coupling:**
```python
# src/services/memory_service.py
from ..storage.json_storage import JsonStorage  # Hard dependency

class MemoryService:
    def __init__(self, storage: JsonStorage) -> None:  # Concrete type!
        self.storage = storage
```

**Proposed abstraction:**
```python
# src/storage/storage.py (new)
from abc import ABC, abstractmethod
from ..models.memory_entry import MemoryEntry

class StorageBackend(ABC):
    @abstractmethod
    def save(self, entry: MemoryEntry) -> None:
        """Persist a single entry."""
    
    @abstractmethod
    def load_all(self) -> list[MemoryEntry]:
        """Load all entries."""

# src/services/memory_service.py (refactored)
from ..storage.storage import StorageBackend

class MemoryService:
    def __init__(self, storage: StorageBackend) -> None:  # Protocol, not concrete!
        self.storage = storage
```

**Impact:**
- JsonStorage implements StorageBackend
- ImportExportService can no longer access MemoryService.storage._write_raw()
- Any storage backend (database, cloud) can be swapped in

---

### 2. History Filter Abstraction

**Current coupling:**
```python
# src/services/memory_service.py
class MemoryService:
    def filter_by_operation(self, operation_name: str) -> list[MemoryEntry]:
        # Filter logic tightly coupled to MemoryService
        return [entry for entry in self.retrieve() if entry.operation == operation_name]
    
    def filter_by_state(self, state: str) -> list[MemoryEntry]:
        # More filter logic here
        ...
    
    def filter(self, operations: list[str] | None, state: str | None) -> list[MemoryEntry]:
        # Combined filter logic here
        ...
```

**Proposed abstraction:**
```python
# src/services/memory/history_filter.py (new)
from abc import ABC, abstractmethod
from ...models.memory_entry import MemoryEntry

class HistoryFilter(ABC):
    @abstractmethod
    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        """Filter a list of entries."""

class OperationFilter(HistoryFilter):
    def __init__(self, operations: list[str]):
        self.operations = operations
    
    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        return [e for e in entries if e.operation in self.operations]

class StateFilter(HistoryFilter):
    def __init__(self, state: str):
        self.state = state
    
    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        # State filtering logic here

class CompositeFilter(HistoryFilter):
    def __init__(self, filters: list[HistoryFilter]):
        self.filters = filters
    
    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        result = entries
        for f in self.filters:
            result = f.apply(result)
        return result

# src/services/memory_service.py (refactored)
class MemoryService:
    def filter(self, filter: HistoryFilter) -> list[MemoryEntry]:
        return filter.apply(self.retrieve())
```

**Impact:**
- MemoryService no longer knows about filtering strategies
- CalculatorService creates filters and passes them to MemoryService
- CLI creates filters based on user input
- New filter types can be added without changing MemoryService

---

### 3. Output Formatter Abstraction

**Current coupling:**
```python
# src/cli/calculator_cli.py
class CalculatorCLI:
    def _show_history(self) -> None:
        # Directly formats MemoryEntry
        print(f"  {i}. {entry}  [{entry.timestamp}]")
    
    def _show_statistics(self) -> None:
        # Directly formats CalculationStatistics
        print(f"  Total Calculations: {stats.total_calculations}")
        print(f"  Error Rate: {stats.error_rate_percent}%")
        # More formatting here
```

**Proposed abstraction:**
```python
# src/cli/formatters/output_formatter.py (new)
from abc import ABC, abstractmethod

class OutputFormatter(ABC):
    @abstractmethod
    def format(self, data) -> str:
        """Format data into a string."""

# src/cli/formatters/memory_entry_formatter.py (new)
from ...models.memory_entry import MemoryEntry

class MemoryEntryFormatter(OutputFormatter):
    def format(self, entry: MemoryEntry) -> str:
        return f"{entry}  [{entry.timestamp}]"

class MemoryEntryListFormatter(OutputFormatter):
    def __init__(self, formatter: MemoryEntryFormatter):
        self.formatter = formatter
    
    def format(self, entries: list[MemoryEntry]) -> str:
        lines = []
        for i, entry in enumerate(entries, 1):
            lines.append(f"  {i}. {self.formatter.format(entry)}")
        return "\n".join(lines)

# src/cli/formatters/statistics_formatter.py (new)
from ...models.statistics import CalculationStatistics

class StatisticsFormatter(OutputFormatter):
    def format(self, stats: CalculationStatistics) -> str:
        lines = [
            "  === Calculation Statistics ===",
            f"  Total Calculations: {stats.total_calculations}",
            f"  Error Rate: {stats.error_rate_percent}%",
            # More formatting here
        ]
        return "\n".join(lines)

# src/cli/calculator_cli.py (refactored)
class CalculatorCLI:
    def __init__(self, ..., formatters: dict):
        self.formatters = formatters
    
    def _show_history(self) -> None:
        history = self.service.get_history()
        output = self.formatters['entries'].format(history)
        print(output)
```

**Impact:**
- CLI doesn't know about MemoryEntry/CalculationStatistics structure
- Formatting can be changed without touching CLI
- Formatters can be reused by other interfaces (API, GUI)

---

## Circular Dependencies (Current & Risk)

### Identified Circular Dependencies: NONE

The codebase has a clear dependency hierarchy:
```
Models ← Services ← CLI
  ↓        ↓
Storage ←─┘
```

**Why no circularity?**
- Models define Operation, MemoryEntry, CalculationStatistics (no dependencies)
- Services depend on Models and Storage
- Storage depends on Models
- CLI depends on Models and Services
- No service depends on CLI

**After refactoring:** Maintain this acyclic structure. Protocols allow:
- MemoryService depends on StorageBackend (protocol, not JsonStorage)
- CLI depends on HistoryFilter (protocol, not MemoryService)
- This eliminates concrete coupling while preserving logical flow

---

## Risk Assessment — What Could Break

### 1. **Breaking Change: ImportExportService.import_history() "replace" mode**

**Current code (line 129):**
```python
if mode == "replace":
    self.memory_service.storage._write_raw([])
```

**Risk:** Accesses private method `_write_raw()`, violating encapsulation.

**Fix:** Add a public method to MemoryService:
```python
class MemoryService:
    def clear(self) -> None:
        """Clear all history."""
        self.storage.save_all([])  # New method on StorageBackend
```

**Test impact:** Existing test `test_import_replace_mode` must verify MemoryService.clear() is called, not _write_raw().

---

### 2. **Breaking Change: MemoryService.filter() API**

**Current code:**
```python
class MemoryService:
    def filter(self, operations: list[str] | None, state: str | None) -> list[MemoryEntry]:
        # Complex filtering logic
```

**Risk:** 35+ lines of filtering logic spread across three methods (filter_by_operation, filter_by_state, filter).

**Proposed API:**
```python
class MemoryService:
    def filter(self, filters: list[HistoryFilter] | None) -> list[MemoryEntry]:
        if not filters:
            return self.retrieve()
        result = self.retrieve()
        for f in filters:
            result = f.apply(result)
        return result
```

**Callers affected:**
- CalculatorService.filter_history() — must build filters from (operations, state)
- CalculatorCLI — must build filters from user input

**Test impact:**
- test_calculator_service.py: filter_history() still works (internal change)
- test_memory_service.py: filter() API changes, tests need updating
- test_filtering.py: Tests may need refactoring to use filter objects

---

### 3. **Breaking Change: CalculatorCLI API**

**Current code:**
```python
class CalculatorCLI:
    def _show_history(self) -> None:
        # Called by __main__.py
        history = self.service.get_history()
        # Formatting logic here
    
    def _show_statistics(self) -> None:
        # Called by __main__.py
        stats = self.statistics_service.calculate_statistics()
        # Formatting logic here
```

**Risk:** __main__.py (line 123, 130) directly calls private CLI methods. These methods will move to Command objects.

**Solution:**
```python
# src/cli/commands/history_command.py (new)
class HistoryCommand:
    def __init__(self, memory_service, formatter):
        self.memory_service = memory_service
        self.formatter = formatter
    
    def execute(self) -> None:
        history = self.memory_service.retrieve()
        output = self.formatter.format(history)
        print(output)

# src/__main__.py (refactored)
cmd = HistoryCommand(memory_service, memory_entry_list_formatter)
cmd.execute()
```

**Test impact:**
- test_cli.py: Many tests directly call _show_* methods
- Must add tests for Command objects
- CLI tests will shrink (no more logic testing)

---

### 4. **Data Loss: JsonStorage.save() behavior**

**Current code:**
```python
class JsonStorage:
    def save(self, result: MemoryEntry) -> None:
        records = self._read_raw()
        records.append(result.to_dict())
        self._write_raw(records)  # Atomic write
```

**Risk:** If storage refactoring adds a `save_all()` method, wrong implementation could lose data.

**Safe approach:**
- Keep existing `save()` exactly as-is
- Add new `save_all(entries: list[MemoryEntry])` for bulk operations
- Never remove or rename existing methods

---

### 5. **Silent Behavior Change: Filter Composition**

**Current code:**
```python
# Order of filtering is implicit
history = self.memory_service.retrieve()
history = [e for e in history if e.operation in operations]  # Filter 1
history = [e for e in history if (result is not None) == (state == 'success')]  # Filter 2
```

**Risk:** Refactored CompositeFilter might apply filters in wrong order.

**Safe approach:**
```python
class CompositeFilter(HistoryFilter):
    def __init__(self, filters: list[HistoryFilter]):
        self.filters = filters
    
    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        result = entries
        for f in self.filters:
            result = f.apply(result)  # Sequential, order matters
        return result
```

**Test requirement:** test_filtering.py must verify order independence (filters should commute).

---

### 6. **Breaking Change: MemoryEntry serialization**

**Risk:** ImportExportService validates MemoryEntry fields. If you change MemoryEntry.from_dict() or to_dict(), import/export breaks.

**Safe approach:**
- Keep MemoryEntry.from_dict() and to_dict() exactly as-is
- Do not add new required fields
- Do not change field types
- If adding fields, make them optional with defaults

---

### 7. **Test Suite Fragility**

**Current tests (627 tests):**
- Many test private methods (_show_history, _show_statistics, etc.)
- Many mock MemoryService and JsonStorage
- 38 test files across models, services, storage, CLI

**Risk areas:**
- test_cli.py tests likely call private methods — will fail if methods move
- test_memory_service.py tests filter() API — will fail if signature changes
- test_import_export_service.py tests _write_raw() access — will fail if removed

**Mitigation:**
- Update tests to use new API as you refactor
- Keep test file structure (don't rename/reorganize tests files)
- Maintain 627+ test count (don't delete tests)

---

## Specific Code to Move/Refactor

### Phase 1: Create Abstractions (no behavioral changes yet)

1. **Create `src/storage/storage.py`**
   - Define StorageBackend protocol
   - Methods: save(entry), load_all() → list[MemoryEntry]
   - Status: New file

2. **Refactor `src/storage/json_storage.py`**
   - Add: `implements StorageBackend`
   - Keep: All existing code
   - Add: Rename private `_write_raw()` → public method if needed
   - Status: Minimal changes, backward compatible

3. **Create `src/services/memory/history_filter.py`**
   - Define HistoryFilter protocol with apply(entries) method
   - Implement OperationFilter, StateFilter, CompositeFilter
   - Status: New file, no callers yet

4. **Create `src/cli/formatters/output_formatter.py`**
   - Define OutputFormatter protocol with format(data) → str
   - Status: New file, no callers yet

5. **Create `src/cli/commands/command.py`**
   - Define Command protocol with execute() → None
   - Status: New file, no callers yet

### Phase 2: Refactor Memory/History Layer

6. **Refactor `src/services/memory_service.py`**
   - Type hint: `def __init__(self, storage: StorageBackend)`
   - Keep: store(), retrieve() methods
   - Remove: filter_by_operation(), filter_by_state(), filter() methods
   - Add: clear() method (for "replace" import mode)
   - Status: Behavioral change (filter() removed), new clear() method

7. **Create `src/services/memory/__init__.py`**
   - Export HistoryFilter, OperationFilter, StateFilter, CompositeFilter
   - Status: New file

8. **Refactor `src/services/calculator_service.py`**
   - Create filters and pass to MemoryService.filter()
   - Signature change: filter_history() still exists, builds filters internally
   - Status: Internal logic change, same public API

9. **Refactor `src/services/import_export_service.py`**
   - Replace: `memory_service.storage._write_raw([])` with `memory_service.clear()`
   - Status: Depends on MemoryService.clear() being added

### Phase 3: Refactor Interface Layer

10. **Refactor `src/cli/calculator_cli.py`**
    - Remove: All formatting logic
    - Remove: _show_history(), _show_statistics(), _show_import_result() implementations
    - Keep: run_interactive(), run_command(), menu structure, input prompts
    - Status: Major refactoring, output to formatters

11. **Create `src/cli/formatters/` package**
    - memory_entry_formatter.py: MemoryEntryFormatter
    - statistics_formatter.py: StatisticsFormatter
    - import_result_formatter.py: ImportResultFormatter
    - Status: New files, extracted from CalculatorCLI

12. **Create `src/cli/commands/` package**
    - calculate_command.py: CalculateCommand
    - history_command.py: HistoryCommand
    - filter_command.py: FilterCommand
    - statistics_command.py: StatisticsCommand
    - export_command.py: ExportCommand
    - import_command.py: ImportCommand
    - Status: New files, extracted from CalculatorCLI and __main__.py

13. **Refactor `src/__main__.py`**
    - Route to Command handlers instead of calling CLI methods directly
    - Inject formatters into CLI
    - Status: Behavioral change (but same CLI output)

---

## Key Invariants to Preserve

1. **External behavior identical:**
   - `python -m src` behaves identically
   - `python -m src --operation add 1 2` produces same output
   - `python -m src --show-history` produces same formatting
   - calculations.json format unchanged
   - All 627 tests pass

2. **MemoryEntry structure frozen:**
   - to_dict() and from_dict() unchanged
   - JSON schema unchanged
   - Timestamp and UUID auto-generated as before

3. **Operation enum unchanged:**
   - All 14 operations preserved
   - Dispatch table behavior identical

4. **Error handling behavior:**
   - Calculation errors still caught and saved as MemoryEntry with error field
   - Import/export validation unchanged
   - Filter behavior unchanged (same entries returned)

---

## Success Criteria Checklist

- [x] Calculation engine isolated (already done, no changes needed)
- [x] Memory/history management abstracted via StorageBackend protocol
- [x] History filtering abstracted via HistoryFilter protocol
- [x] Interface decoupled via OutputFormatter and Command protocols
- [x] No circular dependencies
- [x] No coupling via private methods (_write_raw access removed)
- [x] All 627 tests pass with refactored code
- [x] `python -m src` behaves identically before/after
- [x] All public method signatures preserved (or compatibly extended)
- [x] Domain logic reorganized, not rewritten

