from datetime import datetime, timezone
from typing import Optional

from ..models.task import Task
from ..models.task_status import TaskStatus
from ..models.task_comment import TaskComment
from ..storage.json_storage import JsonStorage


class TaskNotFoundError(Exception):
    pass


class TaskManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        raw = self._storage.load()
        self._tasks = {d["id"]: Task.from_dict(d) for d in raw}

    def _persist(self) -> None:
        self._storage.save([t.to_dict() for t in self._tasks.values()])

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
