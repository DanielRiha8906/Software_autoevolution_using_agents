import json
from typing import TYPE_CHECKING

from ..models.task import Task
from ..models.task_comment import TaskComment
from .todo_service import TodoService
from .comments_service import CommentsService

if TYPE_CHECKING:
    pass


class TaskImportExportService:
    def __init__(self, todo_service: TodoService, comments_service: CommentsService) -> None:
        self._todo_service = todo_service
        self._comments_service = comments_service

    def export(self, filepath: str) -> None:
        """Export all tasks and their comments to a JSON file.

        Args:
            filepath: Path to write the JSON export file

        Writes JSON with structure: {"tasks": [...], "comments": [...]}
        Uses indent=2 and ensure_ascii=False for readability.
        """
        # Get all tasks
        tasks = self._todo_service.list_tasks()
        task_dicts = [task.to_dict() for task in tasks]

        # Get all comments for each task
        comments = []
        for task in tasks:
            task_comments = self._comments_service.list_comments(task.id)
            comments.extend([comment.to_dict() for comment in task_comments])

        # Write to file
        data = {
            "tasks": task_dicts,
            "comments": comments
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from(self, filepath: str) -> tuple[list[Task], list[TaskComment]]:
        """Import tasks and comments from a JSON file.

        Args:
            filepath: Path to the JSON export file

        Returns:
            Tuple of (imported_tasks, imported_comments)

        Raises:
            ValueError: If JSON structure is invalid or required fields are missing

        Validates structure and checks for duplicates. Filters out orphaned comments
        (those referencing non-existent tasks). Persists imported data to storage.
        Skips individual entries on from_dict() ValueError.
        """
        # Load JSON file
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("Import file must contain a JSON object")
        if "tasks" not in data:
            raise ValueError("Import file must contain 'tasks' key")
        if "comments" not in data:
            raise ValueError("Import file must contain 'comments' key")
        if not isinstance(data["tasks"], list):
            raise ValueError("'tasks' must be an array")
        if not isinstance(data["comments"], list):
            raise ValueError("'comments' must be an array")

        # Deserialize tasks with duplicate detection
        imported_tasks: list[Task] = []
        imported_task_ids: set[str] = set()
        existing_task_ids = set(task.id for task in self._todo_service._manager.get_all_tasks())

        for task_dict in data["tasks"]:
            try:
                task = Task.from_dict(task_dict)
                # Check for duplicate
                if task.id in existing_task_ids:
                    continue  # Skip duplicate
                imported_tasks.append(task)
                imported_task_ids.add(task.id)
            except ValueError:
                # Skip individual entries with from_dict() errors
                continue

        # Deserialize comments with duplicate detection
        imported_comments: list[TaskComment] = []
        existing_comment_ids = set(comment.id for comment in self._comments_service._comment_manager.get_all_comments())

        for comment_dict in data["comments"]:
            try:
                comment = TaskComment.from_dict(comment_dict)
                # Filter orphaned comments (task_id must exist in imported_task_ids or existing)
                if comment.task_id not in imported_task_ids and comment.task_id not in existing_task_ids:
                    continue  # Skip orphaned comment
                # Check for duplicate
                if comment.id in existing_comment_ids:
                    continue  # Skip duplicate
                imported_comments.append(comment)
            except ValueError:
                # Skip individual entries with from_dict() errors
                continue

        # Persist imported tasks to storage
        self._todo_service._manager.import_tasks(imported_tasks)

        # Persist imported comments to storage
        self._comments_service._comment_manager.import_comments(imported_comments)

        return (imported_tasks, imported_comments)
