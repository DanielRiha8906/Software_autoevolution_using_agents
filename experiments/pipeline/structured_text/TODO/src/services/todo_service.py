from datetime import datetime
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..models.task_statistics import TaskStatistics
from ..models.project import Project
from ..storage.json_storage import JsonStorage
from .comment_manager import CommentManager
from .import_export_service import ExportService, ImportService
from .task_manager import TaskManager
from .project_manager import ProjectManager


class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._manager = TaskManager(storage)
        self._comment_manager = CommentManager(storage)
        self._project_manager = ProjectManager(storage)

    def add_task(self, title: str, description: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description)

    def get_task(self, task_id: str) -> Task:
        return self._manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        due_after: Optional[datetime] = None,
        due_before: Optional[datetime] = None,
        overdue: Optional[bool] = None,
    ) -> list[Task]:
        """List tasks with optional filtering.

        Args:
            status: Filter by task status (optional).
            due_after: Return tasks with due_date >= this datetime (optional).
            due_before: Return tasks with due_date <= this datetime (optional).
            overdue: If True, return only overdue tasks; if False, return only non-overdue tasks (optional).

        Returns:
            List of tasks matching all specified filters.

        Raises:
            ValueError: If due_after > due_before.
        """
        # Validate date range
        if due_after is not None and due_before is not None:
            if due_after > due_before:
                raise ValueError("due_after cannot be after due_before")

        # Delegate to manager's list_by_filter method
        return self._manager.list_by_filter(
            status=status,
            due_after=due_after,
            due_before=due_before,
            overdue=overdue,
        )

    def start_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.update(task_id, title=title, description=description)

    def delete_task(self, task_id: str) -> None:
        task = self._manager.get(task_id)  # resolves prefix; raises if missing
        self._comment_manager.delete_all_by_task(task.id)  # cascade delete comments
        self._manager.delete(task.id)

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: ID of the task (full or prefix)
            content: Comment text (required, non-empty)
            author: Optional author name

        Returns:
            The created TaskComment instance

        Raises:
            ValueError: If content is empty or whitespace-only
            TaskNotFoundError: If task does not exist
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        # Verify task exists
        task = self._manager.get(task_id)
        return self._comment_manager.add(task.id, content.strip(), author)

    def get_comments(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a task in chronological order.

        Args:
            task_id: ID of the task (full or prefix)

        Returns:
            List of TaskComment instances sorted by created_at (oldest first)

        Raises:
            TaskNotFoundError: If task does not exist
        """
        # Verify task exists
        task = self._manager.get(task_id)
        return self._comment_manager.list_by_task(task.id)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment.

        Args:
            comment_id: ID of the comment (full or prefix)

        Raises:
            CommentNotFoundError: If comment not found or prefix is ambiguous
        """
        self._comment_manager.delete(comment_id)

    def get_statistics(self) -> TaskStatistics:
        """Compute aggregate statistics over all tasks.

        Returns:
            TaskStatistics dataclass with aggregated metrics
        """
        tasks = self._manager.list_all()

        total_count = len(tasks)
        pending_count = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        in_progress_count = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        done_count = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        overdue_count = sum(1 for t in tasks if t.is_overdue())
        with_due_date_count = sum(1 for t in tasks if t.due_date is not None)

        return TaskStatistics(
            total_count=total_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            with_due_date_count=with_due_date_count,
        )

    def export_tasks_and_comments(self, filepath: str) -> tuple[int, int, int]:
        """Export all tasks, comments, and projects to a JSON file.

        Args:
            filepath: Path to write the JSON file to

        Returns:
            Tuple of (tasks_exported, comments_exported, projects_exported)

        Raises:
            ImportExportError: If export fails
        """
        service = ExportService(self._manager, self._comment_manager, self._project_manager)
        return service.export_to_file(filepath)

    def import_tasks_and_comments(self, filepath: str, mode: str = "fail") -> tuple[int, int, int, int]:
        """Import tasks, comments, and projects from a JSON file.

        Args:
            filepath: Path to the JSON file to import from
            mode: How to handle ID conflicts ('fail', 'skip', or 'replace')

        Returns:
            Tuple of (tasks_imported, comments_imported, projects_imported, conflicts_detected)

        Raises:
            ImportExportError: If import fails
        """
        service = ImportService(self._manager, self._comment_manager, self._project_manager)
        return service.import_from_file(filepath, mode)

    def create_project(self, name: str) -> Project:
        """Create a new project.

        Args:
            name: Project name (required, non-empty)

        Returns:
            The created Project instance

        Raises:
            ValueError: If name is empty or whitespace-only
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        return self._project_manager.add(name.strip())

    def list_projects(self) -> list[Project]:
        """List all projects.

        Returns:
            List of all Project instances
        """
        return self._project_manager.list_all()

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID or ID prefix.

        Args:
            project_id: Full project ID or unique prefix

        Returns:
            The Project instance

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        return self._project_manager.get(project_id)

    def delete_project(self, project_id: str) -> None:
        """Delete a project and unassign all its tasks.

        Args:
            project_id: Full project ID or unique prefix

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        project = self._project_manager.get(project_id)
        # Unassign all tasks in this project
        tasks_in_project = self._manager.list_by_project(project.id)
        for task in tasks_in_project:
            self._manager.unassign_from_project(task.id)
        # Delete the project
        self._project_manager.delete(project.id)

    def list_tasks_by_project(self, project_id: str) -> list[Task]:
        """List all tasks assigned to a project.

        Args:
            project_id: Full project ID or unique prefix

        Returns:
            List of Task instances assigned to that project

        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous
        """
        # Verify project exists
        self._project_manager.get(project_id)
        return self._manager.list_by_project(project_id)

    def assign_task_to_project(self, task_id: str, project_id: str) -> Task:
        """Assign a task to a project.

        Args:
            task_id: Full task ID or unique prefix
            project_id: Full project ID or unique prefix

        Returns:
            The updated Task instance

        Raises:
            TaskNotFoundError: If task not found
            ProjectNotFoundError: If project not found
        """
        # Verify project exists
        self._project_manager.get(project_id)
        return self._manager.assign_to_project(task_id, project_id)

    def unassign_task_from_project(self, task_id: str) -> Task:
        """Unassign a task from its project.

        Args:
            task_id: Full task ID or unique prefix

        Returns:
            The updated Task instance

        Raises:
            TaskNotFoundError: If task not found
        """
        return self._manager.unassign_from_project(task_id)

    def update_project(self, project_id: str, name: str) -> Project:
        """Update a project's name.

        Args:
            project_id: Full project ID or unique prefix
            name: New project name (required, non-empty)

        Returns:
            The updated Project instance

        Raises:
            ValueError: If name is empty or whitespace-only
            ProjectNotFoundError: If project not found
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        return self._project_manager.update(project_id, name.strip())
