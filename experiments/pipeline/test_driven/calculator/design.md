# Task 04 Design: MemoryService Implementation

## 1. Class Definition

### MemoryService Structure

```python
class MemoryService:
    """Service for managing MemoryEntry domain objects in-memory.
    
    Provides store() and retrieve() methods for lifecycle management without
    any persistence logic. All file I/O responsibilities are delegated to the
    storage layer (JsonStorage).
    
    This is a stateful service that accumulates entries for the duration of
    the application session.
    """
    
    def __init__(self) -> None:
        """Initialize MemoryService with an empty entry list.
        
        Constructor takes no arguments. Internal state is initialized here.
        """
        self._entries: list[MemoryEntry] = []
```

### Why this constructor design:

- Takes NO arguments because the test requirements explicitly state constructor takes no required arguments
- Aligns with the principle of separation of concerns: MemoryService does NOT instantiate or own storage; it only manages in-memory entries
- Storage integration happens at a higher level (e.g., in CalculatorService or CLI layer), not within MemoryService
- Simpler to test: no setup of dependencies needed; test can instantiate with `MemoryService()`

---

## 2. Methods

### Method Signatures and Specifications

```python
def store(self, entry: MemoryEntry) -> None:
    """Store a MemoryEntry in memory.
    
    Args:
        entry: A MemoryEntry domain object with auto-generated id and timestamp.
    
    Returns:
        None
    
    Behavior:
        - Accepts the entry as-is (does not modify id or timestamp)
        - Appends entry to internal list
        - Does NOT validate, serialize, or persist to any storage
        - Does NOT raise exceptions on duplicate IDs (allows identical entries)
    """
```

```python
def retrieve(self) -> list[MemoryEntry]:
    """Retrieve all stored MemoryEntry objects.
    
    Returns:
        list[MemoryEntry]: A list of all entries in order of insertion.
                          Returns empty list if no entries have been stored.
    
    Behavior:
        - Returns a reference to the internal list (not a copy)
        - Preserves insertion order
        - Preserves all fields (id, timestamp, operation, operands, result, success, execution_time_ms)
        - Does NOT filter, sort, or transform entries
    """
```

### No Helper Methods

- The implementation is simple enough that no private or helper methods are needed
- The internal `_entries` list requires no synchronization logic (single-threaded context)
- No UUID generation, timestamp manipulation, or serialization helpers needed (MemoryEntry handles those)

---

## 3. Type Hints

### Imports Required

```python
from ..models.memory_entry import MemoryEntry
```

### Full Type Annotation Strategy

- All method parameters and return types have explicit type hints
- Use `MemoryEntry` (imported from models) for domain type
- Use `list[MemoryEntry]` for return type (Python 3.9+ syntax, matching existing codebase)
- Use `None` return type for store() method
- No circular imports possible: MemoryService imports MemoryEntry, MemoryEntry does not import MemoryService

---

## 4. File Layout

### Create: `src/services/memory_service.py`

Location: `src/services/memory_service.py`

Content structure:
1. Imports (only MemoryEntry from models)
2. Class docstring
3. Constructor with docstring and `_entries: list[MemoryEntry] = []` initialization
4. `store(self, entry: MemoryEntry) -> None` method
5. `retrieve(self) -> list[MemoryEntry]` method

### Update: `src/services/__init__.py`

Current content:
```python
from .calculator import Calculator
from .calculator_service import CalculatorService

__all__ = ["Calculator", "CalculatorService"]
```

Add MemoryService to imports and __all__:
```python
from .calculator import Calculator
from .calculator_service import CalculatorService
from .memory_service import MemoryService

__all__ = ["Calculator", "CalculatorService", "MemoryService"]
```

### Create: `tests/test_memory_service.py`

Location: `tests/test_memory_service.py`

Content structure (tests are pre-written; this section documents where they go):
1. Import MemoryService from src.services
2. Import MemoryEntry from src.models
3. Five test methods (provided in requirements):
   - `test_memory_service_can_store_entry()`
   - `test_memory_service_retrieve_returns_stored_entries()`
   - `test_memory_service_stores_multiple_entries()`
   - `test_memory_service_retrieve_returns_list()`
   - `test_memory_service_does_not_contain_file_io()`

