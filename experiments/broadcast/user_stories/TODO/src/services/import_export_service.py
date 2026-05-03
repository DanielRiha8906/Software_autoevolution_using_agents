import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from ..models.task import Task
from ..models.task_comment import TaskComment
from .task_manager import TaskManager
from .comments_service import CommentsService


@dataclass
class ImportSummary:
    """Summary of an import operation."""
    tasks_imported: int
    tasks_skipped: int
    comments_imported: int
    comments_skipped: int
    skipped_task_ids: list[str]
    skipped_comment_ids: list[str]

    def __str__(self) -> str:
        lines = [
            f"Tasks imported: {self.tasks_imported}",
            f"Tasks skipped: {self.tasks_skipped}",
            f"Comments imported: {self.comments_imported}",
            f"Comments skipped: {self.comments_skipped}",
        ]
        if self.skipped_task_ids:
            lines.append(f"Skipped task IDs: {', '.join(self.skipped_task_ids[:5])}")
        if self.skipped_comment_ids:
            lines.append(f"Skipped comment IDs: {', '.join(self.skipped_comment_ids[:5])}")
        return "\n".join(lines)


class ImportExportService:
    """Service for exporting and importing tasks and comments to/from JSON files."""

    def __init__(self, task_manager: TaskManager, comments_service: CommentsService) -> None:
        self._task_manager = task_manager
        self._comments_service = comments_service

    def export_to_file(self, filepath: str) -> int:
        """Export all tasks and comments to a JSON file.

        Args:
            filepath: Path to write JSON file to

        Returns:
            Total number of items exported (tasks + comments)
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Collect all tasks and comments
        tasks = self._task_manager.list_all()
        tasks_data = [t.to_dict() for t in tasks]

        all_comments = []
        for task in tasks:
            comments = self._comments_service.list_comments_for_task(task.id)
            all_comments.extend([c.to_dict() for c in comments])

        # Write to file
        data = {
            "tasks": tasks_data,
            "comments": all_comments,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return len(tasks_data) + len(all_comments)

    def import_from_file(self, filepath: str, merge: bool = True) -> ImportSummary:
        """Import tasks and comments from a JSON file.

        Args:
            filepath: Path to JSON file to import from
            merge: If True, merge with existing data (skip duplicates).
                   If False, skip all existing IDs.

        Returns:
            ImportSummary with counts and skipped items

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Import file not found: {filepath}")

        with path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON file: {e}")

        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")

        tasks_data = data.get("tasks", [])
        comments_data = data.get("comments", [])

        if not isinstance(tasks_data, list):
            raise ValueError("'tasks' field must be a list")
        if not isinstance(comments_data, list):
            raise ValueError("'comments' field must be a list")

        # Track what we're importing
        summary = ImportSummary(
            tasks_imported=0,
            tasks_skipped=0,
            comments_imported=0,
            comments_skipped=0,
            skipped_task_ids=[],
            skipped_comment_ids=[],
        )

        # Get existing task IDs
        existing_task_ids = {t.id for t in self._task_manager.list_all()}
        existing_comment_ids = {c.id for c in self._comments_service._comments.values()}

        # Import tasks
        task_id_map = {}  # map of imported task IDs
        for task_data in tasks_data:
            try:
                if not isinstance(task_data, dict):
                    summary.tasks_skipped += 1
                    continue

                task_id = task_data.get("id")
                if not task_id:
                    summary.tasks_skipped += 1
                    continue

                # Check if task already exists
                if task_id in existing_task_ids:
                    summary.tasks_skipped += 1
                    summary.skipped_task_ids.append(task_id[:8])
                    task_id_map[task_id] = task_id  # track for comments
                    continue

                # Validate required fields
                if "title" not in task_data:
                    summary.tasks_skipped += 1
                    summary.skipped_task_ids.append(task_id[:8])
                    continue

                # Create task from dict
                task = Task.from_dict(task_data)
                self._task_manager._tasks[task.id] = task
                existing_task_ids.add(task.id)
                task_id_map[task.id] = task.id
                summary.tasks_imported += 1

            except (ValueError, KeyError, TypeError):
                summary.tasks_skipped += 1
                task_id = task_data.get("id", "unknown")
                if isinstance(task_id, str):
                    summary.skipped_task_ids.append(task_id[:8])

        # Persist after importing tasks
        if summary.tasks_imported > 0:
            self._task_manager._persist()

        # Import comments
        for comment_data in comments_data:
            try:
                if not isinstance(comment_data, dict):
                    summary.comments_skipped += 1
                    continue

                comment_id = comment_data.get("id")
                if not comment_id:
                    summary.comments_skipped += 1
                    continue

                # Check if comment already exists
                if comment_id in existing_comment_ids:
                    summary.comments_skipped += 1
                    summary.skipped_comment_ids.append(comment_id[:8])
                    continue

                # Validate required fields
                task_id = comment_data.get("task_id")
                if not task_id or task_id not in existing_task_ids:
                    summary.comments_skipped += 1
                    summary.skipped_comment_ids.append(comment_id[:8])
                    continue

                if "content" not in comment_data:
                    summary.comments_skipped += 1
                    summary.skipped_comment_ids.append(comment_id[:8])
                    continue

                # Create comment from dict
                comment = TaskComment.from_dict(comment_data)
                self._comments_service._comments[comment.id] = comment
                existing_comment_ids.add(comment.id)
                summary.comments_imported += 1

            except (ValueError, KeyError, TypeError):
                summary.comments_skipped += 1
                comment_id = comment_data.get("id", "unknown")
                if isinstance(comment_id, str):
                    summary.skipped_comment_ids.append(comment_id[:8])

        # Persist after importing comments
        if summary.comments_imported > 0:
            self._comments_service._persist()

        return summary
