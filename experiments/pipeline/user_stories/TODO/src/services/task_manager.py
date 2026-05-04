from datetime import datetime, timezone, date
from typing import Optional
from calendar import monthrange

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage
from .exceptions import TaskNotFoundError


class TaskManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        # Handle both old (list) and new (dict) formats
        if isinstance(raw, dict):
            tasks_data = raw.get("tasks", [])
        else:
            tasks_data = raw
        self._tasks = {d["id"]: Task.from_dict(d) for d in tasks_data}

    def _persist(self) -> None:
        data = self._storage.load()
        # Preserve projects when saving tasks
        projects_data = data.get("projects", []) if isinstance(data, dict) else []
        self._storage.save({
            "tasks": [t.to_dict() for t in self._tasks.values()],
            "projects": projects_data
        })

    def add(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        task = Task(title=title, description=description, due_date=due_date)
        self._tasks[task.id] = task
        self._persist()
        return task

    def get(self, task_id: str) -> Task:
        if task_id in self._tasks:
            return self._tasks[task_id]
        # support short prefix lookup (e.g. first 8 chars shown by list)
        matches = [t for tid, t in self._tasks.items() if tid.startswith(task_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise TaskNotFoundError(f"Ambiguous prefix '{task_id}' matches {len(matches)} tasks")
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())

    def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    def list_by_project(self, project_id: str) -> list[Task]:
        """Filter tasks by project ID.

        Args:
            project_id: The project ID to filter by.

        Returns:
            list[Task]: All tasks assigned to the project.
        """
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def list_by_due_date_range(
        self,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        status: Optional[TaskStatus] = None,
        overdue_only: bool = False,
    ) -> list[Task]:
        """Filter tasks by due date range and optional status/overdue.

        Tasks with no due_date are excluded from all due date range filters.

        Args:
            before: Include only tasks with due_date <= before (or None to exclude from range check).
            after: Include only tasks with due_date >= after (or None to exclude from range check).
            status: If specified, include only tasks with this status.
            overdue_only: If True, include only tasks where is_overdue() returns True.

        Returns:
            list[Task]: Filtered task list.
        """
        result = []
        for task in self._tasks.values():
            # Skip tasks with no due_date unless checking for overdue status
            if task.due_date is None and not overdue_only:
                continue

            # Check due_date range
            if before is not None and task.due_date > before:
                continue
            if after is not None and task.due_date < after:
                continue

            # Check overdue status
            if overdue_only and not task.is_overdue():
                continue

            # Check status
            if status is not None and task.status != status:
                continue

            result.append(task)
        return result

    def get_week_boundaries(self, year: int, week: int) -> tuple[datetime, datetime]:
        """Calculate start and end datetime for an ISO 8601 week.

        Week 1 is the week with the first Thursday of the year (ISO 8601).
        Weeks start on Monday and end on Sunday.

        Args:
            year: Year (e.g., 2026).
            week: ISO week number (1-53).

        Returns:
            tuple[datetime, datetime]: (week_start, week_end) as UTC datetimes.

        Raises:
            ValueError: If week is not in 1-53.
        """
        if not 1 <= week <= 53:
            raise ValueError(f"Week must be 1-53, got {week}")
        # Get the Monday of the given ISO week
        week_start_date = date.fromisocalendar(year, week, 1)  # Monday
        week_start = datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        # Get the Sunday of the given ISO week (6 days after Monday)
        week_end_date = date.fromisocalendar(year, week, 7)  # Sunday
        week_end = datetime.combine(week_end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        return week_start, week_end

    def get_month_boundaries(self, year: int, month: int) -> tuple[datetime, datetime]:
        """Calculate start and end datetime for a calendar month.

        Args:
            year: Year (e.g., 2026).
            month: Month (1-12).

        Returns:
            tuple[datetime, datetime]: (month_start, month_end) as UTC datetimes.

        Raises:
            ValueError: If month is not in 1-12.
        """
        if not 1 <= month <= 12:
            raise ValueError(f"Month must be 1-12, got {month}")
        month_start = datetime(year, month, 1, tzinfo=timezone.utc)
        # Get last day of month
        last_day = monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        return month_start, month_end

    def get_year_boundaries(self, year: int) -> tuple[datetime, datetime]:
        """Calculate start and end datetime for a calendar year.

        Args:
            year: Year (e.g., 2026).

        Returns:
            tuple[datetime, datetime]: (year_start, year_end) as UTC datetimes.
        """
        year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
        year_end = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        return year_start, year_end

    def update(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
        task = self.get(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = due_date
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def set_status(self, task_id: str, status: TaskStatus) -> Task:
        task = self.get(task_id)
        if status == TaskStatus.IN_PROGRESS and task.status == TaskStatus.PENDING:
            task.mark_in_progress()
        elif status == TaskStatus.DONE and task.status == TaskStatus.IN_PROGRESS:
            task.mark_done()
        elif status == TaskStatus.IN_PROGRESS and task.status == TaskStatus.DONE:
            task.reopen()
        elif task.status == status:
            raise ValueError(f"Task is already {status.value}")
        else:
            raise ValueError(f"Cannot transition from {task.status.value} to {status.value}")
        self._persist()
        return task

    def set_due_date(self, task_id: str, due_date: Optional[datetime]) -> Task:
        task = self.get(task_id)
        task.due_date = due_date
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def delete(self, task_id: str) -> None:
        task = self.get(task_id)  # resolves prefix; raises if missing
        del self._tasks[task.id]
        self._persist()

    def set_task(self, task_id: str, task: Task) -> None:
        """Set a task directly in the tasks dictionary and persist.

        Args:
            task_id: The ID to store the task under.
            task: The Task object to store.
        """
        self._tasks[task_id] = task
        self._persist()

    def set_project(self, task_id: str, project_id: Optional[str]) -> Task:
        """Assign or unassign a task to/from a project.

        Args:
            task_id: The ID of the task to assign.
            project_id: The project ID, or None to unassign.

        Returns:
            Task: The updated task.

        Raises:
            TaskNotFoundError: If task is not found.
        """
        task = self.get(task_id)
        task.project_id = project_id
        task.updated_at = datetime.now(timezone.utc)
        self._persist()
        return task

    def orphan_project_tasks(self, project_id: str) -> int:
        """Unassign all tasks from a project (when project is deleted).

        Args:
            project_id: The project ID whose tasks should be orphaned.

        Returns:
            int: Number of tasks orphaned.
        """
        count = 0
        for task in self._tasks.values():
            if task.project_id == project_id:
                task.project_id = None
                count += 1
        if count > 0:
            self._persist()
        return count

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """Add a comment to a task.

        Args:
            task_id: The ID of the task to comment on.
            content: The comment content (non-empty string).
            author: Optional author name for the comment.

        Returns:
            TaskComment: The created comment.

        Raises:
            ValueError: If content is empty.
            TaskNotFoundError: If task is not found.
        """
        task = self.get(task_id)
        comment = TaskComment(content=content, task_id=task.id, author=author)
        task.comments.append(comment)
        self._persist()
        return comment

    def get_comments(self, task_id: str) -> list[TaskComment]:
        """Get all comments for a task, sorted by created_at ascending.

        Args:
            task_id: The ID of the task.

        Returns:
            list[TaskComment]: All comments for the task, sorted by created_at ascending.

        Raises:
            TaskNotFoundError: If task is not found.
        """
        task = self.get(task_id)
        return sorted(task.comments, key=lambda c: c.created_at)

    def delete_comment(self, task_id: str, comment_id: str) -> None:
        """Delete a comment from a task.

        Args:
            task_id: The ID of the task.
            comment_id: The ID of the comment to delete.

        Raises:
            TaskNotFoundError: If task is not found.
            ValueError: If comment is not found on the task.
        """
        task = self.get(task_id)
        comment = next((c for c in task.comments if c.id == comment_id), None)
        if comment is None:
            raise ValueError(f"Comment '{comment_id}' not found on task '{task.id}'")
        task.comments.remove(comment)
        self._persist()

    def edit_comment(self, task_id: str, comment_id: str, content: str) -> TaskComment:
        """Edit a comment on a task.

        Args:
            task_id: The ID of the task.
            comment_id: The ID of the comment to edit.
            content: The new comment content (non-empty string).

        Returns:
            TaskComment: The updated comment.

        Raises:
            TaskNotFoundError: If task is not found.
            ValueError: If comment is not found or content is empty.
        """
        task = self.get(task_id)
        comment = next((c for c in task.comments if c.id == comment_id), None)
        if comment is None:
            raise ValueError(f"Comment '{comment_id}' not found on task '{task.id}'")
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        comment.content = content.strip()
        comment.updated_at = datetime.now(timezone.utc)
        self._persist()
        return comment
