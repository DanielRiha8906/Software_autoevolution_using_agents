# Analysis: MemoryService Implementation (Task 04)

## What the task is asking for

The task requires implementing a `MemoryService` class that acts as an intermediary for managing `MemoryEntry` objects. The service should handle storing and retrieving memory entries while keeping persistence (file I/O, serialization) in a separate storage layer. This separates the concerns of memory management logic from the concrete storage implementation.

## Current Architecture

**What exists:**
- `MemoryEntry` dataclass (src/models/memory_entry.py): 9 fields with full serialization support
  - Tracks operation, operands, result, success/error state, timestamp, execution_time_ms, entry_id
  - Already supports both successful and failed operations
  - Has to_dict() / from_dict() for JSON compatibility

- `CalculationResult` dataclass: Only tracks successful calculations
  - No entry ID, no failure tracking
  - Separate from MemoryEntry (not yet integrated)

- `JsonStorage` class: Persists CalculationResult to JSON
  - Handles file I/O, JSON serialization
  - Uses Path from pathlib
  - No support for MemoryEntry yet

- `CalculatorService`: Currently orchestrates calculations and saves via storage
  - Calls Calculator.calculate(), wraps in CalculationResult, saves to storage
  - Does NOT currently handle error cases (exceptions propagate up)
  - Does NOT create MemoryEntry objects
  - Does NOT attempt to record failed calculations

## Key Findings

1. **MemoryEntry exists but is unused**: It's fully implemented with 31 passing tests but not integrated into the calculation flow.

2. **Current flow only saves successful operations**: CalculatorService saves CalculationResult only after successful calculation. Failed operations throw exceptions before any recording happens.

3. **Persistence layer exists but for CalculationResult**: JsonStorage is purpose-built for CalculationResult, not MemoryEntry.

4. **Clear separation concern**: The task explicitly requires persistence details to NOT be in MemoryService. This means:
   - MemoryService: in-memory lifecycle (store/retrieve operations on MemoryEntry objects)
   - Separate storage layer: handles actual persistence (file I/O, serialization)

## Design Assumptions

1. **"Completed calculation" means attempted and finished** (success or failure)
2. **MemoryService maintains in-memory collection** with optional injected storage backend
3. **MemoryEntry objects are created by orchestrator** (likely CalculatorService in future tasks)
4. **retrieve() returns all stored MemoryEntry objects**

## Implementation Scope

**In Scope:**
- Create `MemoryService` class with store(entry) and retrieve() methods
- MemoryService owns the MemoryEntry lifecycle logic (not persistence mechanics)
- Optional storage backend abstraction
- Unit tests for store/retrieve behavior

**Out of Scope (per acceptance criteria):**
- Persistence details (file I/O, JSON serialization) — stay in storage layer
- Business logic (calculation, validation)
- Direct integration with CalculatorService (design task)
- Changes to MemoryEntry structure

## Implementation Strategy

1. Create `MemoryService` class with:
   - `store(entry: MemoryEntry)` - adds entry to in-memory collection
   - `retrieve() -> List[MemoryEntry]` - returns all stored entries
   - Optional storage backend dependency

2. Add unit tests for store/retrieve operations

3. Update diagrams to reflect new service layer
