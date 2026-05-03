import json
from pathlib import Path
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from .comments_service import CommentsService
from .todo_service import TodoService


class TaskImportExportService:
    """Service for importing and exporting tasks and comments to/from JSON files."""

    def __init__(self, todo_service: TodoService, comments_service: CommentsService) -> None:
        """Initialize the import/export service.

        Args:
            todo_service: The TodoService instance to manage tasks.
            comments_service: The CommentsService instance to manage comments.
        """
        self._todo_service = todo_service
        self._comments_service = comments_service

    def export(self, path: str) -> None:
        """Export all tasks and comments to a JSON file.

        The JSON structure includes:
        - "tasks": list of task dictionaries
        - "comments": list of comment dictionaries

        Args:
            path: The file path to export to.

        Raises:
            IOError: If the file cannot be written.
        """
        # Get all tasks and comments
        tasks = self._todo_service.list_tasks()
        all_comments = self._comments_service.get_all_comments()

        # Build the export structure
        export_data = {
            "tasks": [t.to_dict() for t in tasks],
            "comments": [c.to_dict() for c in all_comments],
        }

        # Write to file
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def import_from(self, path: str) -> None:
        """Import tasks and comments from a JSON file.

        The JSON structure must include:
        - "tasks": list of task dictionaries
        - "comments": list of comment dictionaries

        Only imports tasks and comments that don't already exist (by ID).
        Existing data is never overwritten.

        Args:
            path: The file path to import from.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the JSON structure is invalid or missing required keys.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Import file not found: {path}")

        # Load and parse the JSON
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("JSON root must be a dictionary")
        if "tasks" not in data:
            raise ValueError("JSON must contain 'tasks' key")
        if "comments" not in data:
            raise ValueError("JSON must contain 'comments' key")

        # Validate tasks structure
        if not isinstance(data["tasks"], list):
            raise ValueError("'tasks' must be a list")
        for task_data in data["tasks"]:
            if not isinstance(task_data, dict):
                raise ValueError("Each task must be a dictionary")
            if "id" not in task_data:
                raise ValueError("Each task must have an 'id' field")

        # Validate comments structure
        if not isinstance(data["comments"], list):
            raise ValueError("'comments' must be a list")
        for comment_data in data["comments"]:
            if not isinstance(comment_data, dict):
                raise ValueError("Each comment must be a dictionary")
            if "id" not in comment_data:
                raise ValueError("Each comment must have an 'id' field")
            if "task_id" not in comment_data:
                raise ValueError("Each comment must have a 'task_id' field")

        # Import tasks (skip duplicates)
        existing_task_ids = {t.id for t in self._todo_service.list_tasks()}
        for task_data in data["tasks"]:
            task_id = task_data["id"]
            if task_id not in existing_task_ids:
                task = Task.from_dict(task_data)
                # Add task directly to the manager
                self._todo_service._manager._tasks[task.id] = task
                existing_task_ids.add(task.id)

        # Persist tasks after all have been added
        self._todo_service._manager._persist()

        # Import comments (skip duplicates)
        existing_comments = self._comments_service.get_all_comments()
        existing_comment_ids = {c.id for c in existing_comments}

        comments_added = False
        for comment_data in data["comments"]:
            comment_id = comment_data["id"]
            if comment_id not in existing_comment_ids:
                comment = TaskComment.from_dict(comment_data)
                task_id = comment.task_id
                if task_id not in self._comments_service._comments:
                    self._comments_service._comments[task_id] = []
                self._comments_service._comments[task_id].append(comment)
                existing_comment_ids.add(comment_id)
                comments_added = True

        # Persist comments if any were added
        if comments_added and hasattr(self._comments_service, '_persist'):
            self._comments_service._persist()
