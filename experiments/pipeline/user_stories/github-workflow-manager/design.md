# Task 07 Implementation Design: Export/Import Workflow Runs to JSON

**Date:** 2026-05-03  
**Architecture:** Pipeline (Sequential Agents)  
**Scope:** Export workflow runs and attempts to JSON; import with validation and conflict resolution

## 1. OVERVIEW

This design specifies the implementation of bidirectional JSON export/import for workflow runs and attempts. The feature must:

- Export all runs and optionally all attempts to a user-specified JSON file
- Import runs and attempts from a JSON file with field validation
- Handle conflicts via optional `--overwrite` flag
- Skip invalid records without failing the entire operation
- Provide detailed feedback via `ImportResult` dataclass
- Integrate with existing CLI (flags) and interactive menu

## 2. CLASS DESIGN

### 2.1 ImportResult Dataclass

**Location:** `src/models/import_result.py` (new file)

```python
@dataclass
class ImportResult:
    """Result metadata from an import operation."""
    filepath: str                      # Source file path (as provided by user)
    total_records: int                 # Total runs in file
    imported_runs: int                 # Number of runs successfully added/updated
    skipped_runs: int                  # Number of runs skipped (invalid or duplicate)
    imported_attempts: int             # Number of attempts successfully added/updated
    skipped_attempts: int              # Number of attempts skipped (invalid or duplicate)
    errors: List[str]                  # Detailed error messages for each skip
    had_overwrite: bool                # True if --overwrite was applied
```

### 2.2 WorkflowRunExportImportService Class

**Location:** `src/services/workflow_export_import_service.py` (new file)

#### Export Method Signature
```python
def export_to_file(
    self,
    filepath: str,
    service: WorkflowRunService,
    attempt_service: Optional[WorkflowRunAttemptService] = None,
    include_attempts: bool = False
) -> None:
    """
    Export workflow runs (and optionally attempts) to a JSON file.
    
    Runs are serialized via WorkflowRun.to_dict()
    If include_attempts=True, attempts written to <filepath>_attempts.json
    Parent directories are created if they don't exist
    """
```

#### Import Method Signature
```python
def import_from_file(
    self,
    filepath: str,
    service: WorkflowRunService,
    attempt_service: Optional[WorkflowRunAttemptService] = None,
    overwrite: bool = False,
    dry_run: bool = False
) -> ImportResult:
    """
    Import workflow runs (and optionally attempts) from a JSON file.
    
    Each record is validated individually
    Invalid records are skipped with error logged
    Duplicates skip unless overwrite=True
    If dry_run=True, validation only (no persistence)
    Returns ImportResult with metadata
    """
```

#### Validation Methods
```python
def _validate_and_build_run(self, data: dict, record_index: int) -> WorkflowRun:
    """Validate run dict with 9 validation rules"""
    
def _validate_and_build_attempt(self, data: dict, record_index: int) -> WorkflowRunAttempt:
    """Validate attempt dict with 7 validation rules"""
```

## 3. VALIDATION RULES TABLE

| Field | Required? | Type | Valid Values / Constraints |
|-------|-----------|------|---------------------------|
| **WorkflowRun.id** | Yes | str | Non-empty string |
| **WorkflowRun.workflow_name** | Yes | str | Non-empty string |
| **WorkflowRun.branch** | Yes | str | Non-empty string |
| **WorkflowRun.status** | Yes | str | One of: {queued, in_progress, completed, waiting, requested, pending} |
| **WorkflowRun.conclusion** | No | str \| null | One of: {success, failure, cancelled, skipped, timed_out, action_required, neutral, stale} OR null |
| **WorkflowRun.created_at** | Yes | str | ISO format datetime (e.g., 2025-05-03T10:30:00) |
| **WorkflowRun.updated_at** | No | str \| null | ISO format datetime OR null |
| **WorkflowRun.run_number** | No | int \| null | Any non-negative integer OR null |
| **WorkflowRun.commit_sha** | No | str \| null | Any string OR null |
| **WorkflowRun.duration_seconds** | No | float \| int | >= 0, default 0.0 |
| **WorkflowRunAttempt.id** | Yes | int | Any integer |
| **WorkflowRunAttempt.run_id** | Yes | int | Any integer |
| **WorkflowRunAttempt.attempt_number** | Yes | int | >= 1 |
| **WorkflowRunAttempt.status** | Yes | str | Non-empty string |
| **WorkflowRunAttempt.conclusion** | No | str \| null | Any string OR null |
| **WorkflowRunAttempt.created_at** | Yes | str | ISO format datetime |
| **WorkflowRunAttempt.duration_seconds** | No | float \| int | >= 0, default 0.0 |

## 4. CLI ARGUMENT SPECIFICATIONS

### Export Subcommand
```
Command: export
Arguments:
  --filepath (required): Output file path
  --include-attempts (flag): Also export attempts to <filepath>_attempts.json

Behavior:
  - Creates parent directories if needed
  - Overwrites existing file
  - Prints: "Exported N run(s) to <filepath>"
  - On error: prints to stderr, exits with code 1
```

### Import Subcommand
```
Command: import
Arguments:
  --filepath (required): Input file path
  --overwrite (flag): Allow replacing runs with same id
  --dry-run (flag): Validate without persisting

Behavior:
  - If file not found: FileNotFoundError, exit 1
  - If JSON malformed: ValueError, exit 1
  - Validates each record individually
  - On validation error: skip record, log error, continue
  - Prints ImportResult summary with counts and first N errors
  - If dry_run: appends "(dry run: no changes persisted)"
```

## 5. INTEGRATION POINTS

