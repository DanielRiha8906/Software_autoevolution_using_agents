# Analysis of Task 07: Export/Import Workflow Runs to JSON

## What the Task is Asking For

Task 07 requires implementing functionality to export workflow runs (and implicitly workflow run attempts) from the application to external JSON files and import them back, allowing developers to archive or transfer run data between environments. The feature must include:

- **Export capability**: Write all workflow runs to a JSON file
- **Import capability**: Read workflow runs from a JSON file and merge them into the system
- **Import validation**: Reject invalid data structures before applying
- **Non-destructive import**: Preserve existing data unless explicitly overwriting
- **Graceful failure**: Skip individual invalid or duplicate entries without failing entirely
- **JSON-only format**: No CSV, database, or other formats in scope
- **Architectural constraint**: GitHub adapter (if used) must be the only external API caller
- **CLI exposure**: All functionality must be accessible via `python -m src` in both interactive menu and one-shot flag modes

## Current State: Data Structures and Components

### Existing Data Models
1. **WorkflowRun** - Fields: id, workflow_name, branch, status, conclusion, created_at, updated_at, run_number, commit_sha, duration_seconds
   - Already has `to_dict()` and `from_dict()` methods for serialization
2. **WorkflowRunAttempt** - Fields: id, run_id, attempt_number, status, conclusion, created_at, duration_seconds
   - Already has `to_dict()` and `from_dict()` methods
3. **WorkflowStatus** - enum with 6 values
4. **WorkflowConclusion** - enum with 8 values

### Existing Persistence Layer
**WorkflowJsonStorage**:
- `save(runs: List[WorkflowRun])` → writes to filepath
- `load() → List[WorkflowRun]` — reads from filepath
- `save_attempts()` and `load_attempts()` — similar for attempts

### Existing Service Layer
1. **WorkflowRunService** - manages runs in-memory, persists via storage
2. **WorkflowRunAttemptService** - manages attempts in-memory, persists via storage
3. **WorkflowRunTracker** - facade for creating new runs
4. **StatisticsService** - aggregates metrics (not relevant)

### Existing CLI Layer
- **workflow_cli.py** - argparse-based subcommands: add, list, detail, check, attempt-*, stats
- **interactive_menu.py** - interactive menu with handler functions
- **__main__.py** - entry point, routes to CLI or interactive mode

## What Needs to be Implemented

### 1. New Service: WorkflowRunExportImportService
**Location**: `src/services/workflow_export_import_service.py`

**Export Methods**:
- `export_to_file(filepath: str, service: WorkflowRunService, attempt_service: Optional[WorkflowRunAttemptService] = None) → None`
  - Reads all runs from service._runs
  - Optionally includes attempts from attempt_service._attempts
  - Writes to specified filepath in JSON format

**Import Methods**:
- `import_from_file(filepath: str, service: WorkflowRunService, attempt_service: Optional[WorkflowRunAttemptService] = None, overwrite: bool = False) → ImportResult`
  - Reads JSON file
  - Validates each record structure (required fields, correct types)
  - Skips invalid/duplicate entries individually, doesn't fail entirely
  - Returns ImportResult with metadata

**Validation**:
- Check required fields (id, workflow_name, branch, status, created_at, duration_seconds)
- Validate status is valid WorkflowStatus enum value
- Validate conclusion (if present) is valid WorkflowConclusion enum value
- Validate datetime strings are ISO format
- Validate duration_seconds is non-negative float
- For attempts: validate id, run_id, attempt_number (>=1), status, created_at, duration_seconds

### 2. New Data Model: ImportResult
**Location**: `src/models/import_result.py`

```
@dataclass
class ImportResult:
    filepath: str
    total_records: int
    imported_runs: int
    skipped_runs: int
    imported_attempts: int
    skipped_attempts: int
    errors: List[str]  # List of error messages
    had_overwrite: bool
```

### 3. CLI Integration
**File**: `src/cli/workflow_cli.py`

New subcommands:
- `export` - Arguments: --filepath (required), --include-attempts (optional flag)
- `import` - Arguments: --filepath (required), --overwrite (optional flag), --dry-run (optional flag)

### 4. Interactive Menu Integration
**File**: `src/cli/interactive_menu.py`

New menu functions:
- `_export_runs(service, attempt_service)` - prompts for filepath and include-attempts
- `_import_runs(service, attempt_service)` - prompts for filepath and overwrite behavior

## Files That Will Need Changes

### New Files (must create):
- `src/services/workflow_export_import_service.py`
- `src/models/import_result.py`

### Modified Files:
- `src/cli/workflow_cli.py` — add export/import subparsers and handlers
- `src/cli/interactive_menu.py` — add menu functions and options
- `src/__main__.py` — import new service if needed
- `src/models/__init__.py` — export ImportResult
- `src/services/__init__.py` — optionally export new service

### Diagram Updates:
- `artifacts/class_diagram.puml` — add WorkflowRunExportImportService and ImportResult classes
- `artifacts/component_diagram.puml` — add export/import service component
- Other activity diagrams may need updating

## Key Design Decisions

1. **Non-atomic import**: Individual record failures don't stop the whole import
2. **Separate files for attempts**: Runs exported to one file, attempts to another (with --include-attempts)
3. **Overwrite semantics**: --overwrite flag allows replacing runs with same id
4. **No API calls**: Export/import service stays data-only, no external API integration
5. **File path handling**: User specifies any filepath (relative or absolute)
