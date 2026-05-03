import json
from datetime import datetime
from typing import Tuple

from ..models import Task, TaskComment, TaskStatus
from .task_manager import TaskManager
from .comments_service import CommentsService


class ImportExportService:
    def __init__(self, task_manager: TaskManager, comments_service: CommentsService) -> None:
        self._task_manager = task_manager
        self._comments_service = comments_service

    def export_to_json(self, file_path: str) -> int:
        """
        Export all tasks and comments to a JSON file.

        Args:
            file_path: Path to the JSON file to write

        Returns:
            int: Number of tasks exported

        Raises:
            OSError: If file write fails
        """
        tasks = self._task_manager.list_all()
        tasks_data = [task.to_dict() for task in tasks]

        comments_data = []
        for comment in self._comments_service._comments.values():
            comments_data.append(comment.to_dict())

        export_data = {
            "version": 1,
            "export_date": datetime.utcnow().isoformat() + "Z",
            "tasks": tasks_data,
            "comments": comments_data,
        }

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return len(tasks)

    def import_from_json(
        self, file_path: str, merge_mode: str = "skip"
    ) -> Tuple[int, int, int, int]:
        """
        Import tasks and comments from a JSON file.

        Args:
            file_path: Path to JSON export file
            merge_mode: "skip" (default) or "overwrite"

        Returns:
            Tuple: (tasks_imported, tasks_skipped, comments_imported, comments_skipped)

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If JSON is invalid or missing required keys
        """
        # Load and validate file
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

        if "tasks" not in data or "comments" not in data:
            raise ValueError("Missing 'tasks' or 'comments' key in JSON file")

        tasks_imported = 0
        tasks_skipped = 0
        comments_imported = 0
        comments_skipped = 0

        # Import tasks
        for task_data in data.get("tasks", []):
            try:
                task = Task.from_dict(task_data)

                # Check if already exists
                try:
                    existing = self._task_manager.get(task.id)
                    if merge_mode == "skip":
                        print(f"Skipped task {task.id[:8]}: already exists")
                        tasks_skipped += 1
                        continue
                    # For overwrite mode, delete and re-add
                except:
                    pass

                # Try to add the task
                self._task_manager._tasks[task.id] = task
                self._task_manager._persist()
                tasks_imported += 1
            except Exception as e:
                print(f"Skipped task: {str(e)[:50]}")
                tasks_skipped += 1

        # Import comments
        for comment_data in data.get("comments", []):
            try:
                comment = TaskComment.from_dict(comment_data)

                # Validate task exists
                try:
                    self._task_manager.get(comment.task_id)
                except:
                    print(f"Skipped comment {comment.id[:8]}: task {comment.task_id[:8]} not found")
                    comments_skipped += 1
                    continue

                # Check if comment already exists
                if comment.id in self._comments_service._comments:
                    print(f"Skipped comment {comment.id[:8]}: already exists")
                    comments_skipped += 1
                    continue

                # Add comment
                self._comments_service._comments[comment.id] = comment
                self._comments_service._persist()
                comments_imported += 1
            except Exception as e:
                print(f"Skipped comment: {str(e)[:50]}")
                comments_skipped += 1

        return (tasks_imported, tasks_skipped, comments_imported, comments_skipped)
