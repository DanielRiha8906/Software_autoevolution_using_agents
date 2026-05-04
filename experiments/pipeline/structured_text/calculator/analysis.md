# Calculator Project - Component Separation Analysis

**Task 09: Separate Core Components**
**Status:** Analysis Complete
**Date:** 2026-05-04

---

## Summary

The calculator project is a well-structured OOP application with clear logical separation between calculation logic, memory/history management, and CLI interface. However, components are currently **tightly coupled** at the service and CLI layers, with both `CalculatorService` and `MemoryService` being direct dependencies of the CLI. The memory tracking system is **separate but not formalized** — there are no abstract protocols defining component boundaries.

The refactoring task requires introducing abstract base classes/protocols and clearer encapsulation while preserving all existing functionality and external behavior.

---

## Current Architecture

### Directory Structure

```
src/
├── __main__.py                 # CLI entry point and argparse setup
├── models/                     # Data models (domain entities)
│   ├── operation.py            # Operation enum with fromString factory
│   ├── calculation_result.py   # Dataclass: represents a completed calc
│   ├── memory_entry.py         # Dataclass: represents a stored attempt (success/failure)
│   └── calculation_statistics.py # Dataclass: aggregated metrics
├── services/                   # Business logic and orchestration
│   ├── calculator.py           # Pure calculation engine
│   ├── calculator_service.py   # Orchestrates Calculator + storage for calcs
│   └── memory_service.py       # Manages MemoryEntry lifecycle & filtering
├── storage/                    # Persistence layer
│   ├── json_storage.py         # Persists CalculationResult to JSON
│   └── memory_json_storage.py  # Persists MemoryEntry to JSON
└── cli/
    └── calculator_cli.py       # Interactive & one-shot command interface
```

### Component Responsibilities (Current)

#### 1. Calculation Engine: `Calculator`
- **File:** `src/services/calculator.py`
- **Responsibility:** Pure arithmetic logic
- **Methods:**
  - `add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)` — binary ops
  - `square(a, b)`, `sqrt(a, b)`, `power(a, b)`, `modulo(a, b)` — unary/binary mixed
  - `sin(a, b)`, `cos(a, b)`, `tan(a, b)`, `log(a, b)`, `ln(a, b)`, `exp(a, b)` — trigonometric/logarithmic
  - `calculate(operation: Operation, a, b)` — dispatch by enum
- **No Dependencies:** Uses only Python stdlib (`math`)
- **Error Handling:** Raises `ValueError` for invalid inputs (division by zero, negative sqrt, etc.)
- **Coupling:** NONE. This is a pure, stateless calculation library.

**Current Status:** Well-isolated. No refactoring needed here.

---

#### 2. Memory/History Management: Mixed Layers
This is where the complexity lies. History is tracked in **two separate ways**:

**2a. Short-term calculation history: `CalculatorService` + `JsonStorage`**
- **Class:** `CalculatorService` (`src/services/calculator_service.py`)
- **Purpose:** Perform a calculation and immediately persist it
- **Dependency Chain:** 
  ```
  CalculatorService
    ├── Owns: Calculator (injection)
    ├── Owns: JsonStorage (injection)
    └── Delegates:
        ├── calculation → Calculator.calculate()
        ├── timing measurement → time.perf_counter()
        └── persistence → JsonStorage.save()
  ```
- **Output Model:** `CalculationResult` — simple dataclass with operation, operands, result, timestamp, execution_time_ms
- **Storage:** `JsonStorage` persists to `artifacts/calculations.json` (append-only JSON array)
- **Methods:**
  - `perform(operation, a, b) → CalculationResult` — execute and save, returns result. **On error, raises exception WITHOUT saving.**
  - `get_history() → List[CalculationResult]` — delegates to storage

**2b. Full audit trail: `MemoryService` + `MemoryJsonStorage`**
- **Class:** `MemoryService` (`src/services/memory_service.py`)
- **Purpose:** Store and query a complete audit log of all calculation attempts (including failures with error messages)
- **Dependency Chain:**
  ```
  MemoryService
    ├── Owns: MemoryJsonStorage (injection)
    └── Delegates persistence to storage
  ```
