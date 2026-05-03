# Task 07 Analysis: ImportExportService for MemoryEntry Records

## Task Overview

Implement an `ImportExportService` that provides JSON serialization/deserialization capabilities for `MemoryEntry` records. This service must support:
1. Exporting MemoryEntry objects from MemoryService to JSON files
2. Importing MemoryEntry objects from JSON files back into MemoryService
3. Safe merging on import (preserve existing entries, skip duplicates)
4. Validation of JSON schema on import
5. CLI/interactive menu integration via `python -m src`

## Current State: Files and Implementations

### Existing Models and Services

#### MemoryEntry (src/models/memory_entry.py)
- Dataclass with 7 fields: `operation`, `operands`, `result`, `success`, `execution_time_ms`, `id`, `timestamp`
- `id` field is auto-generated (uuid4) as a string
- `timestamp` is auto-generated in ISO 8601 format via `__post_init__()` if not provided
- Already implements `to_dict()` for serialization → returns all 7 fields as dict
- Already implements `from_dict(cls, data)` classmethod for deserialization
- Round-trip serialization fully preserves all fields including id and timestamp

#### MemoryService (src/services/memory_service.py)
- Manages MemoryEntry objects in-memory via internal list `_entries: list[MemoryEntry]`
- `store(entry: MemoryEntry) -> None` — appends entries to list
- `retrieve() -> list[MemoryEntry]` — returns all entries in insertion order
- `query(operation: Optional[str], success: Optional[bool]) -> list[MemoryEntry]` — filters entries
- Already supports checking if an ID exists (by iterating entries)
- Contains NO file I/O or JSON handling (per design)

#### JsonStorage (src/storage/json_storage.py)
- Handles CalculationResult JSON serialization/persistence
- Pattern: reads list from file, appends dict, writes list back
- Uses `json.load()` and `json.dump()` with indentation
- Creates parent directories as needed (`mkdir(parents=True, exist_ok=True)`)
- Gracefully handles missing files and corrupted JSON

#### CalculatorCLI (src/cli/calculator_cli.py)
- Interactive menu-driven interface
- Dynamically calculates menu options (currently 8 operations + View History + Exit)
- Menu option numbering: operations 1-8, View history at position `len(MENU)+1`, Exit at `len(MENU)+2`
- Also supports one-shot mode via `run_command(operation_str, a, b)` called from `__main__.py`

#### Entry Point (src/__main__.py)
- Uses `argparse.ArgumentParser` for CLI argument parsing
- Accepts `--operation` flag with specific choices (add, subtract, multiply, divide, square, sqrt, power, modulo)
- Requires exactly 2 operands when `--operation` is provided
- Without flags, runs interactive mode via `cli.run_interactive()`
- Pattern: build service with dependency injection, then create CLI and dispatch

### Package Exports
- `src/services/__init__.py` exports: Calculator, CalculatorService, MemoryService, StatisticsService
- `src/models/__init__.py` exports: Operation, CalculationResult, MemoryEntry, StatisticsResult
- `src/storage/__init__.py` exports: JsonStorage

### Test Patterns
- Use pytest fixtures for temporary directories (`tmp_path` fixture)
- Test helper functions (e.g., `_make_entry()` with kwargs for customization)
- Tests import from `src.models` and `src.services` directly
- JsonStorage tests verify: missing files, save/load round-trips, data persistence, corrupted JSON handling, parent directory creation
- MemoryService tests verify: store, retrieve, query filtering, no file I/O

## What Needs to be Created

### 1. ImportExportService Class
**Location:** `src/services/import_export_service.py`

