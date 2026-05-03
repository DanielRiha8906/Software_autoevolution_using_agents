"""JSON import/export service for tasks and comments.

Provides ExportService and ImportService classes for serializing and deserializing
Task and TaskComment objects to/from JSON files.
"""

import json
from pathlib import Path
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from .comment_manager import CommentManager
from .task_manager import TaskManager


class ImportExportError(Exception):
    """Raised when import/export validation fails."""
    pass


class ExportService:
    """Service for exporting tasks and comments to JSON files.

    Exports all tasks and comments to a JSON file with structure:
    {
        "tasks": [...],
        "comments": [...]
    }
    """

    def __init__(self, task_manager: TaskManager, comment_manager: CommentManager) -> None:
        """Initialize ExportService with managers.

        Args:
            task_manager: TaskManager instance for reading tasks
            comment_manager: CommentManager instance for reading comments
        """
        self._task_manager = task_manager
        self._comment_manager = comment_manager

    def export_to_file(self, filepath: str) -> tuple[int, int]:
        """Export all tasks and comments to a JSON file.

        Args:
            filepath: Path to write the JSON file to

        Returns:
            Tuple of (tasks_exported, comments_exported)

        Raises:
            ImportExportError: If file cannot be written
        """
        try:
            tasks = self._task_manager.list_all()
            comments = self._comment_manager.list_all()

            export_data = {
                "tasks": [t.to_dict() for t in tasks],
                "comments": [c.to_dict() for c in comments],
            }

            # Write to file
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return len(tasks), len(comments)
        except Exception as e:
            raise ImportExportError(f"Failed to export to {filepath}: {e}")


class ImportService:
    """Service for importing tasks and comments from JSON files.

    Validates JSON structure and handles ID conflicts according to specified mode:
    - 'fail' (default): Raise error on any ID conflict
    - 'skip': Skip conflicting records, keep existing data
    - 'replace': Overwrite existing records with imported data
    """

    def __init__(self, task_manager: TaskManager, comment_manager: CommentManager) -> None:
        """Initialize ImportService with managers.

        Args:
            task_manager: TaskManager instance for writing tasks
            comment_manager: CommentManager instance for writing comments
        """
        self._task_manager = task_manager
        self._comment_manager = comment_manager

    def import_from_file(self, filepath: str, mode: str = "fail") -> tuple[int, int, int]:
        """Import tasks and comments from a JSON file.

        Args:
            filepath: Path to the JSON file to import from
            mode: How to handle ID conflicts:
                - 'fail': Raise error on conflict (default)
                - 'skip': Skip conflicting records
                - 'replace': Overwrite existing records

        Returns:
            Tuple of (tasks_imported, comments_imported, conflicts_detected)

        Raises:
            ImportExportError: If file cannot be read, JSON is invalid,
                             or validation fails, or mode='fail' and conflicts exist
        """
        if mode not in ("fail", "skip", "replace"):
            raise ImportExportError(f"Invalid mode '{mode}'. Must be 'fail', 'skip', or 'replace'.")

        try:
            path = Path(filepath)
            if not path.exists():
                raise ImportExportError(f"File not found: {filepath}")

            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ImportExportError(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            raise ImportExportError(f"Failed to read {filepath}: {e}")

        # Validate structure
        self._validate_schema(data)

        # Parse and validate tasks
        tasks_to_import = []
        try:
            for task_dict in data.get("tasks", []):
                task = Task.from_dict(task_dict)
                tasks_to_import.append(task)
        except (KeyError, ValueError) as e:
            raise ImportExportError(f"Invalid task format in {filepath}: {e}")

        # Parse and validate comments
        comments_to_import = []
        try:
            for comment_dict in data.get("comments", []):
                comment = TaskComment.from_dict(comment_dict)
                comments_to_import.append(comment)
        except (KeyError, ValueError) as e:
            raise ImportExportError(f"Invalid comment format in {filepath}: {e}")

        # Check for conflicts
        existing_task_ids = set(t.id for t in self._task_manager.list_all())
        existing_comment_ids = set(c.id for c in self._comment_manager.list_all())

        conflicts = 0
        task_conflicts = [t.id for t in tasks_to_import if t.id in existing_task_ids]
        comment_conflicts = [c.id for c in comments_to_import if c.id in existing_comment_ids]
        conflicts = len(task_conflicts) + len(comment_conflicts)

        if mode == "fail" and conflicts > 0:
            raise ImportExportError(
                f"Import conflicts detected: {len(task_conflicts)} task(s) and "
                f"{len(comment_conflicts)} comment(s) already exist. Use --mode skip or --mode replace."
            )

        # Apply imports based on mode
        tasks_imported = 0
        comments_imported = 0

        if mode == "skip":
            # Only import records that don't conflict
            for task in tasks_to_import:
                if task.id not in existing_task_ids:
                    self._task_manager._tasks[task.id] = task
                    tasks_imported += 1

            for comment in comments_to_import:
                if comment.id not in existing_comment_ids:
                    self._comment_manager._comments[comment.id] = comment
                    comments_imported += 1

        else:
            # For 'fail' mode (no conflicts) or 'replace' mode: import all
            for task in tasks_to_import:
                self._task_manager._tasks[task.id] = task
                tasks_imported += 1

            for comment in comments_to_import:
                self._comment_manager._comments[comment.id] = comment
                comments_imported += 1

        # Persist changes
        self._task_manager._persist()
        self._comment_manager._persist()

        return tasks_imported, comments_imported, conflicts

    def _validate_schema(self, data: dict) -> None:
        """Validate JSON schema for import.

        Args:
            data: Parsed JSON data

        Raises:
            ImportExportError: If schema is invalid
        """
        if not isinstance(data, dict):
            raise ImportExportError("Root element must be a JSON object")

        if "tasks" not in data or "comments" not in data:
            raise ImportExportError("JSON must contain 'tasks' and 'comments' keys")

        if not isinstance(data["tasks"], list):
            raise ImportExportError("'tasks' must be a list")

        if not isinstance(data["comments"], list):
            raise ImportExportError("'comments' must be a list")
