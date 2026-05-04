# Calculator Refactoring Analysis

## Current Structure Overview

The calculator is a Python OOP application with 802 lines across 15 modules. Current architecture separates concerns into logical layers:

**File organization:**
- `src/models/` — Domain objects (Operation enum, CalculationResult, MemoryEntry, StatisticsResult)
- `src/services/` — Business logic (Calculator, CalculatorService, MemoryService, ImportExportService, StatisticsService)
- `src/storage/` — Persistence (JsonStorage)
- `src/cli/` — User interface (CalculatorCLI)
- `tests/` — 12 test modules, 174 passing + 7 failing tests

---

## Current Architecture (File-by-File)

### Models Layer (`src/models/`)

#### `operation.py` (30 lines)
- **Enum**: `Operation` with 14 values (ADD, SUBTRACT, MULTIPLY, DIVIDE, SQUARE, SQRT, POWER, MODULO, SIN, COS, TAN, LOG, LN, EXP)
- **Methods**:
  - `from_string(value: str) -> Operation` — case-insensitive lookup
  - `display_name() -> str` — returns capitalized operation name
- **Responsibilities**: Operation type definition and string conversion
- **Dependencies**: None (pure enum)

#### `calculation_result.py` (42 lines)
- **Dataclass**: `CalculationResult` (6 fields: operation, operand_a, operand_b, result, timestamp, execution_time_ms)
- **Auto-generated field**: timestamp defaults to ISO 8601 now
- **Methods**:
  - `__post_init__()` — auto-generates timestamp
  - `to_dict() -> dict` — serialization
  - `from_dict(data: dict) -> CalculationResult` — deserialization
  - `__str__()` — pretty-print with symbols (+ - × ÷ √ ^ % etc.)
- **Responsibilities**: Represent a single calculation with metadata
- **Dependencies**: Operation (via string name only, not imported)

#### `memory_entry.py` (53 lines)
- **Dataclass**: `MemoryEntry` (7 fields: operation, operands, result, success, execution_time_ms, id, timestamp)
- **Auto-generated fields**: id (UUID), timestamp (ISO 8601)
- **Methods**:
  - `__post_init__()` — auto-generates timestamp
  - `to_dict() -> dict` — serialization
  - `from_dict(data: dict) -> MemoryEntry` — deserialization
- **Responsibilities**: Represent a calculation attempt in session memory with success/failure state
- **Dependencies**: None (pure dataclass)

#### `statistics_result.py` (23 lines)
- **Dataclass**: `StatisticsResult` (4 fields: count_per_operation, total_errors, error_rate, avg_execution_time_ms)
- **Responsibilities**: Immutable container for computed statistics
- **Dependencies**: None (pure dataclass)

---

### Services Layer (`src/services/`)

#### `calculator.py` (50 lines)
- **Class**: `Calculator` (arithmetic only)
- **Methods** (all public):
  - `add(a, b) -> float`
  - `subtract(a, b) -> float`
  - `multiply(a, b) -> float`
  - `divide(a, b) -> float` — raises ValueError on b==0
  - `square(a, b=0) -> float`
  - `sqrt(a, b=0) -> float` — raises ValueError if a < 0
  - `power(a, b) -> float`
  - `modulo(a, b) -> float` — raises ValueError on b==0
  - `calculate(operation: Operation, a: float, b: float) -> float` — dispatch method
- **Responsibilities**: Pure computation engine for basic operations
- **Dependencies**: Operation enum
- **Tight Coupling Issues**: NONE — fully decoupled

#### `scientific_calculator.py` (98 lines)
- **Class**: `ScientificCalculator(Calculator)` — extends Calculator via inheritance
- **Additional methods** (all public):
  - `sin(a, b=0) -> float`
  - `cos(a, b=0) -> float`
  - `tan(a, b=0) -> float`
  - `log(a, b=0) -> float` — raises ValueError if a <= 0
  - `ln(a, b=0) -> float` — raises ValueError if a <= 0
  - `exp(a, b=0) -> float`
  - `calculate(operation: Operation, a: float, b: float) -> float` — overrides parent, adds 6 operations
