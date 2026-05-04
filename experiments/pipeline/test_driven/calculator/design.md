# Task 09 Design: Calculator Refactoring into Separated Components

## Overview

Refactor the calculator into clearly separated components (calculation engine, memory/history management, interface layer) while preserving all existing public behavior.

## 1. NEW DIRECTORY STRUCTURE

```
src/
├── __main__.py                          (unchanged, just update imports)
├── models/
│   ├── __init__.py
│   ├── operation.py                     (unchanged)
│   ├── calculation_result.py            (unchanged)
│   ├── memory_entry.py                  (unchanged)
│   └── statistics_result.py             (unchanged)
├── core/                                (NEW DIRECTORY - Calculation Engine Layer)
│   ├── __init__.py
│   ├── interfaces.py                    (NEW - define calculation abstraction)
│   ├── calculator.py                    (MOVED from services/)
│   └── scientific_calculator.py         (MOVED from services/)
├── storage/
│   ├── __init__.py
│   ├── interfaces.py                    (NEW - define storage abstraction)
│   └── json_storage.py                  (unchanged, but depends on interfaces)
├── history/                             (NEW DIRECTORY - Memory/History Layer)
│   ├── __init__.py
│   ├── interfaces.py                    (NEW - define memory backend abstraction)
│   ├── memory_service.py                (unchanged functionally, depends on interfaces)
│   ├── import_export_service.py         (unchanged functionally, depends on interfaces)
│   └── statistics_service.py            (unchanged functionally, depends on interfaces)
├── services/
│   ├── __init__.py
│   └── calculator_service.py            (MODIFIED - depends on storage interface)
└── cli/
    ├── __init__.py
    └── calculator_cli.py                (MODIFIED - dynamic menu)
```

## 2. COMPONENT DEFINITIONS

### Layer 1: Calculation Engine (`src/core/`)
Responsible for: Pure computation logic, no side effects

**Components:**
- `Calculator` — Basic arithmetic operations (add, subtract, multiply, divide, square, sqrt, power, modulo)
- `ScientificCalculator(Calculator)` — Extends Calculator with scientific functions (sin, cos, tan, log, ln, exp)

**Responsibilities:**
- Perform arithmetic and scientific calculations
- Raise ValueError on domain errors (division by zero, negative sqrt, etc.)
- No I/O, no storage, no state persistence

### Layer 2: Storage & History (`src/storage/` and `src/history/`)
Responsible for: State management and persistence

**Components:**

*Storage Layer (`src/storage/`):*
- `StorageBackend` (interface/protocol) — Abstract read/write interface
- `JsonStorage` — Concrete file-based storage for CalculationResult

*History Layer (`src/history/`):*
- `MemoryBackend` (interface/protocol) — Abstract interface for entry storage with retrieve/store
- `MemoryService` — In-memory session storage (implements MemoryBackend)
- `ImportExportService` — JSON serialization/deserialization (depends on MemoryBackend interface)
- `StatisticsService` — Aggregation metrics (depends on MemoryBackend interface)

### Layer 3: Orchestration & Interface (`src/services/` and `src/cli/`)
Responsible for: Coordination, timing, and user interaction

**Components:**
- `CalculatorService` — Orchestrates calculation + storage, measures timing
- `CalculatorCLI` — User interaction (interactive menu, one-shot commands)

## 3. PUBLIC API PRESERVATION

All public APIs are preserved with **identical signatures and behavior**. Changes are internal only.

**Key Preserved Signatures:**
- `Operation` enum — all values, from_string(), display_name()
- `CalculationResult` — all fields and methods
- `MemoryEntry` — all fields and methods
- `StatisticsResult` — all fields
- `Calculator.{add, subtract, multiply, divide, square, sqrt, power, modulo, calculate}()`
- `ScientificCalculator.{sin, cos, tan, log, ln, exp, calculate}()`
- `CalculatorService.__init__(calculator: Calculator, storage: JsonStorage)`
- `CalculatorService.{perform(), get_history()}`
- `MemoryService.{store(), retrieve(), query()}`
- `ImportExportService.{export(), import_from()}`
- `StatisticsService.__init__(), compute()`
- `JsonStorage.__init__(), {save(), load_all()}`
- `CalculatorCLI.__init__(), {run_interactive(), run_command(), export_memory(), import_memory()}`

