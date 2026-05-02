# Design: MemoryService Implementation (Task 04)

## Overview

Implement a `MemoryService` class and `MemoryEntryStorage` abstraction layer to manage MemoryEntry lifecycle separately from persistence mechanics.

## Files to Create

### 1. src/storage/memory_storage.py (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import List
from ..models.memory_entry import MemoryEntry


class MemoryEntryStorage(ABC):
    """
    Abstract base class for MemoryEntry persistence.
    
    Defines the interface for storing and loading MemoryEntry objects
    from persistent storage (file, database, etc.).
    """
    
    @abstractmethod
    def save(self, entry: MemoryEntry) -> None:
        """
        Persist a single MemoryEntry to storage.
        
        Args:
            entry: MemoryEntry object to persist.
        """
        
    @abstractmethod
    def load_all(self) -> List[MemoryEntry]:
        """
        Load all MemoryEntry objects from persistent storage.
        
        Returns:
            List of MemoryEntry objects loaded from storage.
            Returns empty list if no entries exist in storage.
        """
```

**Purpose:** Abstraction layer for MemoryEntry persistence, enabling multiple backend implementations.

---

### 2. src/services/memory_service.py (Service Class)

```python
from typing import List, Optional
from ..models.memory_entry import MemoryEntry
from ..storage.memory_storage import MemoryEntryStorage


class MemoryService:
    """
    Service for managing MemoryEntry objects.
    
    Handles storing and retrieving MemoryEntry objects in an in-memory collection
    with optional persistence to a storage backend.
    """
    
    def __init__(self, storage: Optional[MemoryEntryStorage] = None) -> None:
        """
        Initialize MemoryService.
        
        Args:
            storage: Optional storage backend for persisting MemoryEntry objects.
                    If None, entries are stored only in memory.
        """
        self._entries: List[MemoryEntry] = []
        self._storage: Optional[MemoryEntryStorage] = storage
        
    def store(self, entry: MemoryEntry) -> None:
        """
        Store a MemoryEntry in memory and optionally persist it.
        
        Args:
            entry: MemoryEntry object to store.
            
        Raises:
            TypeError: If entry is not a MemoryEntry instance.
        """
        if not isinstance(entry, MemoryEntry):
            raise TypeError(f"entry must be a MemoryEntry instance, got {type(entry).__name__}")
        self._entries.append(entry)
        if self._storage is not None:
            self._storage.save(entry)
            
    def retrieve(self) -> List[MemoryEntry]:
        """
        Retrieve all stored MemoryEntry objects.
        
        Returns:
            List of all MemoryEntry objects stored in this service.
            Returns empty list if no entries have been stored.
        """
        return self._entries
```

**Purpose:** In-memory service for managing MemoryEntry lifecycle with optional persistence.

**Behavior:**
- `__init__`: Initialize empty in-memory collection and optional storage backend
- `store(entry)`: Validate type, add to collection, optionally persist to storage
- `retrieve()`: Return all stored entries

---

### 3. tests/test_memory_service.py (Test Suite)

**Test Classes & Scenarios:**

#### TestMemoryServiceStore (8 tests)
- `test_store_adds_entry_to_collection` — Single entry storage
- `test_store_multiple_entries` — Sequential storage of 3 entries
- `test_store_successful_operation` — Entry with success=True
- `test_store_failed_operation` — Entry with success=False, error_message
- `test_store_preserves_entry_fields` — All 9 fields preserved
- `test_store_delegates_to_storage_if_provided` — Mock storage.save() called
- `test_store_does_not_call_storage_if_none` — No error when storage=None
- `test_store_raises_type_error_on_invalid_input` — TypeError for non-MemoryEntry

#### TestMemoryServiceRetrieve (7 tests)
- `test_retrieve_empty_initially` — Empty list on fresh service
- `test_retrieve_returns_all_stored_entries` — All 3 stored entries returned
- `test_retrieve_returns_entries_in_order` — Entries returned in store order
- `test_retrieve_includes_successful_entries` — Success entries not filtered
- `test_retrieve_includes_failed_entries` — Failed entries not filtered
- `test_retrieve_does_not_call_storage` — storage.load_all() NOT called
- `test_retrieve_returns_list_type` — Return type is list

#### TestMemoryServiceConstruction (3 tests)
- `test_init_with_no_storage` — Initializes without storage
- `test_init_with_storage` — Initializes with mock storage backend
- `test_init_creates_empty_collection` — Internal list starts empty

#### TestMemoryServiceEdgeCases (6 tests)
- `test_store_entry_with_none_result` — Failed operation (result=None)
- `test_store_entry_with_none_error_message` — Successful operation (error=None)
- `test_store_entry_with_large_operands` — Very large numbers
- `test_store_many_entries` — 100+ entries stored
- `test_retrieve_after_multiple_stores` — Alternate store/retrieve
- `test_storage_exception_propagates` — Exception from storage.save() propagates

**Total: 24 tests**

---

## Files NOT Modified

- src/models/memory_entry.py (unchanged, already exists)
- src/services/calculator_service.py (unchanged, integration is future task)
- src/storage/json_storage.py (unchanged)
- All other existing files

---

## Key Design Decisions

1. **Optional Storage Backend:** 
   - MemoryService works with or without persistent storage
   - Enables unit tests without file I/O
   - Future tasks can provide concrete implementations

2. **In-Memory First:**
   - Service owns in-memory lifecycle
   - store() updates memory immediately + optionally persists
   - retrieve() only returns in-memory entries

3. **No Bidirectional Sync:**
   - No automatic loading from storage at initialization
   - Loading (if needed) is a separate concern (future task)

4. **Type Validation:**
   - store() validates input is MemoryEntry instance
   - Provides clear error messages for misuse

5. **Separate Storage Abstraction:**
   - MemoryEntryStorage is distinct from JsonStorage
   - Allows independent persistence layer evolution

---

## Integration Points

**No integration with existing code in this task.**
- MemoryService is new; no dependencies on other services
- CalculatorService unchanged (integration is Task 05)
- JsonStorage unchanged (handles CalculationResult)
- MemoryEntry model unchanged (read-only)

---

## Implementation Order

1. Create src/storage/memory_storage.py (abstract base)
2. Create src/services/memory_service.py (service class)
3. Create tests/test_memory_service.py (test suite)
4. Run pytest to verify all 24 tests pass

---

## Expected Test Output

All 24 tests pass:
- TestMemoryServiceStore: 8 tests ✓
- TestMemoryServiceRetrieve: 7 tests ✓
- TestMemoryServiceConstruction: 3 tests ✓
- TestMemoryServiceEdgeCases: 6 tests ✓
- No failures, no errors
