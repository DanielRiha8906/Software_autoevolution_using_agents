# Task 07 Analysis: Export/Import Calculation History

## Current State

### Existing Infrastructure
The calculator application already has a well-architected system for persisting calculation history:

- **MemoryEntry** (`src/models/memory_entry.py`): Dataclass representing a single calculation with:
  - `operation`: str (operation name: add, subtract, etc.)
  - `operand_a`, `operand_b`: float (input values)
  - `result`: float | None (calculation result or None on error)
  - `error`: str | None (error message if failed)
  - `error_type`: str | None (exception class name)
  - `execution_time_ms`: float (timing data)
  - `timestamp`: str (ISO 8601 format, auto-generated)
  - `uuid`: str (unique identifier, auto-generated)
  - **Serialization**: `to_dict()` and `from_dict(data)` methods already exist and fully functional

- **JsonStorage** (`src/storage/json_storage.py`): Handles low-level JSON persistence
  - `save(entry)`: Appends a single MemoryEntry to `artifacts/calculations.json`
  - `load_all()`: Reads entire history file and deserializes to MemoryEntry objects
  - Raw methods: `_read_raw()` and `_write_raw(records)` for list-level I/O
  - Error handling: Gracefully returns empty list on missing file or JSON decode errors

- **MemoryService** (`src/services/memory_service.py`): Provides filtering and retrieval
  - `store()`: Delegates to JsonStorage.save()
  - `retrieve()`: Delegates to JsonStorage.load_all()
  - `filter()`: Can filter by operation names and/or state (success/error/both)

- **CalculatorService** (`src/services/calculator_service.py`): Orchestrates calculations
  - `get_history()`: Returns all history via MemoryService
  - `filter_history()`: Returns filtered history

- **CalculatorCLI** (`src/cli/calculator_cli.py`): Interactive and one-shot modes
  - Menu options: View history, filter history, statistics, exit
  - Already wired to display and filter data
  - No export/import functionality currently

- **__main__.py** (`src/__main__.py`): Entry point with argparse support
  - Existing flags: `--operation`, `--show-history`, `--filter-operation`, `--filter-state`, `--statistics`
  - Well-structured service initialization

### Current Storage Format
`artifacts/calculations.json` is a JSON array of objects. Each object matches MemoryEntry.to_dict() format:
```json
{
  "operation": "add",
  "operand_a": 3.0,
  "operand_b": 5.0,
  "result": 8.0,
  "error": null,
  "error_type": null,
  "execution_time_ms": 0.01,
  "timestamp": "2026-05-03T13:11:43.011212",
  "uuid": "c4ebe8ef-ada9-435b-8cca-b60c868586c6"
}
```

Fields: `error` and `error_type` may be absent in older entries (backward compatible via `from_dict()` defaults).

---

## Task Requirements

### Functional Requirements
1. **Export**: Write calculation history to a user-specified JSON file
2. **Import**: Read calculation history from a user-specified JSON file and merge it into current history
3. **Validation**: Before applying imported data, validate structure and reject invalid entries
4. **No Overwrite by Default**: Importing appends; does not replace existing data unless explicitly intended
5. **Per-Entry Error Handling**: Invalid or duplicate entries are skipped individually, not treated as full failure
6. **JSON Only**: No other formats supported
7. **CLI Accessibility**: Both interactive menu option and one-shot CLI flags

### Acceptance Criteria Mapping

| Criterion | Current State | Required Implementation |
|-----------|---------------|--------------------------|
| History can be exported to a JSON file | No | Add export method & CLI |
| History can be imported from a JSON file | No | Add import method & CLI |
| Imported data is validated; invalid structure rejected | No | Add validation logic |
| Importing does not overwrite unless explicitly intended | N/A | Default merge; add `--force` flag if overwrite needed |
| JSON schema matches MemoryEntry serialization format | Partially | Ensure imported data uses exact format |
| Invalid/duplicate entries skipped individually, not full failure | No | Add per-entry error handling |
| Only JSON format supported | N/A | Only support .json; validate extension |
| Accessible via `python -m src` (menu + CLI flag) | N/A | Add menu option & flags to argparse |

---

## What Needs to Change

### New Components to Add

