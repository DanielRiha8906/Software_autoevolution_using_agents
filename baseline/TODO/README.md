# TODO Manager

OOP task manager with persistent JSON storage, an interactive menu, and a one-shot CLI mode.

## Overview

This application represents a baseline task management system used in the experimental part of the bachelor thesis focused on software auto-evolution. In comparison with the calculator baseline, this system works with a richer state model and more complex entity lifecycle, which makes it useful for evaluating whether autonomous agents can correctly evolve software beyond purely arithmetic functionality.

The application allows users to create, inspect, modify, and delete tasks, while also managing state transitions between pending, in-progress, and completed states. Its architecture is separated into domain, service, storage, and CLI layers, enabling controlled observation of how experimental interventions affect different parts of the system.

Within the repository, this project serves as one of the reference baseline applications from which evolved variants in `experiments/` are derived.

## Requirements

- Python 3.12+
- `pytest` (tests only)

## Running

**Interactive menu**
```bash
cd baka/third/baseline/TODO
python -m src
```

The menu lets you list, add, show, change status, update, and delete tasks without typing commands.

**One-shot CLI commands**
```bash
# Add a task
python -m src add "Buy groceries"
python -m src add "Write tests" -d "Cover edge cases in task_manager"

# List all tasks (or filter by status)
python -m src list
python -m src list --status pending
python -m src list --status in_progress
python -m src list --status done

# Show full details of a task (accepts UUID prefix)
python -m src show <id>

# Change task status
python -m src start  <id>   # pending → in_progress
python -m src done   <id>   # → done
python -m src reopen <id>   # → pending

# Edit title or description
python -m src update <id> -t "New title" -d "New description"

# Remove a task
python -m src delete <id>
```

Task IDs are UUIDs. In all commands you can use a unique prefix (e.g. the first 8 characters shown by `list`).

## Task statuses

| Symbol | Status      |
|--------|-------------|
| `[ ]`  | pending     |
| `[~]`  | in_progress |
| `[x]`  | done        |

## Persistence

Tasks are stored in `~/.todo_data.json` by default. A custom path can be provided when constructing `JsonStorage` or `TodoCLI` programmatically.

## Tests

```bash
pytest tests/
pytest tests/ -v        # verbose
pytest tests/ -k task   # filter by name
```

**41 tests** across 5 files:

| File                    | Tests | Covers                                    |
|-------------------------|-------|-------------------------------------------|
| `test_task.py`          | 4     | `Task` dataclass, serialisation           |
| `test_json_storage.py`  | 4     | `JsonStorage` read/write                  |
| `test_task_manager.py`  | 11    | `TaskManager` CRUD and status transitions |
| `test_todo_service.py`  | 11    | `TodoService` validation and delegation   |
| `test_todo_cli.py`      | 11    | `TodoCLI` argument parsing and output     |

## Diagrams

```bash
./generate_diagrams.sh          # PNG (default)
./generate_diagrams.sh svg
./generate_diagrams.sh pdf
```

Output is written to `artifacts/`.

## Structure

```
src/
├── __main__.py          entry point, dispatches to interactive menu or CLI
├── models/
│   ├── task.py          Task dataclass with UUID, timestamps, and serialisation
│   └── task_status.py   TaskStatus enum  (PENDING / IN_PROGRESS / DONE)
├── services/
│   ├── task_manager.py  core CRUD and status-transition logic
│   └── todo_service.py  validation layer on top of TaskManager
├── storage/
│   └── json_storage.py  reads and writes ~/.todo_data.json
└── cli/
    ├── todo_cli.py       argument parser and one-shot command handlers
    └── interactive_menu.py  full-screen terminal menu

tests/                   pytest test suite (41 tests)
```
