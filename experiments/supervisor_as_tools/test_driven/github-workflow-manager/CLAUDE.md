GitHub Workflow Manager — Python CLI.
src/models/: WorkflowRun (dataclass), WorkflowStatus (enum), WorkflowConclusion (enum)
src/services/: WorkflowRunService (API ops), WorkflowRunTracker (local state)
src/storage/: WorkflowJsonStorage (JSON persistence)
src/cli/: WorkflowCLI (commands), InteractiveMenu
tests/: pytest

Edit only src/ and tests/. Tests: pytest tests/ -q
Diagrams: ./generate_diagrams.sh → artifacts/*.puml