#### 1. New Service Class: `ImportExportService` (`src/services/import_export_service.py`)
**Responsibilities:**
- Export history to a JSON file at a user-specified path
- Import history from a JSON file with validation
- Validate JSON structure before import (schema validation)
- Handle duplicate detection (by UUID or timestamp+operation)
- Report per-entry errors (invalid entries skipped, count reported)
- Support merge (append) vs. force (replace) modes

**Key Methods:**
```python
class ImportExportService:
    def __init__(self, memory_service: MemoryService)
    
    def export_history(
        self, 
        filepath: Path | str, 
        entries: list[MemoryEntry] | None = None
    ) -> dict[str, int]:
        """Export entries to filepath.
        
        Args:
            filepath: Destination JSON file path
            entries: Entries to export (None = export all)
            
        Returns:
            {"exported_count": int, "file_path": str}
        """
    
    def import_history(
        self,
        filepath: Path | str,
        mode: str = "merge"  # "merge" or "replace"
    ) -> dict[str, int | list]:
        """Import entries from filepath with validation.
        
        Args:
            filepath: Source JSON file path
            mode: "merge" (append) or "replace" (overwrite)
            
        Returns:
            {
                "imported_count": int,
                "skipped_count": int,
                "skipped_entries": list[dict] (invalid/duplicate entries),
                "duplicates_count": int,
                "invalid_count": int
            }
        """
    
    def _validate_entry(self, data: dict) -> tuple[bool, str | None]:
        """Validate a single entry dict against MemoryEntry schema.
        
        Returns:
            (is_valid, error_message_or_none)
        """
    
    def _detect_duplicate(self, entry: MemoryEntry, existing: list[MemoryEntry]) -> bool:
        """Check if entry already exists by UUID or (operation, operand_a, operand_b, timestamp)."""
```

#### 2. CLI Enhancements to `CalculatorCLI` (`src/cli/calculator_cli.py`)
**New Methods:**
```python
def _export_history(self) -> None:
    """Interactive menu option: prompt for export filepath, call service."""

def _import_history(self, filepath: str | None = None, mode: str = "merge") -> None:
    """Interactive menu option: prompt for import filepath, call service, show results."""

def _show_import_result(self, result: dict) -> None:
    """Display import operation results (counts, skipped entries, etc.)."""
```

**Menu Changes:**
- Add "Export history" option (new menu item)
- Add "Import history" option (new menu item)
- Update `_print_menu()` to include these options
- Update `run_interactive()` to handle these new choices

#### 3. Entry Point Changes to `__main__.py` (`src/__main__.py`)
**New Argparse Arguments:**
```python
parser.add_argument(
    "--export",
    metavar="FILEPATH",
    help="Export calculation history to a JSON file"
)

parser.add_argument(
    "--import",
    metavar="FILEPATH",
    help="Import calculation history from a JSON file (appends by default)"
)

parser.add_argument(
    "--import-mode",
    choices=["merge", "replace"],
    default="merge",
    help="When importing: 'merge' (append to existing) or 'replace' (overwrite all)"
)
```

**Handler Logic:**
```python
# In main(), after building services:
if args.export:
    # Call ImportExportService.export_history()
    # Print status and exit

if args.import:
    # Call ImportExportService.import_history(mode=args.import_mode)
    # Print results and exit
```

---

## Implementation Scope

### Files to Create
- `src/services/import_export_service.py` (new service class)

### Files to Modify
- `src/__main__.py`: Add export/import argparse flags and handlers
- `src/cli/calculator_cli.py`: Add interactive menu options and helper methods
- `src/services/__init__.py`: Export ImportExportService if it uses __init__.py

### Files Unchanged
- `src/models/memory_entry.py`: Already has to_dict() and from_dict()
- `src/storage/json_storage.py`: No changes needed (used internally by service)
- `src/services/memory_service.py`: No changes needed (used by ImportExportService)
- `src/services/calculator_service.py`: No changes needed

### Testing Required
- Unit tests for ImportExportService:
  - Export with valid entries
  - Import with valid entries (merge and replace modes)
  - Import with invalid entries (per-entry skip, report)
  - Duplicate detection and skipping
  - File I/O error handling (missing file, permission denied, etc.)
  - Schema validation (missing required fields, wrong types)