## 4. INTERFACE/PROTOCOL DEFINITIONS

### `src/core/interfaces.py`
```python
from typing import Protocol
from ..models.operation import Operation

class CalculationEngine(Protocol):
    def calculate(self, operation: Operation, a: float, b: float) -> float: ...
```

### `src/storage/interfaces.py`
```python
from typing import Protocol
from ..models.calculation_result import CalculationResult

class StorageBackend(Protocol):
    def save(self, result: CalculationResult) -> None: ...
    def load_all(self) -> list[CalculationResult]: ...
```

### `src/history/interfaces.py`
```python
from typing import Protocol
from ..models.memory_entry import MemoryEntry

class MemoryBackend(Protocol):
    def store(self, entry: MemoryEntry) -> None: ...
    def retrieve(self) -> list[MemoryEntry]: ...
```

## 5. FILE-BY-FILE CHANGES

### Phase 1: Create abstraction interfaces

**New File: `src/core/interfaces.py`**
- Define `CalculationEngine` protocol with `calculate(operation, a, b) -> float` method

**New File: `src/storage/interfaces.py`**
- Define `StorageBackend` protocol with `save(result)` and `load_all()` methods

**New File: `src/history/interfaces.py`**
- Define `MemoryBackend` protocol with `store(entry)` and `retrieve()` methods

### Phase 2: Reorganize and move files

**Action:** Move files to new directories
- Move `src/services/calculator.py` → `src/core/calculator.py`
- Move `src/services/scientific_calculator.py` → `src/core/scientific_calculator.py`
- Create `src/core/__init__.py` (can be empty)
- Move `src/services/memory_service.py` → `src/history/memory_service.py`
- Move `src/services/import_export_service.py` → `src/history/import_export_service.py`
- Move `src/services/statistics_service.py` → `src/history/statistics_service.py`
- Create `src/history/__init__.py` (can be empty)

### Phase 3: Update moved files to implement interfaces

**Modified: `src/core/calculator.py`**
- Update imports for ScientificCalculator: `from .scientific_calculator import ScientificCalculator`
- No changes to logic or public API

**Modified: `src/core/scientific_calculator.py`**
- Update imports: `from .calculator import Calculator`
- No changes to logic or public API

**Modified: `src/history/memory_service.py`**
- Add import: `from .interfaces import MemoryBackend`
- Add type hint annotation (implement MemoryBackend protocol)
- No behavior change

**Modified: `src/history/import_export_service.py`**
- Change parameter type: `memory_service: MemoryBackend` instead of `memory_service: MemoryService`
- Update imports: Add `from .interfaces import MemoryBackend`, remove `MemoryService` import
- Update relative imports for MemoryEntry
- Behavior unchanged — uses duck typing to call retrieve/store

**Modified: `src/history/statistics_service.py`**
- Change parameter type: `memory_service: MemoryBackend` instead of `memory_service: MemoryService`
- Update imports: Add `from .interfaces import MemoryBackend`, remove `MemoryService` import
- Behavior unchanged — uses duck typing to call retrieve()

### Phase 4: Update orchestration layer

**Modified: `src/services/calculator_service.py`**
- Update imports:
  - `from ..core.calculator import Calculator`
  - `from ..storage.interfaces import StorageBackend`
  - `from ..core.interfaces import CalculationEngine`
- Type hints: Accept StorageBackend interface in type hints (parameter name stays `storage: JsonStorage` for public API compatibility)
- Add internal type hints for protocol usage
- No behavior change

