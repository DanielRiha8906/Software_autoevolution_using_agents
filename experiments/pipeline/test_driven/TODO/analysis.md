# Task 07: TaskImportExportService Analysis

## Task Overview
Implement a `TaskImportExportService` that handles bidirectional import/export of tasks and comments in a single JSON file, with duplicate detection and validation, without overwriting existing data.

## Current Class Structure (from artifacts and source code)

### Models
- **Task** (`src/models/task.py`)
  - Fields: `id`, `title`, `description` (opt), `status`, `created_at`, `updated_at`, `due_date` (opt)
  - Methods: `to_dict()`, `from_dict()`, status change methods
  - Key behavior: IDs are UUIDs, datetimes are ISO format strings in dict form

- **TaskComment** (`src/models/task_comment.py`)
  - Fields: `id`, `task_id`, `content`, `created_at`, `author` (opt), `updated_at` (opt)
  - Methods: `to_dict()`, `from_dict()`
  - Validation: Content cannot be empty

- **TaskStatus** (`src/models/task_status.py`)
  - Enum with: PENDING, IN_PROGRESS, DONE

### Storage Layer
- **JsonStorage** (`src/storage/json_storage.py`)
  - Handles JSON persistence at filesystem level
  - Current structure: `{"tasks": [...], "comments": [...]}`
  - Methods: `load()`, `save()`, `load_comments()`, `save_comments()`
  - Preserves existing data when saving (merge pattern)

### Service Layer
- **TaskManager** (`src/services/task_manager.py`)
  - Manages Task CRUD operations in-memory with persistence
  - Stores tasks in dict keyed by ID
  - Methods: `add()`, `get()`, `list_all()`, `list_by_status()`, `update()`, `set_status()`, `delete()`
  - Error handling: `TaskNotFoundError`

- **TodoService** (`src/services/todo_service.py`)
  - Higher-level wrapper over TaskManager
  - Methods: `add_task()`, `get_task()`, `list_tasks()`, `start_task()`, `complete_task()`, `reopen_task()`, `update_task()`, `delete_task()`
  - Timezone validation (requires CEST for filtering)

- **CommentsService** (`src/services/comments_service.py`)
  - Manages TaskComment CRUD operations in-memory with persistence
  - Stores comments in dict keyed by ID
  - Methods: `add_comment()`, `list_comments()`, `delete_comment()`, `delete_comments_for_task()`
  - Validates that task exists before adding comment
  - Sorts comments by created_at

- **TaskStatisticsService** (`src/services/task_statistics_service.py`)
  - Computes statistics on tasks via TodoService

### CLI Layer
- **TodoCLI** (`src/cli/todo_cli.py`)
  - Commands: add, list, show, start, done, reopen, update, delete, statistics
  - Entry point via `argparse` subcommands
  
- **InteractiveMenu** (`src/cli/interactive_menu.py`)
  - Menu-driven CLI for interactive mode
  - Default entry point when no args provided

- **__main__.py** (`src/__main__.py`)
  - Routes to CLI or interactive menu based on argv

## Existing to_dict/from_dict Patterns

### Task.to_dict() Pattern
```
{
  "id": "uuid-string",
  "title": "title",
  "description": null or "text",
  "status": "pending" | "in_progress" | "done",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "due_date": null or "ISO8601"  (optional key)
}
```

### TaskComment.to_dict() Pattern
```
{
  "id": "uuid-string",
  "task_id": "uuid-string",
  "content": "text",
  "created_at": "ISO8601",
  "author": null or "string",
  "updated_at": null or "ISO8601"  (optional key)
}
```

## TodoService and CommentsService Interfaces

### TodoService
- Constructor: `TodoService(storage: Optional[JsonStorage] = None)`
- Does NOT directly manage comments
- Accesses TaskManager via `self._manager`
- All task operations go through manager

### CommentsService
- Constructor: `CommentsService(todo_service: TodoService, storage: Optional[JsonStorage] = None)`
- Maintains independent in-memory dict: `self._comments`
- Persists separately via `self._storage.save_comments()`
- Validates task existence via todo_service
- No cascade delete built-in (manual call needed)

## What Needs to be Implemented

### New File: `src/services/task_import_export_service.py`

**Class: TaskImportExportService**

#### Methods Required:

1. **`export(filepath: str) -> None`**
   - Exports all tasks AND comments from TodoService and CommentsService
   - Creates/writes to single JSON file at filepath
   - Structure: `{"tasks": [...], "comments": [...]}`
   - Both tasks and comments use their existing `to_dict()` format
   - Overwrites file completely (not merge)