- Integration tests:
  - CLI flags: `--export`, `--import`, `--import-mode`
  - Interactive menu: export and import options
- Edge cases:
  - Empty history export
  - Empty import file
  - Malformed JSON
  - Entries with missing optional fields (error, error_type)
  - UUID collision detection
  - Timestamp collision detection

### Validation Rules
1. **Required Fields** per entry: operation, operand_a, operand_b, result, error, error_type, execution_time_ms, timestamp, uuid
2. **Type Validation**: 
   - operation: str, must be valid operation name (add, subtract, multiply, divide, square, sqrt, power, modulo)
   - operand_a, operand_b: must be float-convertible
   - result: float | None
   - error, error_type: str | None
   - execution_time_ms: float >= 0
   - timestamp: str, ISO 8601 format
   - uuid: str, UUID format (or auto-generate if missing)
3. **Duplicate Detection**: By UUID (if present), then by (operation, operand_a, operand_b, timestamp)
4. **Graceful Skip**: Entries that fail validation are reported but don't block import

### Error Handling Strategy
- Missing fields (except optional ones): reject entry, report in skipped list
- Invalid operation name: reject entry
- Non-numeric operands: reject entry
- Invalid timestamp format: reject entry (or auto-generate?)
- UUID collision: skip entry, increment duplicate counter
- File not found: raise error (don't silently fail)
- Permission denied: raise error
- Malformed JSON: raise error (entire file rejected, not per-entry)

---

## Ambiguities & Assumptions

1. **Duplicate Detection**:
   - *Unclear*: Should we detect duplicates by UUID exact match, or by (operation, operands, timestamp)?
   - *Assumption*: Prefer UUID if present; fall back to (operation, operand_a, operand_b, timestamp) tuple. Both trigger skip.

2. **Merge vs. Replace Mode**:
   - *Unclear*: Should `--import-mode replace` delete all existing history first?
   - *Assumption*: "merge" = append to existing (default); "replace" = clear all, then add imported entries. This matches acceptance criterion "not overwrite unless explicitly intended."

3. **Optional Fields on Import**:
   - *Unclear*: Should missing `error`, `error_type`, `execution_time_ms` be auto-filled or cause rejection?
   - *Assumption*: Auto-fill with defaults (None, None, 0.0) to maintain backward compatibility with older JSON exports. MemoryEntry.from_dict() already does this.

4. **File Extension Validation**:
   - *Unclear*: Should we reject non-.json files?
   - *Assumption*: Yes, validate that filepath ends with `.json`, reject otherwise with clear error.

5. **Interactive vs. One-Shot**:
   - *Unclear*: Should `--export` and `--import` work without interactive prompts?
   - *Assumption*: Yes, they are pure CLI flags. Interactive options are separate menu items that prompt for filepath.

6. **Import File Format**:
   - *Unclear*: Must the imported file be exactly the same structure as MemoryEntry.to_dict()?
   - *Assumption*: Yes, the JSON schema must match MemoryEntry serialization format exactly. MemoryEntry.from_dict() handles field defaults.

---

## Suggested Implementation Order

1. **ImportExportService** (core logic)
   - Implement validation
   - Implement duplicate detection
   - Implement export
   - Implement import with merge and replace modes
   - Unit tests

2. **__main__.py** (CLI flags)
   - Add argparse arguments
   - Add handlers that call ImportExportService
   - Test with `python -m src --export FILE`, `python -m src --import FILE`

3. **CalculatorCLI** (interactive menu)
   - Add export/import menu options
   - Implement interactive prompts
   - Wire to ImportExportService
   - Test interactive menu flow

4. **Full Integration Tests**
   - Test all combinations (export, import, merge, replace, filter, statistics)
   - Test error cases (missing files, malformed JSON, invalid entries)

---

## Summary

**What needs to exist after Task 07:**
- New `ImportExportService` that exports/imports history with validation and per-entry error handling
- Menu options in interactive mode for export/import
- CLI flags `--export FILEPATH`, `--import FILEPATH`, `--import-mode {merge,replace}`
- Full validation of imported entries; duplicates and invalid entries skipped (not full failure)
- Clear error/success reporting to the user
- All functionality wired through `python -m src` entry point
