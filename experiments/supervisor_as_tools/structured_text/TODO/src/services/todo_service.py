import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.project import Project
from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_statistics import TaskStatistics
from ..models.task_status import TaskStatus
from ..repositories.task_repository import TaskRepository
from ..storage.storage import Storage
from ..storage.json_storage import JsonStorage
from .comments_service import CommentsService
from .project_manager import ProjectManager
from .task_manager import TaskManager


class TodoService:
    def __init__(self, storage: Optional[Storage] = None) -> None:
        storage = storage or JsonStorage()
        self._task_manager = TaskManager(storage)
        self._repository = TaskRepository(self._task_manager)
        self._comments_service = CommentsService(storage, self._repository)
        self._repository.set_comments_service(self._comments_service)
        self._project_manager = ProjectManager(storage)
        # Keep backward compatibility reference
        self._manager = self._task_manager

    def add_task(self, title: str, description: Optional[str] = None, project_id: Optional[str] = None) -> Task:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._manager.add(title.strip(), description, project_id)

    def get_task(self, task_id: str) -> Task:
        return self._task_manager.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        overdue: bool = False,
        project_id: Optional[str] = None,
    ) -> list[Task]:
        """List tasks with optional filtering.

        Args:
            status: Optional status filter.
            due_before: Optional upper bound for due_date (inclusive).
            due_after: Optional lower bound for due_date (inclusive).
            overdue: If True, return only overdue tasks, ignoring due_before/due_after.
            project_id: Optional project filter.

        Returns:
            Filtered list of tasks.
        """
        if project_id is not None:
            return self._task_manager.list_by_project(project_id)
        elif overdue:
            return self._task_manager.list_overdue(status)
        elif due_before is not None or due_after is not None:
            return self._task_manager.list_by_due_date_range(due_after, due_before, status)
        elif status is not None:
            return self._task_manager.list_by_status(status)
        else:
            return self._task_manager.list_all()

    def start_task(self, task_id: str) -> Task:
        return self._task_manager.set_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> Task:
        return self._task_manager.set_status(task_id, TaskStatus.DONE)

    def reopen_task(self, task_id: str) -> Task:
        return self._task_manager.set_status(task_id, TaskStatus.PENDING)

    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        if title is not None and not title.strip():
            raise ValueError("Task title cannot be empty")
        return self._task_manager.update(task_id, title=title, description=description)

    def delete_task(self, task_id: str) -> None:
        self._repository.delete_task_with_comments(task_id)

    def set_due_date(self, task_id: str, due_date: Optional[datetime] = None) -> Task:
        return self._task_manager.set_due_date(task_id, due_date)

    def add_comment(self, task_id: str, content: str) -> TaskComment:
        return self._comments_service.add_comment(task_id, content)

    def list_comments(self, task_id: str) -> list[TaskComment]:
        return self._comments_service.list_comments(task_id)

    def delete_comment(self, comment_id: str) -> None:
        self._comments_service.delete_comment(comment_id)

    def get_statistics(self) -> TaskStatistics:
        """Calculate and return statistics about all tasks.

        Returns:
            TaskStatistics with task counts, completion rate, and average days to completion.
        """
        all_tasks = self._task_manager.list_all()
        total_count = len(all_tasks)

        # Count tasks by status
        pending_count = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
        in_progress_count = len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS])
        done_count = len([t for t in all_tasks if t.status == TaskStatus.DONE])

        # Count overdue tasks
        overdue_count = len([t for t in all_tasks if t.is_overdue()])

        # Count tasks with due date
        tasks_with_due_date = len([t for t in all_tasks if t.due_date is not None])

        # Compute completion rate
        completion_rate = (done_count / total_count * 100) if total_count > 0 else 0
        completion_rate = round(completion_rate, 1)

        # Compute average days to completion for done tasks
        done_tasks = [t for t in all_tasks if t.status == TaskStatus.DONE]
        if done_tasks:
            total_days = sum((t.updated_at - t.created_at).days for t in done_tasks)
            avg_days_to_completion = round(total_days / len(done_tasks), 1)
        else:
            avg_days_to_completion = None

        return TaskStatistics(
            total_count=total_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            done_count=done_count,
            overdue_count=overdue_count,
            tasks_with_due_date=tasks_with_due_date,
            completion_rate=completion_rate,
            avg_days_to_completion=avg_days_to_completion,
        )

    def export_tasks(self, filepath: str) -> tuple[int, int]:
        """Export all tasks and comments to a JSON file.

        Args:
            filepath: Path to write the JSON export file.

        Returns:
            Tuple of (task_count, comment_count).
        """
        all_tasks = self._task_manager.list_all()
        all_comments = []
        for task in all_tasks:
            all_comments.extend(self._comments_service.list_comments(task.id))

        export_data = {
            "tasks": [t.to_dict() for t in all_tasks],
            "comments": [c.to_dict() for c in all_comments],
        }

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return (len(all_tasks), len(all_comments))

    def import_tasks(self, filepath: str, overwrite: bool = False) -> tuple[int, int, list]:
        """Import tasks and comments from a JSON file.

        Args:
            filepath: Path to the JSON import file.
            overwrite: If False, raise error if database not empty. If True, clear before loading.

        Returns:
            Tuple of (task_count, comment_count, []).

        Raises:
            ValueError: If file doesn't exist, JSON is invalid, required keys missing,
                       or validation fails.
        """
        path = Path(filepath)
        if not path.exists():
            raise ValueError(f"Import file not found: {filepath}")

        try:
            with path.open("r", encoding="utf-8") as f:
                import_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON syntax in {filepath}: {e}")

        # Check for required keys
        if not isinstance(import_data, dict):
            raise ValueError("Import file must contain a JSON object")
        if "tasks" not in import_data:
            raise ValueError('Required key "tasks" not found in import file')
        if "comments" not in import_data:
            raise ValueError('Required key "comments" not found in import file')

        tasks_data = import_data["tasks"]
        comments_data = import_data["comments"]

        if not isinstance(tasks_data, list):
            raise ValueError("tasks must be a list")
        if not isinstance(comments_data, list):
            raise ValueError("comments must be a list")

        # Validate all tasks first
        for i, task_dict in enumerate(tasks_data):
            self._validate_task_dict(task_dict, i)

        # Build a set of valid task IDs for comment validation
        valid_task_ids = {t["id"] for t in tasks_data}

        # Validate all comments
        for i, comment_dict in enumerate(comments_data):
            self._validate_comment_dict(comment_dict, i, valid_task_ids)

        # Check if database is not empty (before loading anything)
        if not overwrite and (self._task_manager.has_tasks() or self._comments_service.has_comments()):
            raise ValueError("Database is not empty. Use overwrite=True to replace existing data")

        # Clear existing data if overwrite is True
        if overwrite:
            self._task_manager.clear()
            self._comments_service.clear()

        # Load tasks and comments
        self._task_manager.load_from_dicts(tasks_data)
        self._comments_service.load_from_dicts(comments_data)

        return (len(tasks_data), len(comments_data), [])

    def _validate_task_dict(self, task_dict: dict, index: int) -> None:
        """Validate a task dictionary from import file.

        Args:
            task_dict: Task dictionary to validate.
            index: Index in the tasks list (for error messages).

        Raises:
            ValueError: If validation fails.
        """
        required_fields = ["id", "title", "description", "status", "created_at", "updated_at", "due_date"]
        for field in required_fields:
            if field not in task_dict:
                raise ValueError(f"Task at index {index}: required field '{field}' not found")

        # Validate status
        status_value = task_dict["status"]
        if status_value not in {"pending", "in_progress", "done"}:
            raise ValueError(
                f"Task at index {index}: invalid status '{status_value}'. "
                f"Must be one of: pending, in_progress, done"
            )

        # Validate datetime fields are ISO 8601 parseable
        for datetime_field in ["created_at", "updated_at"]:
            try:
                datetime.fromisoformat(task_dict[datetime_field])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Task at index {index}: field '{datetime_field}' is not valid ISO 8601 datetime"
                )

        # Validate due_date if present
        due_date_str = task_dict["due_date"]
        if due_date_str is not None:
            try:
                datetime.fromisoformat(due_date_str)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Task at index {index}: field 'due_date' is not valid ISO 8601 datetime"
                )

    def _validate_comment_dict(self, comment_dict: dict, index: int, valid_task_ids: set) -> None:
        """Validate a comment dictionary from import file.

        Args:
            comment_dict: Comment dictionary to validate.
            index: Index in the comments list (for error messages).
            valid_task_ids: Set of valid task IDs in the import.

        Raises:
            ValueError: If validation fails.
        """
        required_fields = ["id", "task_id", "content", "created_at"]
        for field in required_fields:
            if field not in comment_dict:
                raise ValueError(f"Comment at index {index}: required field '{field}' not found")

        # Validate content is not empty
        content = comment_dict["content"]
        if not content or not content.strip():
            raise ValueError(f"Comment at index {index}: content cannot be empty or whitespace-only")

        # Validate task_id references valid task
        task_id = comment_dict["task_id"]
        if task_id not in valid_task_ids:
            raise ValueError(
                f"Comment at index {index}: task_id '{task_id}' does not reference a valid task"
            )

        # Validate created_at is ISO 8601 parseable
        try:
            datetime.fromisoformat(comment_dict["created_at"])
        except (ValueError, TypeError):
            raise ValueError(
                f"Comment at index {index}: field 'created_at' is not valid ISO 8601 datetime"
            )

    def add_project(self, name: str) -> Project:
        """Add a new project.

        Args:
            name: Project name.

        Returns:
            Created Project.
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        return self._project_manager.add(name.strip())

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID.

        Args:
            project_id: The project ID.

        Returns:
            Project object.
        """
        return self._project_manager.get(project_id)

    def list_projects(self) -> list[Project]:
        """List all projects.

        Returns:
            List of all projects.
        """
        return self._project_manager.list_all()

    def delete_project(self, project_id: str) -> None:
        """Delete a project and unassign all its tasks.

        Args:
            project_id: The project ID to delete.
        """
        # Unassign all tasks from this project
        self._task_manager.unassign_from_project(project_id)
        # Delete the project
        self._project_manager.delete(project_id)
