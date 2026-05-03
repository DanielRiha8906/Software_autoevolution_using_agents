# Task 04 Analysis: MemoryService Implementation

## Task Summary

Implement a MemoryService that handles storing and retrieving MemoryEntry objects, with persistence details delegated to a separate storage layer. The service should provide `store(entry)` and `retrieve()` operations, ensure every completed calculation is recorded via the service, keep responsibilities limited to MemoryEntry lifecycle with no business logic, and be accessible via `python -m src` as both interactive menu and CLI flag.

---

## Current State Assessment

### What Exists: MemoryEntry

**File**: `src/models/memory_entry.py`

A complete dataclass that captures calculation attempts:
- **Fields**: 
  - `operation: str` — operation name (e.g., "add")
  - `operand_a: float`, `operand_b: float` — inputs
  - `result: float | None` — None if failed
  - `error: str | None`, `error_type: str | None` — error state
  - `timestamp: str` — ISO format creation time (auto-generated in `__post_init__()`)
  - `uuid: str` — UUID v4 identifier (auto-generated in `__post_init__()`)

- **Methods**:
  - `__post_init__()` — Auto-generates uuid and timestamp if not provided
  - `to_dict() -> dict` — Serialization for JSON
  - `from_dict(data: dict) -> MemoryEntry` — Deserialization with backward compatibility
  - `__str__() -> str` — Display format: "A SYMBOL B = RESULT" or "A SYMBOL B = ERROR: message"

**Status**: Fully implemented and tested (44 tests in test_memory_entry.py). This model is the backbone of the MemoryService.

### What Exists: JsonStorage

**File**: `src/storage/json_storage.py`

Handles JSON file persistence:
- **Constructor**: Takes `filepath: Path | str` to specify storage location
- **Methods**:
  - `save(result: MemoryEntry) -> None` — Appends entry to JSON file
  - `load_all() -> list[MemoryEntry]` — Reads all entries from JSON file
  - `_read_raw() -> list` — Internal: reads JSON, handles missing/invalid files
  - `_write_raw(records: list) -> None` — Internal: writes JSON with formatting

**Key detail**: This class is **not** a MemoryService. It is a storage adapter that handles the mechanics of persistence (file I/O, JSON serialization). It has no knowledge of business logic.

**Status**: Fully implemented. Works with MemoryEntry serialization.

### What Exists: CalculatorService

**File**: `src/services/calculator_service.py`

Current responsibilities:
- `perform(operation: Operation, a: float, b: float) -> MemoryEntry`
  - Calls Calculator to compute
  - Wraps result/error in MemoryEntry
  - **Calls storage.save() directly** — persists to JsonStorage
  - Returns the entry
- `get_history() -> list[MemoryEntry]`
  - **Delegates directly to storage.load_all()** — retrieves from JsonStorage

**Current design flaw**: CalculatorService is tightly coupled to JsonStorage. It knows how and when to persist, violating the separation of concerns principle outlined in the task.

### What Exists: CLI Layer

**File**: `src/cli/calculator_cli.py`

- `run_interactive()` — Interactive menu loop
  - Gets user choices for operations
  - Calls `service.perform()`
  - Displays result or error
  - Can view history via menu option
- `run_command(operation_str, a, b)` — One-shot mode
  - Parses operation
  - Calls `service.perform()`
  - Prints result or exits with error
- `_show_history()` — Displays all entries
  - Calls `service.get_history()`
  - Iterates and prints each entry

**Integration**: Currently retrieves history directly from CalculatorService, which in turn gets it from JsonStorage. No intermediate memory service layer.

### What Exists: CLI Entry Point

**File**: `src/__main__.py`

- `--show-history` flag — displays history and exits
- `--operation OP A B` — one-shot calculation
- Interactive menu (default) — full interactive session

**Status**: Fully wired and functional.

---

## What Is Missing: MemoryService

The task explicitly asks for a **MemoryService** class. Currently, there is **no such class**.

### What MemoryService Should Do

Based on task requirements and architecture principles:

1. **Provide memory-specific operations**:
   - `store(entry: MemoryEntry) -> None` — Record a calculation attempt
   - `retrieve() -> list[MemoryEntry]` — Get all recorded entries

2. **Encapsulate MemoryEntry lifecycle**:
   - Accept entries (no creation/modification)
   - Persist them via storage layer
   - Retrieve them from storage layer
   - **Never** perform calculations, apply business logic, or validate operation types