- **Responsibilities**: Extended computation engine with scientific functions
- **Dependencies**: Calculator (parent), Operation enum
- **Inheritance Pattern**: Proper use of base class with extended dispatch table
- **Tight Coupling Issues**: NONE — clean inheritance

#### `calculator_service.py` (31 lines)
- **Class**: `CalculatorService`
- **Constructor**: `__init__(calculator: Calculator, storage: JsonStorage)`
- **Public methods**:
  - `perform(operation: Operation, a: float, b: float) -> CalculationResult` — executes, times, saves, returns result
  - `get_history() -> list[CalculationResult]` — delegates to storage
- **Responsibilities**: Orchestrate calculation + storage, measure execution time
- **Dependencies**: Calculator (injected), JsonStorage (injected), Operation, CalculationResult
- **Tight Coupling Issues**: 
  - Medium: Directly imports and uses JsonStorage; would benefit from interface abstraction
  - Exception handling: Lets calculator exceptions propagate (intentional — see test_perform_divide_by_zero_does_not_save)

#### `memory_service.py` (93 lines)
- **Class**: `MemoryService`
- **Constructor**: `__init__()` — no arguments, initializes empty list
- **Public methods**:
  - `store(entry: MemoryEntry) -> None` — appends entry to internal list
  - `retrieve() -> list[MemoryEntry]` — returns reference to internal list
  - `query(operation: Optional[str] = None, success: Optional[bool] = None) -> list[MemoryEntry]` — filters by operation and/or success state
- **Responsibilities**: In-memory session storage for MemoryEntry objects
- **Dependencies**: MemoryEntry
- **Tight Coupling Issues**: NONE — pure in-memory service, no file I/O or external calls
- **Key constraint**: Tests verify no `open()` or `json.dump()` calls (test_memory_service_does_not_contain_file_io)

#### `import_export_service.py` (89 lines)
- **Class**: `ImportExportService`
- **Public methods**:
  - `export(memory_service: MemoryService, filepath: Path | str) -> None` — serialize all entries to JSON
  - `import_from(memory_service: MemoryService, filepath: Path | str) -> None` — deserialize from JSON, skip duplicates
- **Responsibilities**: JSON serialization/deserialization of MemoryEntry collections
- **Dependencies**: MemoryService (parameter), MemoryEntry (calls to_dict/from_dict), Path (pathlib)
- **Tight Coupling Issues**: 
  - Medium: Depends directly on MemoryService interface (calls retrieve, store)
  - Duplicate detection: Checks entry.id against existing entries (tight coupling to MemoryEntry.id)

#### `statistics_service.py` (72 lines)
- **Class**: `StatisticsService`
- **Constructor**: `__init__(memory_service: MemoryService)`
- **Public methods**:
  - `compute() -> StatisticsResult` — aggregates stats from memory_service
- **Responsibilities**: Compute aggregated metrics (counts, error rates, timing) from session history
- **Dependencies**: MemoryService (injected), MemoryEntry (iterates over entries), StatisticsResult
- **Tight Coupling Issues**: 
  - Medium: Depends on MemoryService interface (calls retrieve)
  - Assumes MemoryEntry field names (operation, success, execution_time_ms)

---

### Storage Layer (`src/storage/`)

#### `json_storage.py` (32 lines)
- **Class**: `JsonStorage`
- **Constructor**: `__init__(filepath: Path | str)`
- **Public methods**:
  - `save(result: CalculationResult) -> None` — append result as dict to JSON file
  - `load_all() -> list[CalculationResult]` — read all records from file, deserialize
- **Private methods**:
  - `_read_raw() -> list` — safely reads JSON, returns [] on missing/invalid file
  - `_write_raw(records: list) -> None` — writes list to JSON, creates parent dirs