Required interface (from task requirements):
```python
class ImportExportService:
    def export(self, memory_service: MemoryService, filepath: Path | str) -> None:
        """Export MemoryEntry records from MemoryService to JSON file.
        
        - Retrieves all entries from memory_service via retrieve()
        - Converts each MemoryEntry to dict via to_dict()
        - Writes list of dicts as JSON to filepath
        - Creates parent directories if needed
        """

    def import_entries(self, memory_service: MemoryService, filepath: Path | str) -> None:
        """Import MemoryEntry records from JSON file into MemoryService.
        
        - Reads JSON file
        - Validates structure (should be list of dicts)
        - For each entry dict:
          - Create MemoryEntry via from_dict()
          - Check if entry.id already exists in memory_service
          - If exists: skip (preserve existing, no overwrite)
          - If not exists: store via memory_service.store()
        - Raise Exception on invalid JSON schema
        """
```

**Key design decisions:**
- Constructor should accept MemoryService dependency injection? Or methods take MemoryService as parameter?
  - Task spec shows methods taking MemoryService as parameter → implement that way
- Validation: must check that JSON is valid JSON and structure is a list
- Duplicate detection: by ID comparison, not by full entry equality
- No overwriting: skip duplicates, don't raise errors on them
- File path handling: follow JsonStorage pattern (parent dir creation, Path normalization)

### 2. Integration Points

#### src/services/__init__.py
- Add ImportExportService to imports: `from .import_export_service import ImportExportService`
- Add to `__all__`: `"ImportExportService"`

#### src/__main__.py Updates
- Add argparse flag: `--export FILEPATH` to export current memory to JSON
- Add argparse flag: `--import FILEPATH` to import memory from JSON
- OR add to interactive menu if export/import should only be interactive
- Task requirement states: "Must be accessible via python -m src (interactive menu and CLI flag)"
  - Interpret as: both interactive menu option AND CLI flags must work
  - Interactive menu: add two menu options (e.g., "Export memory" and "Import memory")
  - CLI flags: add `--export` and `--import` arguments
  
#### src/cli/calculator_cli.py Updates
- Add methods to handle export/import:
  - `def export_memory(self, filepath: str) -> None` — calls service export, prints confirmation
  - `def import_memory(self, filepath: str) -> None` — calls service import, prints confirmation
- Add menu options (e.g., positions after statistics, before Exit):
  - "Export to JSON"
  - "Import from JSON"
- Prompt for file path in interactive mode if user selects export/import

#### Service Integration
- Need to decide: should CalculatorService or a new service coordinate with ImportExportService?
  - Current pattern: CalculatorService orchestrates Calculator and JsonStorage
  - MemoryService is standalone (no file I/O)
  - Create ImportExportService to handle MemoryEntry JSON I/O only
  - CalculatorService likely doesn't need changes (it works with CalculationResult, not MemoryEntry)
  - ImportExportService should be independent service for MemoryEntry I/O

### 3. Test Suite

**Location:** `tests/test_import_export_service.py`

Required tests (from task spec):
- `test_export_creates_valid_json_file` — verify JSON file contains list of entry dicts
- `test_import_loads_entries` — verify entries from JSON loaded into MemoryService
- `test_import_validates_structure` — invalid JSON structure raises Exception
- `test_import_preserves_existing_entries` — existing entries not overwritten
- `test_import_skips_duplicate_entries` — duplicate IDs skipped on import

Additional tests (coverage):
- Export empty memory service (creates empty list in JSON)
- Export multiple entries (preserves all fields)
- Import from missing file (handle gracefully)
- Import corrupted JSON (raise Exception)
- Round-trip: export then import restores all data
- Import with mixed new and existing entries

## What Exists and Does NOT Need to Change

### Read-Only / Stable
- MemoryEntry model: fully functional, already has to_dict() and from_dict()
- MemoryService: fully functional, no changes needed
- JsonStorage: pattern can be followed but focused on CalculationResult
- CalculatorCLI: can be extended with new methods without changing existing ones
- All existing tests: should remain passing

## Ambiguities and Working Assumptions

1. **Should MemoryService be integrated with CalculatorService?**
   - Assumption: No. MemoryService is independent, CalculatorService works with CalculationResult.
   - Task only mentions ImportExportService for MemoryEntry records.