---

## 5. Key Design Decisions

### Decision 1: Why Use a Simple List for Storage?

**Choice:** Use `list[MemoryEntry]` as the internal data structure.

**Rationale:**
- List preserves insertion order (predictable behavior for testing and user comprehension)
- No index lookup or search requirements (tests only call retrieve() to get all entries)
- Simple semantics: O(1) append, O(n) retrieve (acceptable for calculator session scope)
- Matches the pattern of JsonStorage's internal representation: it also works with lists
- No need for deduplication or uniqueness constraints (tests allow duplicates)

### Decision 2: Why No Constructor Parameters?

**Choice:** Constructor takes no arguments; initialize `_entries = []` directly in `__init__`.

**Rationale:**
- Test requirement explicitly states "Constructor takes no required arguments"
- MemoryService is a pure domain service, not a configuration container
- Separation of concerns: service manages entries, not storage configuration or dependencies
- Storage integration happens at orchestration level
- Simplifies instantiation: `MemoryService()` vs. `MemoryService(storage=...)`

### Decision 3: Why No Storage Layer Integration in MemoryService?

**Choice:** MemoryService contains ONLY store() and retrieve(). No save() or load_all() methods that call JsonStorage.

**Rationale:**
- Clean separation of layers: domain service ≠ persistence service
- MemoryService is responsible for in-memory lifecycle ONLY
- JsonStorage is responsible for file I/O ONLY
- Orchestration layer (e.g., CalculatorService or CLI) composes these services
- Test constraint: "No file I/O or JSON serialization in MemoryService source" enforces this boundary

### Decision 4: How This Fits the Existing Architecture

**Pattern:**
- `Calculator` — pure function collection (no state, no I/O)
- `CalculatorService` — orchestrates calculation + persistence
- `JsonStorage` — handles file I/O and JSON serialization
- `MemoryService` — stateful complement to Calculator, manages transient in-session entries

---

## 6. Test Plan Summary

The 5 test cases validate all requirements:

### Test 1: `test_memory_service_can_store_entry()`
- Verify method exists and accepts the correct type

### Test 2: `test_memory_service_retrieve_returns_stored_entries()`
- Verify entries are actually stored and can be retrieved

### Test 3: `test_memory_service_stores_multiple_entries()`
- Verify accumulation, no overwrite, multiple entries in insertion order

### Test 4: `test_memory_service_retrieve_returns_list()`
- Verify return type contract (not tuple, not custom iterable)

### Test 5: `test_memory_service_does_not_contain_file_io()`
- Verify implementation does not include persistence logic

---

## 7. Implementation Checklist for Programmer

1. Create `src/services/memory_service.py`
   - Import MemoryEntry from `..models.memory_entry`
   - Define MemoryService class
   - Implement `__init__(self) -> None` with `self._entries: list[MemoryEntry] = []`
   - Implement `store(self, entry: MemoryEntry) -> None` with `self._entries.append(entry)`
   - Implement `retrieve(self) -> list[MemoryEntry]` with `return self._entries`

2. Update `src/services/__init__.py`
   - Add import: `from .memory_service import MemoryService`
   - Add to __all__: `"MemoryService"`

3. Create test file with provided test cases (tester will handle this)

---

## 8. Code Skeleton

```python
# src/services/memory_service.py

from ..models.memory_entry import MemoryEntry


class MemoryService:
    """Service for managing MemoryEntry domain objects in-memory."""

    def __init__(self) -> None:
        """Initialize MemoryService with an empty entry list."""
        self._entries: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """Store a MemoryEntry in memory.
        
        Args:
            entry: A MemoryEntry domain object.
        """
        # Implementation: one line

    def retrieve(self) -> list[MemoryEntry]:
        """Retrieve all stored MemoryEntry objects.
        
        Returns:
            list[MemoryEntry]: All entries in insertion order.
        """
        # Implementation: one line
```
