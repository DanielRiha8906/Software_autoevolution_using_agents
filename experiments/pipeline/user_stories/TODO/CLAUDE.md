TODO — Python CLI task manager.
src/models/: Task (dataclass), TaskStatus (enum)
src/services/: TaskManager (CRUD), TodoService (higher-level ops)
src/storage/: JsonStorage (JSON persistence)
src/cli/: TodoCLI (commands), InteractiveMenu
tests/: pytest

Edit only src/ and tests/. Tests: pytest tests/ -q
Diagrams: ./generate_diagrams.sh → artifacts/*.puml
