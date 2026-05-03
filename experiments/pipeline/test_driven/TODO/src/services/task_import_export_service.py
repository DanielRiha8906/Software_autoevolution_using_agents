import json
from typing import List, Tuple
from pathlib import Path

from ..models.task import Task
from ..models.task_comment import TaskComment
from .todo_service import TodoService
from .comments_service import CommentsService
from .task_manager import TaskNotFoundError


class TaskImportExportService:
    """Service for bidirectional import/export of tasks and comments to/from JSON files."""

    def __init__(self, todo_service: TodoService, comments_service: CommentsService) -> None:
        """Initialize the import/export service.

        Args:
            todo_service: The TodoService instance managing tasks.
            comments_service: The CommentsService instance managing comments.
        """
        self._todo_service = todo_service
        self._comments_service = comments_service

    def export(self, filepath: str) -> None:
        """Export all tasks and comments to a JSON file.

        Creates or overwrites a JSON file with structure:
        {
            "tasks": [...task dicts...],
            "comments": [...comment dicts...]
        }

        Args:
            filepath: Path to write the export file to.
        """
        # Get all tasks and comments from services
        tasks = self._todo_service._manager.list_all()
        all_comments = self._comments_service._comments.values()

        # Convert to dict format
        export_data = {
            "tasks": [t.to_dict() for t in tasks],
            "comments": [c.to_dict() for c in all_comments],
        }

        # Write to file
        path = Path(filepath)
        with open(path, "w") as f:
            json.dump(export_data, f, indent=2)

    def import_from(self, filepath: str) -> Tuple[List[Task], List[TaskComment]]:
        """Import tasks and comments from a JSON file.

        Reads a JSON file and imports both tasks and comments. Validates the JSON structure
        and skips duplicates (by ID) without modifying existing data. Comments referencing
        non-existent tasks are silently skipped.

        Args:
            filepath: Path to the JSON file to import from.

        Returns:
            A tuple of (imported_tasks, imported_comments) excluding duplicates.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the JSON is malformed or missing required arrays.
        """
        path = Path(filepath)

        # Read and parse JSON
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        if "tasks" not in data:
            raise ValueError("JSON must contain 'tasks' array")
        if "comments" not in data:
            raise ValueError("JSON must contain 'comments' array")
        if not isinstance(data["tasks"], list):
            raise ValueError("'tasks' must be an array")
        if not isinstance(data["comments"], list):
            raise ValueError("'comments' must be an array")

        imported_tasks: List[Task] = []
        imported_comments: List[TaskComment] = []

        # Import tasks first
        for task_dict in data["tasks"]:
            try:
                task = Task.from_dict(task_dict)
                # Check if task already exists (skip if it does)
                try:
                    self._todo_service.get_task(task.id)
                    # Task exists, skip
                    continue
                except TaskNotFoundError:
                    # Task doesn't exist, add it
                    pass

                # Add task directly to the manager to bypass TodoService validations
                self._todo_service._manager._tasks[task.id] = task
                imported_tasks.append(task)
            except (KeyError, ValueError, TypeError) as e:
                # Skip malformed task entries
                continue

        # Persist tasks after import
        if imported_tasks:
            self._todo_service._manager._persist()

        # Import comments second
        for comment_dict in data["comments"]:
            try:
                comment = TaskComment.from_dict(comment_dict)
                # Check if comment already exists (skip if it does)
                if comment.id in self._comments_service._comments:
                    # Comment exists, skip
                    continue

                # Check if task exists
                try:
                    self._todo_service.get_task(comment.task_id)
                except TaskNotFoundError:
                    # Referenced task doesn't exist, skip comment silently
                    continue

                # Add comment directly to the comments service
                self._comments_service._comments[comment.id] = comment
                imported_comments.append(comment)
            except (KeyError, ValueError, TypeError) as e:
                # Skip malformed comment entries
                continue

        # Persist comments after import
        if imported_comments:
            self._comments_service._persist()

        return (imported_tasks, imported_comments)