### Modified: `src/cli/workflow_cli.py`
- **Imports**: Add WorkflowRunExportImportService and ImportResult
- **build_parser()**: Add export and import subparsers after stats_p (around line 200)
- **run_cli()**: Add handlers for export and import (around line 403)
- **_print_import_result()**: New formatter function for ImportResult

### Modified: `src/cli/interactive_menu.py`
- **Imports**: Add WorkflowRunExportImportService
- **_export_runs()**: New handler (prompts for filepath, include-attempts)
- **_import_runs()**: New handler (prompts for filepath, overwrite, dry-run)
- **MENU list**: Add two new options for export/import
- **run_interactive()**: Update handler dispatch for new handlers

### Modified: `src/models/__init__.py`
- Export ImportResult

### Modified: `src/services/__init__.py`
- Optionally export WorkflowRunExportImportService

## 6. DATA FLOW

### Export Flow
```
User: python -m src export --filepath=output.json [--include-attempts]
                    ↓
run_cli() routes to export handler
                    ↓
WorkflowRunExportImportService.export_to_file()
                    ↓
1. Validate filepath is string
2. Create parent dirs: Path(filepath).parent.mkdir(parents=True, exist_ok=True)
3. Get all runs: runs = service.list_runs()
4. Serialize: data = [run.to_dict() for run in runs]
5. Write JSON: Path(filepath).write_text(json.dumps(data, indent=2))
6. If include_attempts:
   - Get all attempts: attempts = attempt_service.list_attempts()
   - Write to <filepath>_attempts.json
                    ↓
Print: "Exported N run(s) to <filepath>"
```

### Import Flow
```
User: python -m src import --filepath=input.json [--overwrite] [--dry-run]
                    ↓
run_cli() routes to import handler
                    ↓
WorkflowRunExportImportService.import_from_file()
                    ↓
1. Check file exists (raise FileNotFoundError if not)
2. Read and parse JSON (raise ValueError if malformed)
3. For each run in JSON:
   a. Validate: _validate_and_build_run()
   b. Check if exists: service.get_run_detail(id)
   c. If exists && !overwrite: skip, log "already exists"
   d. If valid && !dry_run: add to service (or replace if exists && overwrite)
   e. On validation error: skip, log error
4. For attempts file (if exists and attempt_service not None):
   - Same validation and conflict handling
5. Return ImportResult
                    ↓
Print ImportResult summary (counts, first N errors)
If dry_run: append "(dry run: no changes persisted)"
```

## 7. EDGE CASES & HANDLING

| Edge Case | Behavior |
|-----------|----------|
| File does not exist | FileNotFoundError; exit 1 |
| Malformed JSON | ValueError; exit 1 |
| Empty array `[]` | Import succeeds with 0 imported |
| Invalid status enum | Skip run; log error |
| Invalid datetime format | Skip run; log error |
| Negative duration_seconds | Skip run; log error |
| Duplicate id (no --overwrite) | Skip run; log error |
| Duplicate id (with --overwrite) | Replace existing run |
| Attempt without parent run | Skip attempt; log error |
| --dry-run with valid data | Validate but don't persist |

## 8. FILES TO CREATE/MODIFY

### New Files
- `src/models/import_result.py` — ImportResult dataclass
- `src/services/workflow_export_import_service.py` — Export/import service

### Modified Files
- `src/models/__init__.py` — Export ImportResult
- `src/services/__init__.py` — Export service (optional)
- `src/cli/workflow_cli.py` — Add export/import subcommands and handlers
- `src/cli/interactive_menu.py` — Add export/import menu options and handlers

## 9. ARCHITECTURAL DECISIONS

1. **Separate files for attempts**: `<runs_filepath>_attempts.json`
2. **Non-atomic import**: Per-record error handling; invalid records skip without failing entire import
3. **Overwrite as opt-in**: Default skips duplicates; `--overwrite` flag allows replacing
4. **Stateless service**: Instantiated per-call in handlers
5. **Pre-validation**: _validate_and_build_* methods before from_dict()
6. **No API calls**: Local archiving only; GitHub adapter not involved

## 10. TEST SPECIFICATIONS (for pytest-tester)

### Export Tests
- `test_export_runs_to_file_basic`: Export 2 runs to file
- `test_export_runs_and_attempts`: Export runs and attempts to separate files
- `test_export_empty_service`: Export with no runs

### Import Tests
- `test_import_valid_runs`: Import 2 valid runs into empty service
- `test_import_duplicate_no_overwrite`: Duplicate id, --overwrite not set; skip with error
- `test_import_duplicate_with_overwrite`: Duplicate id, --overwrite set; replace run
- `test_import_invalid_status`: Invalid status enum; skip with error
- `test_import_invalid_datetime`: Invalid created_at format; skip with error
- `test_import_invalid_duration`: Negative duration_seconds; skip with error
- `test_import_dry_run`: Dry-run mode; validation runs but no persistence
- `test_import_file_not_found`: FileNotFoundError on missing file
- `test_import_malformed_json`: ValueError on invalid JSON syntax
- `test_import_mixed_valid_invalid`: File has valid and invalid; import valid, skip invalid
- `test_import_missing_required_field`: Skip record with missing required field
- `test_import_wrong_field_type`: Skip record with wrong field type
- `test_export_import_roundtrip`: Export → clear → import; verify data matches

### CLI Tests
- `test_cli_export_command`: Invoke `export --filepath test.json`
- `test_cli_export_with_attempts`: Invoke `export --filepath test.json --include-attempts`
- `test_cli_import_command`: Invoke `import --filepath test.json`
- `test_cli_import_with_overwrite`: Invoke `import --filepath test.json --overwrite`
- `test_cli_import_dry_run`: Invoke `import --filepath test.json --dry-run`

### Interactive Menu Tests
- `test_interactive_export`: User selects export from menu
- `test_interactive_import`: User selects import from menu