- **Responsibilities**: Persist CalculationResult objects to JSON file
- **Dependencies**: CalculationResult (calls to_dict/from_dict), Path (pathlib)
- **Tight Coupling Issues**: 
  - Low: Only depends on CalculationResult interface (to_dict/from_dict)
  - File I/O is contained and safe (handles missing files gracefully)

---

### CLI Layer (`src/cli/`)

#### `calculator_cli.py` (170 lines)
- **Class**: `CalculatorCLI`
- **Constructor**: `__init__(service: CalculatorService, memory_service: Optional[MemoryService], import_export_service: Optional[ImportExportService])`
- **Public methods**:
  - `run_interactive() -> None` — REPL menu loop (14 operations + view history + export/import + exit)
  - `run_command(operation_str: str, a: float, b: float) -> None` — one-shot mode
  - `export_memory(filepath: str) -> None` — wrapper around import_export_service.export
  - `import_memory(filepath: str) -> None` — wrapper around import_export_service.import_from
- **Private methods** (interaction helpers):
  - `_print_menu()` — renders operation list
  - `_resolve_menu_choice(choice: str) -> Operation | None` — maps choice string to Operation
  - `_prompt_number(prompt: str) -> float | None` — prompts for float, returns None on invalid
  - `_show_history()` — displays CalculationService history
  - `_prompt_and_export()` — prompts for filepath, calls export_memory
  - `_prompt_and_import()` — prompts for filepath, calls import_memory
- **Responsibilities**: User interaction (interactive menu + one-shot), command dispatch, error handling
- **Dependencies**: CalculatorService (required), MemoryService (optional), ImportExportService (optional), Operation enum, CalculationResult
- **Tight Coupling Issues**:
  - High: Tightly coupled to CalculatorService and optional services
  - Menu is hardcoded with operation list (duplicates Operation enum)
  - Exception handling: Catches ValueError and prints to stderr
  - Test failures: run_interactive() doesn't properly handle menu navigation (7 failing tests)

---

### Entry Point

#### `src/__main__.py` (89 lines)
- **Factory functions**:
  - `_build_service() -> CalculatorService` — instantiates ScientificCalculator + JsonStorage
  - `_build_memory_service() -> MemoryService` — instantiates MemoryService
  - `_build_import_export_service() -> ImportExportService` — instantiates ImportExportService
  - `_as_number(value: str) -> float` — argparse type converter
- **Main function** (55 lines):
  - Argparse setup: --operation {operations}, --export FILE, --import FILE, OPERANDS...
  - Service instantiation
  - CLI routing: one-shot, export, import, or interactive
- **Responsibilities**: Dependency injection, argument parsing, flow control
- **Dependencies**: All services and models
- **Tight Coupling Issues**: NONE — proper factory pattern

---

## Public APIs (Methods That Must Be Preserved)

### Operation Enum
```python
Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE,
Operation.SQUARE, Operation.SQRT, Operation.POWER, Operation.MODULO,
Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP
Operation.from_string(value: str) -> Operation
Operation.display_name() -> str
```

### CalculationResult
```python
CalculationResult(operation: str, operand_a: float, operand_b: float, result: float, 
                  timestamp: str = "", execution_time_ms: float = 0.0)
CalculationResult.to_dict() -> dict
CalculationResult.from_dict(data: dict) -> CalculationResult
CalculationResult.__str__() -> str
# Fields: operation, operand_a, operand_b, result, timestamp, execution_time_ms
```

### MemoryEntry
```python
MemoryEntry(operation: str, operands: list, result: Optional[float], success: bool,
            execution_time_ms: float, id: str = "auto-uuid", timestamp: str = "auto-timestamp")
MemoryEntry.to_dict() -> dict
MemoryEntry.from_dict(data: dict) -> MemoryEntry
# Fields: operation, operands, result, success, execution_time_ms, id, timestamp
```