3. **Delegate persistence to storage**:
   - Use injected storage instance (likely JsonStorage)
   - Never handle file I/O directly
   - Never know details of JSON serialization

4. **Be accessible via CLI**:
   - History retrieval via `--show-history` flag (already implemented)
   - Interactive history viewing via menu (already implemented)
   - **Possibly**: new CLI commands for memory management (e.g., clear history, export entries) — *not explicitly required by acceptance criteria*

### Design Pattern

```python
class MemoryService:
    def __init__(self, storage: Storage):
        self.storage = storage
    
    def store(self, entry: MemoryEntry) -> None:
        """Record a calculation attempt."""
        self.storage.save(entry)
    
    def retrieve(self) -> list[MemoryEntry]:
        """Get all recorded entries."""
        return self.storage.load_all()
```

This is a **thin adapter** layer that:
- Abstracts storage details from business logic
- Provides a domain-focused API (memory-specific terms: store/retrieve)
- Allows future storage implementations without changing calling code

### How MemoryService Fits Into The Architecture

**Current flow** (without MemoryService):
```
CalculatorService.perform()
    ├─> Calculator.calculate()
    └─> JsonStorage.save() [direct call]

CalculatorService.get_history()
    └─> JsonStorage.load_all() [direct call]
```

**Desired flow** (with MemoryService):
```
CalculatorService.perform()
    ├─> Calculator.calculate()
    └─> MemoryService.store()
        └─> JsonStorage.save()

CalculatorService.get_history()
    └─> MemoryService.retrieve()
        └─> JsonStorage.load_all()
```

**Benefit**: CalculatorService no longer imports or knows about JsonStorage. If you want to switch storage backends (e.g., SQLite, in-memory, cloud database), you only change MemoryService's constructor, not CalculatorService.

---

## Current Integration Points

### Where Calculations Are Recorded

**File**: `src/services/calculator_service.py`, `perform()` method

Currently:
```python
def perform(self, operation: Operation, a: float, b: float) -> MemoryEntry:
    try:
        result = self.calculator.calculate(operation, a, b)
        entry = MemoryEntry(...)
    except Exception as e:
        entry = MemoryEntry(..., error=str(e), error_type=type(e).__name__)
    
    self.storage.save(entry)  # <-- Direct storage call
    return entry
```

**Change required**: Replace `self.storage.save(entry)` with `self.memory_service.store(entry)`.

### Where History Is Retrieved

**File**: `src/services/calculator_service.py`, `get_history()` method

Currently:
```python
def get_history(self) -> list[MemoryEntry]:
    return self.storage.load_all()  # <-- Direct storage call
```

**Change required**: Replace with `return self.memory_service.retrieve()`.

### CLI Access Points

Both are already implemented and working:
1. **Interactive history**: Menu option in `CalculatorCLI._show_history()` calls `service.get_history()`
2. **CLI flag**: `python -m src --show-history` calls `cli._show_history()`

**No changes needed** — the CLI is already calling the right methods (CalculatorService.get_history()). Once MemoryService is added, these will automatically use it (if CalculatorService is updated to delegate to MemoryService).

---

## MemoryEntry Field Explanation

For context on what MemoryService stores:

| Field | Type | Populated By | Use Case |
|-------|------|--------------|----------|
| `operation` | `str` | CalculatorService during perform() | What calculation was attempted |
| `operand_a` | `float` | CalculatorService during perform() | First input value |
| `operand_b` | `float` | CalculatorService during perform() | Second input value |
| `result` | `float \| None` | Calculator result or None on error | Successful calculation output |
| `error` | `str \| None` | Exception message or None | Human-readable error description |
| `error_type` | `str \| None` | Exception class name or None | Programmatic error type (e.g., "ValueError") |
| `timestamp` | `str` | Auto-generated by MemoryEntry.__post_init__() | ISO format time of record creation |
| `uuid` | `str` | Auto-generated by MemoryEntry.__post_init__() | Unique identifier for record retrieval/updates |

The MemoryService should **never modify** these fields — it only passes entries through to storage.

---

## Persistence Layer (JsonStorage)

### Current Implementation

**File**: `src/storage/json_storage.py`

