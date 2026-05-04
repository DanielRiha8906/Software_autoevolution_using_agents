# TODO Application - UML Diagrams (Task 09: Layered Architecture Refactor)

## Overview

This directory contains PlantUML diagrams documenting the refactored TODO application after implementing a clean layered architecture with the Repository pattern and dependency injection.

## Diagrams

### 1. **class_diagram.puml**
- **Purpose**: Shows all classes, their attributes, methods, and relationships
- **Key elements**:
  - Exception hierarchy (DomainError and subclasses)
  - Domain models (Task, TaskComment, Project, TaskStatus, TaskStatistics)
  - Storage layer (JsonStorage, StoragePathProvider)
  - **Repository layer** (new): BaseRepository<T> abstract class with three implementations
  - Services (TodoService, ExportService, ImportService)
  - Container for dependency injection
  - CLI components (TodoCLI, InteractiveMenu)
- **What changed**: Managers removed, repositories added, Container added

### 2. **component_diagram.puml**
- **Purpose**: Shows system architecture with components and their interactions
- **Key elements**:
  - Exception layer
  - Domain model components
  - Storage abstraction (PathProvider, JsonStorage)
  - Repository layer with inheritance
  - Service layer with import/export
  - Container wiring
  - CLI entry points
  - Database files
- **What changed**: Repositories replace managers, Container manages DI

### 3. **architecture_diagram.puml** (NEW)
- **Purpose**: High-level layered architecture visualization
- **Key elements**:
  - 7 distinct layers: CLI, DI, Services, Repositories, Storage, Domain, Exceptions/Utils
  - Shows dependencies flowing downward (CLI → DI → Services → Repositories → Storage)
  - No circular dependencies
  - Legend explaining clean layering principles
- **Why created**: Clarifies the new layered architecture and clean dependency flow

### 4. **repository_pattern_diagram.puml** (NEW)
- **Purpose**: Detailed explanation of the Repository pattern implementation
- **Key elements**:
  - BaseRepository<T> generic abstract class
  - TaskRepository, CommentRepository, ProjectRepository implementations
  - Generic serialization/deserialization interface
  - Domain models managed by each repository
  - Exception types raised by repositories
- **Why created**: Explains the core pattern change and its benefits

### 5. **dependency_diagram.puml** (NEW)
- **Purpose**: Dependency graph showing clean layering and no cycles
- **Key elements**:
  - 6 layers showing dependency directions (downward only)
  - Domain & Exceptions (Layer 1)
  - Storage abstraction (Layer 2)
  - Repositories (Layer 3)
  - Services (Layer 4)
  - Container (Layer 5)
  - CLI (Layer 6)
  - Legend explaining clean architecture principles
- **Why created**: Validates the acyclic dependency graph and inversion of control

### 6. **sequence_diagram.puml**
- **Purpose**: Shows interaction sequence for a typical operation (assign task to project)
- **Key elements**:
  - User → Menu → Container → Service → Repositories → Storage
  - Container injection of dependencies
  - Repository CRUD operations
- **What changed**: Replaced TaskManager/ProjectManager with TaskRepository/ProjectRepository, added Container

### 7. **refactoring_summary.puml** (NEW)
- **Purpose**: Before/after comparison of the refactoring
- **Key elements**:
  - OLD: TaskManager, CommentManager, ProjectManager (coupled to JsonStorage)
  - NEW: BaseRepository<T> pattern with three implementations
  - List of removed classes
  - List of added classes
  - Benefits of the refactor
- **Why created**: Documents the migration path and justification

### 8. **use_case_diagram.puml**
- **Purpose**: User-facing functionality (interactive and command-line modes)
- **Status**: Unchanged (user interactions remain the same)

### 9. **state_diagram.puml**
- **Purpose**: Task lifecycle states (PENDING → IN_PROGRESS → DONE)
- **Status**: Unchanged (domain model states unchanged)

### 10. **activity_diagram.puml**
- **Purpose**: User workflows for various operations
- **Status**: Unchanged (user workflows remain the same)

## Key Architectural Changes

### Removed
- `TaskManager` class
- `CommentManager` class
- `ProjectManager` class
- Direct manager instantiation in services

### Added
- **exceptions.py**: Centralized exception types with inheritance hierarchy
- **BaseRepository<T>**: Abstract generic repository pattern
- **TaskRepository, CommentRepository, ProjectRepository**: Concrete implementations
- **StoragePathProvider**: Abstraction for file paths
- **Container**: Dependency injection container

### Refactored
- **TodoService**: Now uses repositories instead of managers
- **ExportService**: Now uses repositories
- **ImportService**: Now uses repositories
- **TodoCLI**: Now uses Container to create service
- **InteractiveMenu**: Now uses Container to create service

## Design Patterns

### Repository Pattern
Each entity type has a `Repository<T>` that:
- Inherits from `BaseRepository<T>` (generic abstract base)
- Implements `_deserialize()` and `_serialize()` for type-specific conversion
- Handles CRUD operations
- Raises appropriate domain exceptions

### Dependency Injection
The `Container` class:
- Lazy-initializes repositories and services
- Provides single point of service creation
- Eliminates hard dependencies on concrete classes
- Enables easy testing and swapping

### Clean Architecture
- **No circular dependencies**: Layers only depend on layers below them
- **Inversion of control**: CLI doesn't create repositories, Container does
- **Single responsibility**: Each class has one reason to change
- **Interface segregation**: Repositories define clear CRUD contracts

## Files Updated During Task 09

1. `class_diagram.puml` - Updated to show new Repository layer
2. `component_diagram.puml` - Updated to show Container and Repository layer
3. `sequence_diagram.puml` - Updated to show Container usage
4. `architecture_diagram.puml` - **Created** - Layered architecture overview
5. `repository_pattern_diagram.puml` - **Created** - Repository pattern details
6. `dependency_diagram.puml` - **Created** - Dependency graph
7. `refactoring_summary.puml` - **Created** - Before/after comparison

Unchanged:
- `use_case_diagram.puml` - User workflows unchanged
- `state_diagram.puml` - Task lifecycle unchanged
- `activity_diagram.puml` - Activity flows unchanged
