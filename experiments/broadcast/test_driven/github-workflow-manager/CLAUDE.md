GitHub Workflow Manager — Python CLI.
src/models/: WorkflowRun (dataclass), WorkflowStatus (enum), WorkflowConclusion (enum)
src/services/: WorkflowRunService (API ops), WorkflowRunTracker (local state)
src/storage/: WorkflowJsonStorage (JSON persistence)
src/cli/: WorkflowCLI (commands), InteractiveMenu
tests/: pytest

Edit only src/ and tests/. Tests: write to tests/ and run pytest tests/ -q — never python -c
Diagrams: ./generate_diagrams.sh → artifacts/*.puml