Handles all file I/O and JSON formatting:
- Reads `calculations.json` from disk
- Parses JSON into list of dicts
- Each dict is converted to MemoryEntry via `MemoryEntry.from_dict()`
- When saving, reverses the process: MemoryEntry → dict → JSON string → file

### Backward Compatibility

JsonStorage handles old CalculationResult format (which lacks uuid, error, error_type):
- On deserialization: `MemoryEntry.from_dict()` auto-generates missing fields
- On serialization: `MemoryEntry.to_dict()` always includes all fields
- Old entries gain uuid and null error fields when loaded

---

## Storage Abstraction

### Why JsonStorage Is NOT MemoryService

JsonStorage is a **storage adapter**:
- It knows about JSON, file paths, parsing, formatting
- It has no understanding of memory, entries, or semantics
- It is low-level (data persistence mechanics)

MemoryService is a **domain service**:
- It knows about MemoryEntry lifecycle (store/retrieve semantics)
- It coordinates with storage without knowing storage details
- It is high-level (business logic coordination)

### Future Storage Flexibility

If someone wanted to use SQLite instead of JSON, the change would be:
1. Create `SqliteStorage` with same interface (`save()`, `load_all()`)
2. Update `MemoryService.__init__()` to accept it
3. Update `__main__.py` to instantiate SqliteStorage instead of JsonStorage
4. **No changes** to CalculatorService, CLI, or business logic

Without MemoryService, you'd have to change CalculatorService too, creating coupling.

---

## Acceptance Criteria Verification

| Criterion | Current Status | What's Needed |
|-----------|----------------|---------------|
| MemoryService provides `store(entry)` | ❌ Not implemented | Create MemoryService with store() method |
| MemoryService provides `retrieve()` | ❌ Not implemented | Create MemoryService with retrieve() method |
| Every calculation recorded via service | ⚠️ Recorded directly to storage | Update CalculatorService to call MemoryService.store() |
| Persistence details not in MemoryService | ✅ Already true for new class | Keep MemoryService delegation-only |
| Service responsibilities limited to lifecycle | ✅ Will be if designed correctly | No business logic in MemoryService |
| Accessible via `python -m src` interactive menu | ✅ Already working | No changes needed (uses existing get_history()) |
| Accessible via `python -m src --show-history` | ✅ Already working | No changes needed (uses existing get_history()) |

---

## Scope Signals

### In Scope (Required)
- Create MemoryService class with store(entry) and retrieve() methods
- Update CalculatorService to use MemoryService for persistence
- Ensure all existing CLI functionality continues to work
- Write tests for MemoryService operations

### Out of Scope (Not Required)
- Refactoring JsonStorage (it already works)
- Changing MemoryEntry structure (it already works)
- New CLI commands (history is already exposed)
- GUI features (not applicable)
- Performance optimization (beyond current)
- Migration of old data (backward compat already built in)

### Borderline (Depends on Implementation Details)
- Storage interface abstraction (abstract base class or protocol) — useful for testability and future flexibility, but not strictly required by criteria
- Memory statistics (count, oldest entry, newest entry) — could be nice-to-have, not required

---

## Files Affected

### Must Create
- `src/services/memory_service.py` — NEW class with store() and retrieve() methods

### Must Modify
- `src/services/calculator_service.py`
  - Add import: `from .memory_service import MemoryService`
  - Update `__init__()` to accept MemoryService (inject dependency)
  - Update `perform()` to call `self.memory_service.store(entry)` instead of `self.storage.save(entry)`
  - Update `get_history()` to call `self.memory_service.retrieve()` instead of `self.storage.load_all()`
  - Can remove direct dependency on JsonStorage

- `src/services/__init__.py`
  - Add export: `from .memory_service import MemoryService`

- `src/__main__.py`
  - Update `_build_service()` to instantiate MemoryService
  - Pass MemoryService to CalculatorService constructor

### No Changes Needed
- `src/models/memory_entry.py` — complete
- `src/storage/json_storage.py` — complete and correct
- `src/cli/calculator_cli.py` — calls through service, will work automatically
- `artifacts/` diagrams — architect will update after implementation
- `tests/test_*_existing.py` — most will work as-is; may need minor updates for new service

---

## Design Questions & Assumptions

### 1. Dependency Injection vs. Direct Instantiation

**Question**: Should CalculatorService receive MemoryService as a constructor parameter, or instantiate it internally?