### StatisticsResult
```python
StatisticsResult(count_per_operation: dict[str, int], total_errors: int, 
                 error_rate: float, avg_execution_time_ms: float)
# All fields are read-only (dataclass)
```

### Calculator
```python
Calculator.add(a: float, b: float) -> float
Calculator.subtract(a: float, b: float) -> float
Calculator.multiply(a: float, b: float) -> float
Calculator.divide(a: float, b: float) -> float
Calculator.square(a: float, b: float = 0) -> float
Calculator.sqrt(a: float, b: float = 0) -> float
Calculator.power(a: float, b: float) -> float
Calculator.modulo(a: float, b: float) -> float
Calculator.calculate(operation: Operation, a: float, b: float) -> float
```

### ScientificCalculator (extends Calculator)
```python
ScientificCalculator.sin(a: float, b: float = 0) -> float
ScientificCalculator.cos(a: float, b: float = 0) -> float
ScientificCalculator.tan(a: float, b: float = 0) -> float
ScientificCalculator.log(a: float, b: float = 0) -> float
ScientificCalculator.ln(a: float, b: float = 0) -> float
ScientificCalculator.exp(a: float, b: float = 0) -> float
ScientificCalculator.calculate(operation: Operation, a: float, b: float) -> float
```

### CalculatorService
```python
CalculatorService.__init__(calculator: Calculator, storage: JsonStorage)
CalculatorService.perform(operation: Operation, a: float, b: float) -> CalculationResult
CalculatorService.get_history() -> list[CalculationResult]
```

### MemoryService
```python
MemoryService.__init__()
MemoryService.store(entry: MemoryEntry) -> None
MemoryService.retrieve() -> list[MemoryEntry]
MemoryService.query(operation: Optional[str] = None, success: Optional[bool] = None) -> list[MemoryEntry]
```

### ImportExportService
```python
ImportExportService.export(memory_service: MemoryService, filepath: Path | str) -> None
ImportExportService.import_from(memory_service: MemoryService, filepath: Path | str) -> None
```

### StatisticsService
```python
StatisticsService.__init__(memory_service: MemoryService)
StatisticsService.compute() -> StatisticsResult
```

### JsonStorage
```python
JsonStorage.__init__(filepath: Path | str)
JsonStorage.save(result: CalculationResult) -> None
JsonStorage.load_all() -> list[CalculationResult]
```

### CalculatorCLI
```python
CalculatorCLI.__init__(service: CalculatorService, memory_service: MemoryService | None = None, 
                       import_export_service: ImportExportService | None = None)
CalculatorCLI.run_interactive() -> None
CalculatorCLI.run_command(operation_str: str, a: float, b: float) -> None
CalculatorCLI.export_memory(filepath: str) -> None
CalculatorCLI.import_memory(filepath: str) -> None
```

---

## Tests to Preserve (174 passing + 7 failing)

### Test Modules and Coverage

| Test File | Test Count | Status | Focus |
|-----------|-----------|--------|-------|
| test_calculator.py | ? | passing | Calculator basic operations (add, subtract, multiply, divide, square, sqrt, power, modulo) |
| test_scientific_calculator.py | ? | passing | ScientificCalculator extended ops (sin, cos, tan, log, ln, exp) |
| test_advanced_operations.py | ? | passing | Edge cases: modulo by zero, division by zero, negative sqrt, log/ln domain errors |
| test_execution_time_tracking.py | ? | passing | CalculationResult execution_time_ms is set and > 0 |
| test_calculator_service.py | 9 | 9 passing | CalculatorService.perform() and get_history(), storage integration |
| test_memory_entry.py | ? | passing | MemoryEntry serialization (to_dict, from_dict), auto-generation of id/timestamp |
| test_memory_service.py | 10 | 10 passing | MemoryService (store, retrieve, query with operation/success filters) |
| test_json_storage.py | ? | passing | JsonStorage (save, load_all), file I/O |
| test_import_export_service.py | 7 | 7 passing | ImportExportService (export, import with duplicate detection) |
| test_statistics_service.py | ? | passing | StatisticsService.compute() (operation counts, error rate, avg time) |
| test_cli.py | 12 | 5 passing / 7 failing | CalculatorCLI (run_command, run_interactive, import/export) |

