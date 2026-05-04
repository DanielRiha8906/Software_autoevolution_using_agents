# TODO Application Layered Architecture

## Overview

The TODO application follows a clear layered architecture pattern to separate concerns and maintain testability. Each layer has distinct responsibilities and dependencies only flow downward (no circular dependencies).

## Layers

### 1. CLI Layer (`src/cli/`)
- **Purpose**: Command-line interface and interactive menu
- **Files**: `todo_cli.py`, `interactive_menu.py`
- **Dependencies**: Services layer (TodoService)
- **Public API**: TodoCLI, InteractiveMenu

### 2. Services Layer (`src/services/` and `src/layers/services/`)
- **Purpose**: High-level business logic coordinators
- **Files**: 
  - `layers/services/todo_service.py` - Main unified service
  - `layers/services/task_service.py` - Task-specific operations
  - `layers/services/comment_service.py` - Comment-specific operations
  - `layers/services/project_service.py` - Project-specific operations
  - `layers/services/import_export_service.py` - Import/export operations
  - `layers/services/statistics_service.py` - Statistics calculations
- **Dependencies**: Repositories layer
- **Public API**: TodoService (main entry point)
- **Note**: `src/services/` re-exports from `src/layers/services/` for backward compatibility

### 3. Repositories Layer (`src/layers/repositories/`)
- **Purpose**: Data access abstraction and persistence operations
- **Files**:
  - `protocols.py` - Abstract interfaces (TaskRepository, CommentRepository, ProjectRepository)
  - `json_repositories.py` - Concrete JSON-based implementations
- **Dependencies**: Models layer, Storage layer
- **Public API**: Repository protocols and implementations
- **Key Concepts**:
  - Protocol-based design for interface-first abstraction
  - Concrete implementations for JSON persistence
  - Exception classes (TaskNotFoundError, CommentNotFoundError, ProjectNotFoundError)

### 4. Storage Layer (`src/storage/` and `src/layers/storage/`)
- **Purpose**: Persistence mechanism abstraction
- **Files**:
  - `layers/storage/protocols.py` - StorageProtocol interface
  - `layers/storage/json_storage.py` - JSON file implementation
- **Dependencies**: None (bottom layer for persistence)
- **Public API**: StorageProtocol, JsonStorage
- **Note**: `src/storage/` re-exports from `src/layers/storage/` for backward compatibility

### 5. Models Layer (`src/models/` and `src/layers/models/`)
- **Purpose**: Domain data structures and value objects
- **Files**:
  - `task.py` - Task domain model
  - `task_status.py` - Status enumeration
  - `task_comment.py` - Comment domain model
  - `project.py` - Project domain model
  - `task_statistics.py` - Statistics value object
- **Dependencies**: None (independent of all other layers)
- **Public API**: All model classes and enums
- **Note**: `src/models/` re-exports from `src/layers/models/` for backward compatibility

### 6. Domain Layer (`src/layers/domain/`)
- **Purpose**: Alternative domain logic approach with repositories and domain services
- **Files**:
  - `exceptions.py` - Domain exceptions
  - `task_repository.py` - Task repository implementation
  - `project_repository.py` - Project repository implementation
  - `comment_repository.py` - Comment repository implementation
  - `task_domain_service.py` - Task domain service
  - `project_domain_service.py` - Project domain service
  - `comment_domain_service.py` - Comment domain service
- **Dependencies**: Models layer, Storage protocol
- **Note**: Provides alternative abstraction approach; not currently used by CLI but available

## Dependency Flow (No Cycles)

```
CLI Layer
  └─→ Services Layer
      └─→ Repositories Layer
          └─→ Models Layer
          └─→ Storage Layer
              └─→ (no dependencies)

Models Layer
  └─→ (no dependencies)

Storage Layer
  └─→ (no dependencies)

Domain Layer (Alternative)
  └─→ Models Layer
  └─→ Storage Protocol
```

## Public API

The main entry point is `TodoService` from `src/services/todo_service.py`:

```python
from src import TodoService, JsonStorage

# Create service with default or custom storage
service = TodoService()
# or
service = TodoService(storage=JsonStorage(path="/custom/path"))

# Operations
task = service.add_task("My task", description="Details", due_date=None, project_id=None)
tasks = service.list_tasks(status=TaskStatus.PENDING, overdue=False)
service.start_task(task.id)
service.complete_task(task.id)
service.delete_task(task.id)

# Comments
comment = service.add_comment(task.id, "Comment text", author="User")
comments = service.list_comments(task.id)
service.delete_comment(comment.id)

# Projects
project = service.add_project("My Project")
projects = service.list_projects()
service.delete_project(project.id)
```

## Backward Compatibility

The refactoring maintains full backward compatibility:
- `src/models/` re-exports all models from `src/layers/models/`
- `src/storage/` re-exports JsonStorage from `src/layers/storage/`
- `src/services/` includes both the legacy managers and new service implementations
- All existing public interfaces remain unchanged

## Benefits

1. **Clear Separation of Concerns**: Each layer has a single responsibility
2. **Testability**: Layers can be tested independently with mock storage
3. **Maintainability**: Changes to one layer don't affect others (unidirectional dependencies)
4. **Extensibility**: New storage implementations can be added without changing services
5. **Interface-First Design**: Repositories use protocols for loose coupling
6. **No Circular Dependencies**: Dependency graph is acyclic
