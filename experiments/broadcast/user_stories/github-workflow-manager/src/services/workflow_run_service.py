from typing import List, Optional, TYPE_CHECKING

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.protocols import StorageBackend

if TYPE_CHECKING:
    from .workflow_query import WorkflowQuery
    from .attempt_service import AttemptService


class WorkflowRunService:
    def __init__(self, storage: StorageBackend):
        self._storage = storage
        self._runs: List[WorkflowRun] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._runs)

    def add_workflow_run(self, run: WorkflowRun) -> WorkflowRun:
        if any(r.id == run.id for r in self._runs):
            raise ValueError(f"Run with id '{run.id}' already exists.")
        self._runs.append(run)
        self._persist()
        return run

    def list_runs(self) -> List[WorkflowRun]:
        return list(self._runs)

    def get_run_detail(self, run_id: str) -> Optional[WorkflowRun]:
        return next((r for r in self._runs if r.id == run_id), None)

    def filter_by_branch(self, branch: str) -> List[WorkflowRun]:
        return [r for r in self._runs if r.branch == branch]

    def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRun]:
        return [r for r in self._runs if r.status == status]

    def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRun]:
        return [r for r in self._runs if r.conclusion == conclusion]

    def create_query(self, attempt_service: Optional["AttemptService"] = None) -> "WorkflowQuery":
        """Create a query interface for advanced filtering.

        Args:
            attempt_service: Optional AttemptService for attempt presence filtering.

        Returns:
            A WorkflowQuery instance initialized with current runs.
        """
        from .workflow_query import WorkflowQuery
        return WorkflowQuery(list(self._runs), attempt_service)


__all__ = ["WorkflowRunService"]