**Total**: 12 test modules, ~174 passing, 7 failing (pre-existing)

**Failing tests** (pre-existing, not related to refactoring):
1. `test_invalid_operation_exits` — run_command() should exit on invalid operation
2. `test_exit_choice` — run_interactive() menu navigation
3. `test_add_operation` — run_interactive() menu + number prompts
4. `test_invalid_choice_retries` — run_interactive() error handling
5. `test_invalid_number_retries` — run_interactive() number validation
6. `test_history_empty` — run_interactive() history option
7. `test_history_shows_entries` — run_interactive() history display

---

## Current Issues (Tight Coupling, Mixed Responsibilities)

### Issue 1: CalculatorService Directly Imports JsonStorage
**Severity**: Medium
**Location**: `calculator_service.py` line 5, constructor parameter
**Problem**: CalculatorService takes JsonStorage as a concrete dependency (not an interface). Any storage implementation must be JsonStorage.
**Impact**: Cannot easily swap storage backend without modifying CalculatorService.
**Refactoring Opportunity**: Extract Storage interface (read/write), depend on abstraction.

### Issue 2: CLI Menu Duplicates Operation Enum
**Severity**: Low
**Location**: `calculator_cli.py` lines 10-25, hardcoded menu list
**Problem**: The menu list hardcodes all 14 operations with labels. If Operation enum changes, menu breaks.
**Impact**: Maintenance burden, inconsistency risk.
**Refactoring Opportunity**: Dynamically build menu from Operation enum.

### Issue 3: ImportExportService and StatisticsService Depend on MemoryService Interface
**Severity**: Low-Medium
**Location**: `import_export_service.py` (calls retrieve, store), `statistics_service.py` (calls retrieve)
**Problem**: Both services assume MemoryService has retrieve() and store() methods. Tight coupling to session storage.
**Impact**: Cannot use different memory backends (e.g., persistent DB).
**Refactoring Opportunity**: Define MemoryBackend interface for retrieve/store.

### Issue 4: CalculatorCLI Optional Dependencies
**Severity**: Low
**Location**: `calculator_cli.py` lines 96-118
**Problem**: export_memory and import_memory check for None services, print errors, but constructor allows None.
**Impact**: Runtime errors if features used without initialization.
**Refactoring Opportunity**: Separate CLI layer into base + feature modules, or make services required.

### Issue 5: Hardcoded Storage Path
**Severity**: Low
**Location**: `src/__main__.py` line 15
**Problem**: Storage path is hardcoded relative to __file__: `artifacts/calculations.json`
**Impact**: Cannot easily change storage location without modifying __main__.
**Refactoring Opportunity**: Make storage path configurable (env var or CLI arg).

### Issue 6: CalculationResult and MemoryEntry Are Similar
**Severity**: Low
**Location**: Both in models/
**Problem**: Both track operations and results, but use different field names (operand_a/b vs operands, no success field in CalculationResult)
**Impact**: Conceptual overlap, potential for confusion.
**Refactoring Opportunity**: Consider unified Result type with operation, operands, result, success, timing, id, timestamp.

### Issue 7: Pre-existing CLI Test Failures
**Severity**: High (pre-existing, not new)
**Location**: `tests/test_cli.py` (7 failing tests)
**Problem**: run_interactive() test mocks don't provide enough input values for the menu loop. Tests expect different menu navigation behavior.
**Impact**: Cannot verify interactive CLI works correctly.
**Refactoring Opportunity**: Fix test mocks to simulate full menu interaction, or refactor menu to be more testable.