- **Output Model:** `MemoryEntry` — richer dataclass capturing:
  - `operation, operand_a, operand_b` — what was tried
  - `result, success, error_message` — outcome and error details
  - `execution_timestamp, execution_time_ms` — timing
  - `memory_entry_id` — unique identifier (UUID auto-generated)
- **Storage:** `MemoryJsonStorage` persists to `artifacts/memory_entries.json` (append-only JSON array)
- **Methods:**
  - `store(entry: MemoryEntry) → None`
  - `retrieve_all() → List[MemoryEntry]`
  - `filter_by_operation(name) → List[MemoryEntry]` — case-insensitive
  - `filter_by_success(bool) → List[MemoryEntry]`
  - `filter_by_execution_time(min_ms, max_ms) → List[MemoryEntry]`
  - `compute_statistics() → CalculationStatistics` — aggregates metrics over all entries
  - `export_to_file(path) → int` — serializes all entries to JSON
  - `import_from_file(path, skip_invalid) → tuple[int, list]` — deserializes and imports with validation

**Key Coupling Issue:**
- `CalculatorService` and `MemoryService` are **separate** but **not coordinated**.
- The CLI must manually decide to store results in both systems (not shown in `CalculatorService`, happens elsewhere).
- There is **no abstract protocol** defining what a "memory" or "storage" component should do.
- Two different storage classes (`JsonStorage`, `MemoryJsonStorage`) with **no common interface** — similar responsibilities but no base class.

---

#### 3. Interface/CLI: `CalculatorCLI`
- **File:** `src/cli/calculator_cli.py`
- **Responsibility:** User interaction and presentation
- **Dependency Chain:**
  ```
  CalculatorCLI
    ├── Owns: CalculatorService (injection)
    ├── Owns: MemoryService | None (optional injection)
    ├── Imports: Operation enum
    └── No direct dependency on storage classes
  ```
- **Public Methods (entry points):**
  - `run_interactive() → None` — main menu loop
  - `run_command(operation_str, a, b) → None` — one-shot execution
  - `show_memory() → None` — display all memory entries
  - `show_statistics() → None` — display aggregated stats
  - `export_memory(filepath=None) → None` — export to file (prompts if path missing)
  - `import_memory(filepath=None, skip_invalid=False) → None` — import from file
- **Private Helpers (pure UI):**
  - `_print_menu()` — render menu
  - `_resolve_menu_choice(choice)` → Operation | None
  - `_prompt_number(prompt)` → float | None
  - `_show_history()` — display calculation history (from `CalculatorService`)
  - `_show_memory()` — display memory entries (from `MemoryService`)
  - `_filter_memory_by_operation()` — interactive filter UI
  - `_filter_memory_by_status()` — interactive filter UI
  - `_show_statistics()` — display stats (computed by `MemoryService`)

**Key Coupling Issues:**
- CLI directly calls `service.perform()` and `memory_service.*()`, mixing **computation orchestration** with **presentation logic**.
- The CLI knows too much about both `CalculatorService` and `MemoryService` internals (methods, parameters).
- No abstraction layer; replacing or extending either service requires CLI changes.
- `MemoryService` is **optional** (can be None), forcing defensive null-checks throughout CLI.

---

## Data Flow

### Success Path: Add 3 + 5 (Interactive)

```
1. CLI: show menu
2. User: enter choice "1" (add)
3. CLI: prompt operands → 3, 5
4. CLI: run_interactive() → cli.service.perform(Operation.ADD, 3.0, 5.0)
5. CalculatorService.perform():
   - time measurement starts
   - Calculator.calculate(Operation.ADD, 3, 5) → 8.0
   - CalculationResult created with result=8.0, timestamp, execution_time
   - JsonStorage.save(result) → appends to calculations.json
   - returns CalculationResult
6. CLI: display result "3 + 5 = 8"
7. (MemoryService NOT called in current path — memory entry is NOT stored)
```

### Failure Path: Divide by 0