**Modified: `src/storage/json_storage.py`**
- Add import: `from .interfaces import StorageBackend`
- Add type hint annotation: implement StorageBackend protocol
- No behavior change

### Phase 5: Update CLI and entry point

**Modified: `src/cli/calculator_cli.py`**
- Remove hardcoded `_MENU` class variable (lines 10-25)
- Add method `_build_menu() -> list[tuple]` that dynamically builds menu from Operation enum
- Update references to `_MENU` to call `_build_menu()`
- Update imports if ScientificCalculator imported (now at `..core.scientific_calculator`)
- No changes to public API

**Modified: `src/__main__.py`**
- Update import paths:
  - `from .core.scientific_calculator import ScientificCalculator`
  - `from .history.memory_service import MemoryService`
  - `from .history.import_export_service import ImportExportService`
  - `from .history.statistics_service import StatisticsService`
  - Keep `from .services.calculator_service import CalculatorService` (unchanged)
  - Keep `from .storage.json_storage import JsonStorage` (unchanged)
- No changes to factory functions or main logic

## 6. IMPLEMENTATION ORDER

1. Create `src/core/interfaces.py` — CalculationEngine protocol
2. Create `src/storage/interfaces.py` — StorageBackend protocol
3. Create `src/history/interfaces.py` — MemoryBackend protocol
4. Move `src/services/calculator.py` → `src/core/calculator.py`
5. Move `src/services/scientific_calculator.py` → `src/core/scientific_calculator.py`
6. Create `src/core/__init__.py`
7. Move `src/services/memory_service.py` → `src/history/memory_service.py`
8. Move `src/services/import_export_service.py` → `src/history/import_export_service.py`
9. Move `src/services/statistics_service.py` → `src/history/statistics_service.py`
10. Create `src/history/__init__.py`
11. Update `src/core/calculator.py` — update imports for ScientificCalculator
12. Update `src/core/scientific_calculator.py` — import Calculator from `.calculator`
13. Update `src/history/memory_service.py` — add MemoryBackend protocol annotation
14. Update `src/history/import_export_service.py` — change MemoryService param to MemoryBackend, update imports
15. Update `src/history/statistics_service.py` — change MemoryService param to MemoryBackend, update imports
16. Update `src/services/calculator_service.py` — import from core/, add type hints for protocols
17. Update `src/storage/json_storage.py` — add protocol implementation annotation
18. Update `src/cli/calculator_cli.py` — dynamic menu from Operation enum
19. Update `src/__main__.py` — import paths for moved files
20. Run all tests to ensure no breakage

## 7. TESTING STRATEGY

- No test modifications required — all 174 passing tests should continue to pass without change
- All public APIs remain unchanged in signature and behavior
- Test scenarios verify:
  - All arithmetic and scientific operations still work
  - CalculatorService performs calculations and stores results
  - JsonStorage persists and retrieves calculations
  - MemoryService stores and retrieves memory entries
  - ImportExportService exports/imports with duplicate detection
  - StatisticsService computes aggregates correctly
  - CalculatorCLI interactive and one-shot modes work
  - Dynamic menu displays all operations
  - python -m src entry point works identically

## 8. SUMMARY

| Aspect | Detail |
|--------|--------|
| **Layers** | 3 (Calculation Engine, Storage/History, Orchestration/Interface) |
| **New Directories** | `src/core/`, `src/history/` |
| **Files Moved** | 5 (calculator.py, scientific_calculator.py, memory_service.py, import_export_service.py, statistics_service.py) |
| **Files Created** | 4 (3 interface files, 2 __init__ files) |
| **Files Modified** | 4 (calculator_service.py, json_storage.py, calculator_cli.py, __main__.py) |
| **Interfaces Introduced** | 3 (CalculationEngine, StorageBackend, MemoryBackend) |
| **Public APIs Changed** | 0 (all preserved) |
| **Tests Modified** | 0 (all pass without change) |