---

## Refactoring Scope

### What CAN Change (Internal Implementation)
- Move responsibilities between files (as long as public APIs stay the same)
- Introduce internal interfaces (abstract base classes, protocols)
- Refactor CalculatorService to use dependency injection with an abstract Storage interface
- Refactor ImportExportService and StatisticsService to accept an abstract MemoryBackend interface
- Dynamically build CLI menu from Operation enum
- Make storage path configurable
- Consolidate CalculationResult and MemoryEntry into a single Result type (if tests are updated accordingly)
- Reorganize files into new subdirectories (e.g., `services/calculation_engine/`, `services/history/`, `services/interface/`)

### What CANNOT Change (Public APIs)
- All method signatures listed above must be preserved exactly
- All Operation enum values must exist
- CalculationResult, MemoryEntry, StatisticsResult fields and serialization behavior
- Calculator and ScientificCalculator method behavior (return types, exceptions)
- CalculatorService.perform() must save to storage and measure execution time
- MemoryService must not perform file I/O
- JsonStorage must read/write to actual files
- All 174 passing tests must continue to pass
- CLI entry points (interactive, one-shot, export, import) must work as-is

### Borderline/Requires Careful Testing
- Refactoring the internal import graph (e.g., moving Calculator to engine/ subdirectory)
- Changing how ScientificCalculator inherits from Calculator (could impact isinstance checks in tests)
- Restructuring services layer organization (tests import directly from services/)

---

## Suggested Priorities

### High-Impact, Low-Risk
1. **Extract Storage interface** (e.g., `StorageBackend` protocol or ABC)
   - Impact: Decouple CalculatorService from JsonStorage
   - Risk: Low (no public API change, same behavior)
   - Effort: 2-3 hours

2. **Dynamically build CLI menu from Operation enum**
   - Impact: Reduce duplication, improve maintainability
   - Risk: Low (purely internal)
   - Effort: 1 hour

3. **Introduce Memory interface** for MemoryService, ImportExportService, StatisticsService
   - Impact: Enable different memory backends, clarify dependencies
   - Risk: Low (no public API change)
   - Effort: 2 hours

### Medium-Impact, Higher-Risk (Requires Careful Testing)
4. **Reorganize services layer** into three directories:
   - `services/calculation_engine/` (Calculator, ScientificCalculator)
   - `services/history/` (MemoryService, ImportExportService, StatisticsService)
   - `services/orchestration/` (CalculatorService)
   - Risk: Import paths change; tests and __main__.py need updates
   - Effort: 3-4 hours

5. **Fix pre-existing CLI test failures**
   - Impact: Enable CI/CD to verify interactive mode
   - Risk: May require refactoring CLI for testability
   - Effort: 3-4 hours

### Low-Priority
6. **Consolidate CalculationResult and MemoryEntry** into a single type
   - Impact: Cleaner domain model
   - Risk: High (affects many tests and import paths)
   - Effort: 5+ hours

---

## Summary Table

| Metric | Value |
|--------|-------|
| Total Source Lines | 802 |
| Total Test Lines | ~1200+ |
| Test Count | 181 (174 passing + 7 failing) |
| Public Methods | 65+ |
| Modules | 15 |
| Enum Values | 14 |
| Dataclasses | 3 |
| Service Classes | 7 |
| Tight Coupling Issues | 7 (medium to low severity) |
| Pre-existing Test Failures | 7 (CLI-related) |

---

## Diagram References

Existing architecture diagrams in `artifacts/`:
- `component_diagram.puml` — High-level component dependencies
- `class_diagram.puml` — Detailed class structure and relationships
- `use_case_diagram.puml` — User-facing features
- `activity_diagram.puml` — Calculation workflow
- `state_diagram_*.puml` — State machines (command parsing, interactive mode)

These diagrams should be updated after refactoring to reflect new file organization and dependency structure.