```
1. CLI: prompt operation (divide), operands (10, 0)
2. CLI: cli.service.perform(Operation.DIVIDE, 10, 0)
3. CalculatorService.perform():
   - Calculator.calculate(Operation.DIVIDE, 10, 0)
   - Calculator.divide() checks: if b == 0 → raise ValueError("Division by zero...")
   - Exception propagates up; JsonStorage.save() NEVER CALLED
4. CLI: catches ValueError, prints "Error: Division by zero..."
5. (MemoryService NOT called — no audit trail of the failed attempt)
```

**Critical Gap:** Failed calculations are **not** recorded. Only `MemoryService` can capture failures, but the CLI doesn't automatically wire them together.

---

## Couplings and Dependencies

### Tight Couplings

1. **CLI → CalculatorService**
   - Direct method calls: `service.perform()`, `service.get_history()`
   - Knows about return type: `CalculationResult`
   - No abstraction layer

2. **CLI → MemoryService**
   - Direct method calls: `memory_service.store()`, `memory_service.retrieve_all()`, `memory_service.filter_*()`, `memory_service.compute_statistics()`, `memory_service.export_to_file()`, `memory_service.import_from_file()`
   - Knows about return types: `List[MemoryEntry]`, `CalculationStatistics`, tuple
   - Optional dependency with repeated null-checks

3. **CalculatorService → JsonStorage**
   - Direct injection dependency
   - Knows about storage interface: `save(result)`, `load_all()`
   - No abstraction; storage implementation detail exposed

4. **MemoryService → MemoryJsonStorage**
   - Direct injection dependency
   - Knows about storage interface: `save(entry)`, `load_all()`, `_read_raw()`, `_write_raw()`
   - No abstraction

5. **Two Storage Implementations with No Common Interface**
   - `JsonStorage` and `MemoryJsonStorage` are both persistence layers
   - **No shared base class or protocol**
   - Similar method signatures (`save()`, `load_all()`) but unrelated
   - Different model types (`CalculationResult` vs `MemoryEntry`)

### Loose Couplings

- **CLI → Operation enum:** Uses `Operation.from_string()` and display names. Acceptable; enum is a stable model.
- **CLI → Models (CalculationResult, MemoryEntry, CalculationStatistics):** Uses for display/inspection. Acceptable; models are stable data containers.

---

## What Exists Now

| Component | Type | Purpose | Hidden Behavior |
|-----------|------|---------|-----------------|
| `Calculator` | Pure logic | Arithmetic operations | None; deterministic and stateless |
| `CalculatorService` | Orchestrator | Calc + persist to history | Timing measurement; exception stops save |
| `MemoryService` | Orchestrator + Query | Manage audit trail | Filtering logic; statistics computation |
| `JsonStorage` | Persistence | Store CalculationResult | File I/O, error recovery (silently ignores corruption) |
| `MemoryJsonStorage` | Persistence | Store MemoryEntry | File I/O, error recovery (silently ignores corruption) |
| `CalculatorCLI` | Interface | Menu + one-shot mode | Menu numbering depends on `_MENU` length; complex state machine |

---

## What Needs Separation

### 1. **Abstract Storage Interface(s)**
   
**Problem:** Two storage classes do the same thing but with different models. No interface to swap implementations.

**Solution:** Create an abstract base class or protocol.

```python
# Option A: ABC (Abstract Base Class)
from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def save(self, entry) -> None: ...
    
    @abstractmethod
    def load_all(self) -> List: ...

# Option B: Protocol (duck typing + type hints)
from typing import Protocol

class Storage(Protocol):
    def save(self, entry) -> None: ...
    def load_all(self) -> List: ...
```

**Scope:**
- `JsonStorage` → implements `Storage[CalculationResult]`
- `MemoryJsonStorage` → implements `Storage[MemoryEntry]`
- Both follow same contract: append-only JSON persistence

---

### 2. **Abstract Service Interfaces**

**Problem:** `CalculatorService` and `MemoryService` have different contracts. CLI must know about both.

**Solution:** Formalize service contracts with protocols or ABCs.

**Calculation Service Protocol:**
```python
class CalculationService(Protocol):
    """Execute a single calculation and return result."""
    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult: ...
    def get_history(self) -> List[CalculationResult]: ...
```

