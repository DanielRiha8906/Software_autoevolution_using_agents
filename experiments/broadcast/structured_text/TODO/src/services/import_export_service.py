import json
from pathlib import Path
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.task_status import TaskStatus
from ..storage.json_storage import JsonStorage


class ImportExportValidationError(Exception):
    """Raised when imported data fails validation."""
    pass


class ImportExportService:
    """Service for importing and exporting tasks and comments to/from JSON files."""

    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()

    def export_to_file(self, file_path: str) -> dict:
        """Export all stored tasks and comments to a JSON file.

        Args:
            file_path: Path where the JSON file will be saved

        Returns:
            A dict containing the exported data structure

        Raises:
            IOError: If file cannot be written
        """
        raw = self._storage.load()

        # Extract tasks and comments from storage
        if isinstance(raw, dict):
            tasks = raw.get("tasks", [])
            comments = raw.get("comments", [])
        else:
            tasks = raw if isinstance(raw, list) else []
            comments = []

        export_data = {
            "tasks": tasks,
            "comments": comments,
        }

        # Write to file
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return export_data

    def import_from_file(self, file_path: str, overwrite: bool = False) -> dict:
        """Import tasks and comments from a JSON file.

        Args:
            file_path: Path to the JSON file to import
            overwrite: If True, replace all existing data. If False, only add new entries.

        Returns:
            A dict with keys 'added_tasks', 'added_comments', 'skipped_tasks', 'skipped_comments'

        Raises:
            FileNotFoundError: If the file does not exist
            ImportExportValidationError: If the file format is invalid
            IOError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Import file not found: {file_path}")

        with path.open("r", encoding="utf-8") as f:
            import_data = json.load(f)

        # Validate the import structure
        self._validate_import_data(import_data)

        # Get current data
        raw = self._storage.load()
        if isinstance(raw, dict):
            current_tasks = {t["id"]: t for t in raw.get("tasks", [])}
            current_comments = {c["id"]: c for c in raw.get("comments", [])}
        else:
            current_tasks = {t["id"]: t for t in (raw if isinstance(raw, list) else [])}
            current_comments = {}

        # Parse imported data
        imported_tasks = import_data.get("tasks", [])
        imported_comments = import_data.get("comments", [])

        # If overwrite, clear current data
        if overwrite:
            current_tasks.clear()
            current_comments.clear()

        # Track what was added and skipped
        added_tasks = []
        skipped_tasks = []
        added_comments = []
        skipped_comments = []

        # Import tasks
        for task_dict in imported_tasks:
            task_id = task_dict.get("id")
            if task_id in current_tasks:
                skipped_tasks.append(task_id)
            else:
                try:
                    # Validate the task dict can be reconstructed
                    Task.from_dict(task_dict)
                    current_tasks[task_id] = task_dict
                    added_tasks.append(task_id)
                except (KeyError, ValueError) as e:
                    skipped_tasks.append(task_id)

        # Import comments
        for comment_dict in imported_comments:
            comment_id = comment_dict.get("id")
            if comment_id in current_comments:
                skipped_comments.append(comment_id)
            else:
                try:
                    # Validate the comment dict can be reconstructed
                    TaskComment.from_dict(comment_dict)
                    current_comments[comment_id] = comment_dict
                    added_comments.append(comment_id)
                except (KeyError, ValueError) as e:
                    skipped_comments.append(comment_id)

        # Persist updated data
        updated_data = {
            "tasks": list(current_tasks.values()),
            "comments": list(current_comments.values()),
        }
        self._storage.save(updated_data)

        return {
            "added_tasks": added_tasks,
            "added_comments": added_comments,
            "skipped_tasks": skipped_tasks,
            "skipped_comments": skipped_comments,
        }

    def validate_import_data(self, data: dict) -> tuple[bool, str]:
        """Validate the structure of imported data.

        Args:
            data: The import data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._validate_import_data(data)
            return True, ""
        except ImportExportValidationError as e:
            return False, str(e)

    def _validate_import_data(self, data: dict) -> None:
        """Validate the structure of imported data.

        Args:
            data: The import data to validate

        Raises:
            ImportExportValidationError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise ImportExportValidationError("Import data must be a JSON object (dict)")

        tasks = data.get("tasks")
        comments = data.get("comments")

        if tasks is not None and not isinstance(tasks, list):
            raise ImportExportValidationError("'tasks' field must be a list")

        if comments is not None and not isinstance(comments, list):
            raise ImportExportValidationError("'comments' field must be a list")

        # Validate individual task entries
        if tasks is not None:
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    raise ImportExportValidationError(f"Task {i} must be a dict")
                required_fields = {"id", "title", "status", "created_at", "updated_at"}
                missing = required_fields - set(task.keys())
                if missing:
                    raise ImportExportValidationError(
                        f"Task {i} missing required fields: {', '.join(missing)}"
                    )
                # Validate status is a valid TaskStatus value
                if task["status"] not in {"pending", "in_progress", "done"}:
                    raise ImportExportValidationError(
                        f"Task {i} has invalid status: {task['status']}"
                    )

        # Validate individual comment entries
        if comments is not None:
            for i, comment in enumerate(comments):
                if not isinstance(comment, dict):
                    raise ImportExportValidationError(f"Comment {i} must be a dict")
                required_fields = {"id", "task_id", "content", "created_at"}
                missing = required_fields - set(comment.keys())
                if missing:
                    raise ImportExportValidationError(
                        f"Comment {i} missing required fields: {', '.join(missing)}"
                    )
