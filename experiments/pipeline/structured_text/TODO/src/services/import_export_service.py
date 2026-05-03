"""JSON import/export service for tasks and comments.

Provides ExportService and ImportService classes for serializing and deserializing
Task and TaskComment objects to/from JSON files.
"""

import json
from pathlib import Path
from typing import Optional

from ..models.task import Task
from ..models.task_comment import TaskComment
from ..models.project import Project
from .comment_manager import CommentManager
from .task_manager import TaskManager
from .project_manager import ProjectManager


class ImportExportError(Exception):
    """Raised when import/export validation fails."""
    pass


class ExportService:
    """Service for exporting tasks, comments, and projects to JSON files.

    Exports all tasks, comments, and projects to a JSON file with structure:
    {
        "tasks": [...],
        "comments": [...],
        "projects": [...]
    }
    """

    def __init__(self, task_manager: TaskManager, comment_manager: CommentManager, project_manager: ProjectManager) -> None:
        """Initialize ExportService with managers.

        Args:
            task_manager: TaskManager instance for reading tasks
            comment_manager: CommentManager instance for reading comments
            project_manager: ProjectManager instance for reading projects
        """
        self._task_manager = task_manager
        self._comment_manager = comment_manager
        self._project_manager = project_manager

    def export_to_file(self, filepath: str) -> tuple[int, int, int]:
        """Export all tasks, comments, and projects to a JSON file.

        Args:
            filepath: Path to write the JSON file to

        Returns:
            Tuple of (tasks_exported, comments_exported, projects_exported)

        Raises:
            ImportExportError: If file cannot be written
        """
        try:
            tasks = self._task_manager.list_all()
            comments = self._comment_manager.list_all()
            projects = self._project_manager.list_all()

            export_data = {
                "tasks": [t.to_dict() for t in tasks],
                "comments": [c.to_dict() for c in comments],
                "projects": [p.to_dict() for p in projects],
            }

            # Write to file
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return len(tasks), len(comments), len(projects)
        except Exception as e:
            raise ImportExportError(f"Failed to export to {filepath}: {e}")


class ImportService:
    """Service for importing tasks, comments, and projects from JSON files.

    Validates JSON structure and handles ID conflicts according to specified mode:
    - 'fail' (default): Raise error on any ID conflict
    - 'skip': Skip conflicting records, keep existing data
    - 'replace': Overwrite existing records with imported data
    """

    def __init__(self, task_manager: TaskManager, comment_manager: CommentManager, project_manager: ProjectManager) -> None:
        """Initialize ImportService with managers.

        Args:
            task_manager: TaskManager instance for writing tasks
            comment_manager: CommentManager instance for writing comments
            project_manager: ProjectManager instance for writing projects
        """
        self._task_manager = task_manager
        self._comment_manager = comment_manager
        self._project_manager = project_manager

    def import_from_file(self, filepath: str, mode: str = "fail") -> tuple[int, int, int, int]:
        """Import tasks, comments, and projects from a JSON file.

        Args:
            filepath: Path to the JSON file to import from
            mode: How to handle ID conflicts:
                - 'fail': Raise error on conflict (default)
                - 'skip': Skip conflicting records
                - 'replace': Overwrite existing records

        Returns:
            Tuple of (tasks_imported, comments_imported, projects_imported, conflicts_detected)

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

        # Parse and validate projects
        projects_to_import = []
        try:
            for project_dict in data.get("projects", []):
                project = Project.from_dict(project_dict)
                projects_to_import.append(project)
        except (KeyError, ValueError) as e:
            raise ImportExportError(f"Invalid project format in {filepath}: {e}")

        # Check for conflicts
        existing_task_ids = set(t.id for t in self._task_manager.list_all())
        existing_comment_ids = set(c.id for c in self._comment_manager.list_all())
        existing_project_ids = set(p.id for p in self._project_manager.list_all())

        conflicts = 0
        task_conflicts = [t.id for t in tasks_to_import if t.id in existing_task_ids]
        comment_conflicts = [c.id for c in comments_to_import if c.id in existing_comment_ids]
        project_conflicts = [p.id for p in projects_to_import if p.id in existing_project_ids]
        conflicts = len(task_conflicts) + len(comment_conflicts) + len(project_conflicts)

        if mode == "fail" and conflicts > 0:
            raise ImportExportError(
                f"Import conflicts detected: {len(task_conflicts)} task(s), "
                f"{len(comment_conflicts)} comment(s), and {len(project_conflicts)} project(s) already exist. "
                f"Use --mode skip or --mode replace."
            )

        # Apply imports based on mode
        tasks_imported = 0
        comments_imported = 0
        projects_imported = 0

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

            for project in projects_to_import:
                if project.id not in existing_project_ids:
                    self._project_manager._projects[project.id] = project
                    projects_imported += 1

        else:
            # For 'fail' mode (no conflicts) or 'replace' mode: import all
            for task in tasks_to_import:
                self._task_manager._tasks[task.id] = task
                tasks_imported += 1

            for comment in comments_to_import:
                self._comment_manager._comments[comment.id] = comment
                comments_imported += 1

            for project in projects_to_import:
                self._project_manager._projects[project.id] = project
                projects_imported += 1

        # Persist changes
        self._task_manager._persist()
        self._comment_manager._persist()
        self._project_manager._persist()

        return tasks_imported, comments_imported, projects_imported, conflicts

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

        # Projects key is optional (for backward compatibility)
        if "projects" in data and not isinstance(data["projects"], list):
            raise ImportExportError("'projects' must be a list if present")