**Memory Service Protocol:**
```python
class MemoryManagement(Protocol):
    """Store, retrieve, and query calculation attempts."""
    def store(self, entry: MemoryEntry) -> None: ...
    def retrieve_all(self) -> List[MemoryEntry]: ...
    def filter_by_operation(self, name: str) -> List[MemoryEntry]: ...
    def filter_by_success(self, success: bool) -> List[MemoryEntry]: ...
    def filter_by_execution_time(self, min_ms: float, max_ms: float) -> List[MemoryEntry]: ...
    def compute_statistics(self) -> CalculationStatistics: ...
    def export_to_file(self, filepath) -> int: ...
    def import_from_file(self, filepath, skip_invalid) -> tuple[int, list]: ...
```

---

### 3. **Decouple CLI from Service Details**

**Problem:** CLI directly calls service methods and knows their signatures. Hard to test; hard to extend.

**Solution:** Introduce a facade or coordinator that sits between CLI and services.

**Current:** CLI → CalculatorService/MemoryService
**Proposed:** CLI → CalculatorFacade → (CalculatorService + MemoryService)

The facade would:
- Coordinate between calculation and memory services
- Present a unified interface to CLI
- Handle error cases (e.g., capture failures in both systems)
- Manage orchestration logic (e.g., "when a calc fails, create a MemoryEntry")

---

## Tests Verify Current Behavior

- **433 tests, all passing** ✓
- Coverage includes:
  - Calculator pure logic (30+ tests)
  - CalculatorService orchestration (15+ tests)
  - MemoryService store/retrieve (50+ tests)
  - MemoryService filtering & statistics (50+ tests)
  - Storage persistence (20+ tests)
  - CLI interactive mode (20+ tests)
  - CLI one-shot flags (50+ tests)
  - Import/export (30+ tests)
  - Data models serialization (50+ tests)

**Requirement:** All 433 tests must pass after refactoring.

---

## External Behavior (Must Not Change)

### CLI Entry Point: `python -m src`
- **Interactive:** No args → show menu, accept user input
- **One-shot:** `--operation add 3 5` → execute and print result
- **Flags:** `--memory`, `--statistics`, `--export`, `--import`, etc.
- **Output:** Same format and messages as before
- **Side Effects:** Same JSON files created/updated

### Return Types
- `CalculatorService.perform()` → `CalculationResult` (same fields, same serialization)
- `MemoryService.retrieve_all()` → `List[MemoryEntry]` (same fields, same serialization)
- Storage JSON format must remain compatible (backward compat required)

---

## Ambiguities and Working Assumptions

### 1. **Are we creating a "memory" abstraction separate from "storage"?**
   - **Current state:** Memory (audit trail) and History (short-term calc log) are logically separate.
   - **Assumption:** Keep them separate. A "memory service" is not just persistence; it's a query/analytics layer on top of storage.
   - **Implication:** Abstract storage, but memory service remains domain-specific.

### 2. **Should the CLI talk to a facade, or directly to services with abstract interfaces?**
   - **Option A (Facade):** CLI → Facade → Services. Cleaner separation, easier testing.
   - **Option B (Direct + Protocols):** CLI → CalculationService (protocol) + MemoryService (protocol). Simpler, less indirection.
   - **Assumption:** Use **Option B** (protocols). Aligns with Python idiom; simpler to implement; tests can mock protocols directly.

### 3. **Who is responsible for linking Calculator → MemoryService (when failures occur)?**
   - **Current:** Never. Failures are not recorded.
   - **Assumption:** This is a **missing feature**, not part of separation. Don't add it during refactoring; preserve current behavior.
   - **Implication:** After refactoring, failures still won't be recorded automatically. That's fine; it's out of scope.

### 4. **Should abstract types be in a new module?**
   - **Option A:** Create `src/protocols/` directory with `calculation_service.py`, `memory_service.py`, `storage.py`
   - **Option B:** Add protocols to existing modules (e.g., `calculation_protocol.py` in services)
   - **Option C:** Use inline Protocol definitions (no new files)
   - **Assumption:** Use **Option A** for clarity. New `src/protocols/` module with 2-3 protocol files.