2. **Where should ImportExportService be instantiated?**
   - Assumption: In `__main__.py`, build service similar to CalculatorService
   - Pass it to CLI for interactive dispatch

3. **Should import prompt user if file not found?**
   - Assumption: Raise exception, let caller handle (consistent with JsonStorage pattern)
   - However, interactive CLI can catch and prompt retry

4. **JSON schema validation — how strict?**
   - Assumption: Must be a list at top level, each element must be dict-like with at least required MemoryEntry fields
   - If MemoryEntry.from_dict() succeeds, schema is valid
   - Catch exceptions during from_dict() and raise as generic Exception

5. **Menu integration — where to add export/import options?**
   - Assumption: After operation menu items, before "View history", since those are data management operations
   - Or after "View history" to keep utility options together
   - Task doesn't specify, so flexibility here

6. **CLI flags for export/import — one-shot or interactive?**
   - Assumption: One-shot with filepath argument
   - `python -m src --export /path/to/file.json` exports and exits
   - `python -m src --import /path/to/file.json` imports and exits
   - Cannot combine with `--operation` (mutually exclusive)

## Scope Signals

### In Scope
- ImportExportService class with export() and import_entries() methods
- JSON file I/O using standard library json module
- Duplicate detection by entry ID
- Safe merging (skip duplicates, preserve existing)
- Schema validation
- Both CLI flag and interactive menu access
- New test file with at least 5 specified tests
- Integration with existing MemoryService (no modification to MemoryService itself)

### Explicitly Out of Scope
- Modifications to MemoryEntry or MemoryService internals
- Changes to CalculatorService or its integration
- GUI enhancements
- Database instead of JSON
- Batch operations (export/import works with single file at a time)

### Borderline
- Whether to create MemoryService instance in __main__ or reuse from CalculatorService
  - Currently, CalculatorService has its own storage but doesn't use MemoryService
  - Task creates isolated ImportExportService for MemoryEntry, separate concern

## Key Integration Points

1. **File location:** Import/export from where?
   - Assumption: Allow user-specified path (no fixed location)
   - Pattern: Follow JsonStorage which takes path in constructor

2. **Menu positioning:** Where in CLI menu?
   - Current menu: 8 operations, View History, Exit
   - Add: Export Memory (position 10), Import Memory (position 11)

3. **MemoryService instantiation:** Currently not used anywhere in main
   - Need to create MemoryService instance in __main__.py if not already done
   - Pass to CLI for interactive dispatch

4. **Error handling:**
   - Missing file on import: raise Exception (can be FileNotFoundError)
   - Invalid JSON: raise Exception (json.JSONDecodeError)
   - Schema validation: raise Exception on structural mismatch

## Implementation Checklist for Next Phase

1. Create `src/services/import_export_service.py` with class and two methods
2. Update `src/services/__init__.py` with ImportExportService export
3. Create MemoryService instance in `src/__main__.py`
4. Create ImportExportService instance in `src/__main__.py`
5. Pass both to CalculatorCLI (or create new method to bind them)
6. Add export_memory() and import_memory() methods to CalculatorCLI
7. Update CalculatorCLI menu to include export/import options
8. Add --export and --import argparse flags in `src/__main__.py`
9. Wire CLI dispatch in __main__.py for export/import operations
10. Create `tests/test_import_export_service.py` with full test suite

## Files to Read/Understand (Already Done)
- src/models/memory_entry.py ✓
- src/services/memory_service.py ✓
- src/storage/json_storage.py ✓
- src/cli/calculator_cli.py ✓
- src/__main__.py ✓
- tests/test_json_storage.py ✓
- tests/test_memory_service.py ✓

## Files to Create
- src/services/import_export_service.py (new)
- tests/test_import_export_service.py (new)

## Files to Modify
- src/services/__init__.py
- src/__main__.py
- src/cli/calculator_cli.py
- artifacts/component_diagram.puml (add ImportExportService component)
- artifacts/class_diagram.puml (add ImportExportService class)