**Assumption**: Use **constructor injection**. This allows:
- Testing with mock storage
- Swapping storage backends without code changes
- Clear dependency declaration

Pattern:
```python
service = CalculatorService(calculator, memory_service)
```

### 2. Storage Backend Abstraction

**Question**: Should MemoryService depend on an abstract Storage interface, or concrete JsonStorage?

**Assumption**: Start with **concrete dependency** on JsonStorage. If multiple storage backends become needed, add an abstract interface later (ABC or Protocol).

Rationale: Simpler now, extensible later.

### 3. Bidirectional Reference

**Question**: Should JsonStorage know about MemoryEntry?

**Assumption**: **Yes**. JsonStorage is specifically designed for this. It already:
- Serializes MemoryEntry to dict via `to_dict()`
- Deserializes dict to MemoryEntry via `from_dict()`
- Handles backward compatibility

This is correct — JsonStorage is the persistence layer for MemoryEntry.

### 4. Error Handling

**Question**: If storage.save() fails (e.g., disk full), should MemoryService re-raise, or silently fail?

**Assumption**: **Propagate exceptions**. Let the caller decide what to do (CalculatorService will decide whether to re-raise or return error state).

### 5. History Ordering

**Question**: Should `retrieve()` return entries in insertion order, or allow sorting?

**Assumption**: **Insertion order**. JsonStorage returns them in file order (oldest first). MemoryService should preserve this.

---

## Testing Strategy

### MemoryService Tests

**File**: `tests/test_memory_service.py` (new)

Test scenarios:
1. **store()** — Entry is passed to storage
   - `test_store_calls_storage_save()`
   - `test_store_with_success_entry()`
   - `test_store_with_error_entry()`
   - `test_store_multiple_entries()`

2. **retrieve()** — Returns list from storage
   - `test_retrieve_calls_storage_load_all()`
   - `test_retrieve_empty_history()`
   - `test_retrieve_multiple_entries()`
   - `test_retrieve_preserves_order()`

3. **Integration** — Works with real JsonStorage
   - `test_store_and_retrieve_round_trip()`
   - `test_store_error_and_success_entries()`

### Integration Tests

**Update**: `tests/test_calculator_service.py`

- Update `_build_service()` mock to use MemoryService
- Verify `perform()` still returns MemoryEntry
- Verify `get_history()` still returns list

### End-to-End Tests

**Existing tests** — Most will pass unchanged:
- `tests/test_cli.py` — Uses service, doesn't care about MemoryService
- `tests/test_main_show_history.py` — Uses CLI, doesn't care about MemoryService

---

## Implementation Order

1. **Create MemoryService** (`src/services/memory_service.py`)
   - Simple class: store() and retrieve() methods
   - Inject JsonStorage as dependency

2. **Update CalculatorService**
   - Add MemoryService as constructor parameter
   - Update perform() to call memory_service.store()
   - Update get_history() to call memory_service.retrieve()
   - Remove direct JsonStorage usage

3. **Update __main__.py**
   - Instantiate MemoryService with JsonStorage
   - Pass MemoryService to CalculatorService

4. **Write tests** for MemoryService

5. **Verify end-to-end**
   - Run all existing tests — should pass
   - Run `python -m src --show-history`
   - Run `python -m src --operation add 3 5`
   - Run interactive mode with history option

---

## Key Insights

1. **MemoryEntry is ready** — Fully implemented, tested, and battle-hardened. No changes needed.

2. **JsonStorage is ready** — Handles all persistence details correctly, including backward compatibility.

3. **The gap**: No **MemoryService** exists. Currently CalculatorService directly calls JsonStorage, creating coupling.

4. **The fix**: Add thin MemoryService layer that CalculatorService calls instead. This separates concerns and enables flexibility.

5. **CLI already works**: Interactive menu and --show-history flag are fully functional. They'll continue to work once MemoryService is added, because they call through CalculatorService.

6. **Minimal changes required**:
   - Create 1 new file (~20 lines)
   - Modify 2 existing files (~10 lines each)
   - Add tests
   - No changes to CLI, models, or storage

---

## Notes on "Every Calculation Recorded"

The acceptance criterion "every completed calculation is recorded via the service" is already satisfied **in principle** — CalculatorService.perform() calls storage.save() for every result (success or error). 

The task requirement is to ensure this happens **via MemoryService** instead of directly. This enforces proper separation of concerns: CalculatorService should not know about storage details.