### 5. **Rename "CalculatorService" to avoid confusion with protocol?**
   - **Current:** `CalculatorService` implements the service, no separate name for the interface.
   - **Assumption:** Keep the name. Use `from src.protocols import CalculationService` (interface); concrete class remains `CalculatorService`.
   - **Implication:** No breaking API changes; type hints can reference protocol.

---

## Scope Boundaries

### IN SCOPE (must be addressed)
- Introduce abstract storage interface (base class or protocol)
- Introduce abstract service interfaces (protocols for calculation and memory)
- Make concrete services implement these interfaces
- Ensure CLI uses interfaces, not concrete types
- Preserve all external behavior and tests

### OUT OF SCOPE
- Rewrite calculation algorithms
- Add new features (e.g., auto-store failures in memory)
- Change CLI commands or flags
- Refactor the data models (`CalculationResult`, `MemoryEntry`, `CalculationStatistics`)
- Optimize performance
- Change JSON storage format (must maintain backward compatibility)

### BORDERLINE (clarify with stakeholder)
- Should `CalculatorService` automatically create `MemoryEntry` for all attempts? → NO, preserve current behavior
- Should storage classes share code? → No explicit code sharing required; just unified interface
- Should filters/statistics move to separate class? → No; keep as part of `MemoryService`

---

## Suggested Implementation Order

1. **Create protocols module** (`src/protocols/__init__.py`)
   - Define `Storage[T]` protocol (generic)
   - Define `CalculationService` protocol
   - Define `MemoryService` protocol

2. **Make storage classes implement protocol**
   - Update `JsonStorage` type hints
   - Update `MemoryJsonStorage` type hints
   - No code changes; just confirm they match protocol

3. **Update service constructors**
   - Change `CalculatorService.__init__(calculator: Calculator, storage: Storage)` (instead of `JsonStorage`)
   - Change `MemoryService.__init__(storage: Storage)` (instead of `MemoryJsonStorage`)
   - Allow dependency injection of protocol implementations

4. **Update CLI type hints**
   - Change `__init__(self, service: CalculationService, memory_service: MemoryService | None)`
   - Import protocols; use in type hints
   - No behavioral changes

5. **Test and verify**
   - Run all 433 tests → must all pass
   - Test `python -m src --operation add 3 5` → output unchanged
   - Test CLI interactive mode → behavior unchanged

---

## Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Storage implementations | 2 classes, no interface | 2 classes + 1 protocol |
| Service implementations | 2 classes, no interface | 2 classes + 2 protocols |
| Tests | 433 passing | 433 passing |
| CLI entry points | All working | All unchanged |
| Public method signatures | As-is | No breaking changes |
| Dependencies | Circular potential | Clearly acyclic |

---

## Risk Assessment

**Low Risk:**
- Adding protocols/abstract classes doesn't break concrete implementations
- Type hints are not enforced at runtime; old code still works
- Tests use mocks, so they're compatible with protocols

**Medium Risk:**
- Import paths change if protocols added to new module (need to update imports in services + CLI)
- Type checkers (mypy) will flag protocol mismatches if not careful

**High Risk:**
- None identified; this is a low-impact refactoring

---

## Files to Modify

| File | Change | Reason |
|------|--------|--------|
| `src/protocols/__init__.py` | **Create** | Define Storage, CalculationService, MemoryService protocols |
| `src/services/calculator_service.py` | **Minor** | Update type hints; no logic changes |
| `src/services/memory_service.py` | **Minor** | Update type hints; no logic changes |
| `src/storage/json_storage.py` | **Minor** | Add `# implements Storage` comment; verify signature match |
| `src/storage/memory_json_storage.py` | **Minor** | Add `# implements Storage` comment; verify signature match |
| `src/cli/calculator_cli.py` | **Minor** | Update type hints in `__init__` |
| `src/__main__.py` | **Minimal** | Update imports if protocols moved to new module |
| `tests/` | **No changes** | Tests should pass without modification |

---

## Success Criteria

1. All 433 tests pass without modification
2. `python -m src` runs identically before and after
3. All public interfaces (methods, return types, side effects) are unchanged
4. Type hints now reference protocols where appropriate
5. Coupling metrics improve (fewer direct dependencies on concrete classes)
6. Code review confirms component boundaries are now clear and formalized