2. **`import_from(filepath: str) -> tuple[List[Task], List[TaskComment]]`**
   - Reads JSON file and imports both tasks and comments
   - Validates JSON structure against schema (must have "tasks" and "comments" arrays)
   - **Duplicate handling:**
     - For tasks: Skip if task with same ID already exists in TodoService
     - For comments: Skip if comment with same ID already exists in CommentsService
   - **No overwrite:** Existing tasks/comments in the service are never modified
   - Returns tuple of (imported_tasks, imported_comments) - excluding duplicates
   - Raises ValueError on malformed JSON or missing arrays

3. **Constructor: `__init__(todo_service: TodoService, comments_service: CommentsService)`**
   - Takes references to both services
   - No storage parameter (services already manage storage)

#### Error Handling:
- `ValueError`: Invalid JSON format, missing "tasks"/"comments" arrays, schema mismatch
- `FileNotFoundError`: If import filepath doesn't exist (let it propagate)
- Task with comment that references non-existent task: Skip the comment or raise?
  - **ASSUMPTION**: Skip the comment (import doesn't fail, but comment is skipped)

#### Design Decisions:
- No modification of existing data in services (skip duplicates)
- Validation at import time: structure only, not semantic validation
- Export is full snapshot (tasks + comments in one file)
- Import is additive only (no delete, no update)
- Service instances must be passed in (no storage coupling)

## Gaps and Design Questions

1. **Task-Comment Referential Integrity on Import**
   - What if import file contains comments for non-existent tasks?
   - ASSUMPTION: Skip such comments silently (don't fail the import)
   - Could be configurable in future (strict vs lenient mode)

2. **Export Scope**
   - Export everything vs selective export?
   - ASSUMPTION: Always export all tasks and all comments (full snapshot)
   - Could add filters in future (status-based, date-range, etc.)

3. **Duplicate Detection Strategy**
   - Use ID as sole key?
   - ASSUMPTION: Yes, ID is unique within each entity type
   - No content-based duplicate detection (hash of title/description)

4. **File Format Versioning**
   - Should the export include a version marker?
   - ASSUMPTION: No version field (keep it simple for Task 07)
   - If needed: Could add `{"version": "1.0", "tasks": [...], "comments": [...]}`

5. **CLI Integration**
   - Should there be `python -m src export <file>` and `import <file>` commands?
   - ASSUMPTION: Yes, per Experiment Governance requirements
   - Will be implemented by python-programmer after this analysis

6. **Interactive Menu Integration**
   - Should InteractiveMenu have export/import options?
   - ASSUMPTION: Yes, as menu items for full feature completeness
   - Programmer can add as needed

## Scope Signals

**In:**
- Single JSON file with tasks + comments together
- Duplicate detection (ID-based)
- Schema validation on import
- Export/import methods on the service
- CLI integration (export/import commands and flags)
- Interactive menu options

**Out (Not for Task 07):**
- Encrypted/compressed export
- Selective export (filtering by status, date, etc.)
- Incremental sync (only changed items)
- CSV/XML/other formats
- Conflict resolution on duplicate detection
- Batch import/export of multiple files

**Borderline:**
- Referential integrity validation (skip vs fail) - Decision: Skip silently
- File versioning - Decision: Not needed for Task 07
- Relative vs absolute paths - Use absolute paths (standard Python)

## Implementation Dependencies

### Required Imports in new service:
- `from typing import Optional, List, Tuple`
- `from pathlib import Path`
- `import json`
- `from ..models.task import Task`
- `from ..models.task_comment import TaskComment`
- `from .todo_service import TodoService`
- `from .comments_service import CommentsService`

### Service Integration Pattern:
Services are instantiated in TodoCLI and InteractiveMenu. The import/export service will need to:
- Be instantiated in both CLI and interactive contexts
- Receive todo_service and comments_service instances
- Example: `import_export_svc = TaskImportExportService(todo_service, comments_service)`

## Suggested Priorities

1. **High**: Implement core export/import logic in TaskImportExportService
   - Both methods must handle to_dict/from_dict correctly
   - Duplicate detection must work accurately

2. **High**: Validate JSON structure on import (schema validation)
   - Catch malformed files early
   - Provide clear error messages

3. **Medium**: Add CLI commands (export/import flags to TodoCLI)
   - Standard: `python -m src export <filepath>`
   - Standard: `python -m src import <filepath>`

4. **Medium**: Add interactive menu options
   - Menu item for "Export to file"
   - Menu item for "Import from file"
   - Prompt for filepath

5. **Low**: Polish error messages and feedback
   - Report how many items were imported
   - Warn about skipped duplicates

## File Paths Reference

**Key source files:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/src/models/task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/src/models/task_comment.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/src/services/todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/src/services/comments_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/src/cli/todo_cli.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/src/cli/interactive_menu.py`

**Diagram references:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/artifacts/class_diagram.puml`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/artifacts/component_diagram.puml`

**Test examples:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/tests/test_comments_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/TODO/tests/test_task.py`
