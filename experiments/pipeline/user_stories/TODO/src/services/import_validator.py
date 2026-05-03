"""Validation logic for importing tasks from JSON files."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.task_status import TaskStatus


class ImportValidator:
    """Validates JSON files and task data for import operations."""

    def validate_file(self, file_path: str) -> tuple[list[dict], list[dict]]:
        """Validate a JSON file and extract valid tasks.

        Args:
            file_path: Path to the JSON file to validate.

        Returns:
            tuple[list[dict], list[dict]]: A tuple of (validated_tasks, errors) where:
                - validated_tasks: List of valid task dictionaries
                - errors: List of error messages for invalid entries or file issues

        The validated_tasks list contains only valid task dictionaries.
        Individual task validation errors are collected in the errors list.
        """
        errors: list[dict] = []
        validated_tasks: list[dict] = []

        # Check if file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return [], [{"error": f"File not found: {file_path}"}]

        # Try to read and parse JSON
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return [], [{"error": "File is empty"}]
                data = __import__("json").loads(content)
        except __import__("json").JSONDecodeError as e:
            return [], [{"error": f"Invalid JSON syntax: {e}"}]
        except Exception as e:
            return [], [{"error": f"Error reading file: {e}"}]

        # Check if data is an array
        if not isinstance(data, list):
            return [], [{"error": "JSON root must be an array"}]

        # Validate each task
        seen_ids: set[str] = set()
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append({"index": index, "error": "Task entry must be an object"})
                continue

            error_msg = self.validate_task_dict(item, index)
            if error_msg:
                errors.append({"index": index, "error": error_msg})
                continue

            # Check for duplicate IDs within the import file
            task_id = item.get("id")
            if task_id in seen_ids:
                errors.append(
                    {"index": index, "error": f"Duplicate task ID in import file: {task_id}"}
                )
                continue

            seen_ids.add(task_id)
            validated_tasks.append(item)

        return validated_tasks, errors

    @staticmethod
    def validate_task_dict(task_dict: dict, index: int) -> Optional[str]:
        """Validate a single task dictionary.

        Args:
            task_dict: Task data as a dictionary.
            index: Index of the task in the array (for error messages).

        Returns:
            Optional[str]: Error message if validation fails, None if valid.
        """
        # Required fields
        required_fields = ["id", "title", "status", "created_at", "updated_at"]
        for field in required_fields:
            if field not in task_dict:
                return f"Missing required field: {field}"
            if task_dict[field] is None:
                return f"Field '{field}' cannot be null"

        # Validate id
        task_id = task_dict.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            return "Task ID must be a non-empty string"

        # Validate title
        title = task_dict.get("title")
        if not isinstance(title, str) or not title.strip():
            return "Task title must be a non-empty string"

        # Validate status
        status = task_dict.get("status")
        if not isinstance(status, str):
            return "Task status must be a string"
        try:
            TaskStatus(status)
        except ValueError:
            valid_values = ", ".join([s.value for s in TaskStatus])
            return f"Invalid status '{status}'. Must be one of: {valid_values}"

        # Validate created_at (ISO format datetime)
        created_at_str = task_dict.get("created_at")
        if not isinstance(created_at_str, str):
            return "created_at must be a string in ISO 8601 format"
        try:
            datetime.fromisoformat(created_at_str)
        except (ValueError, TypeError):
            return f"Invalid created_at format: {created_at_str}. Must be ISO 8601 format"

        # Validate updated_at (ISO format datetime)
        updated_at_str = task_dict.get("updated_at")
        if not isinstance(updated_at_str, str):
            return "updated_at must be a string in ISO 8601 format"
        try:
            datetime.fromisoformat(updated_at_str)
        except (ValueError, TypeError):
            return f"Invalid updated_at format: {updated_at_str}. Must be ISO 8601 format"

        # Validate optional due_date
        if "due_date" in task_dict and task_dict["due_date"] is not None:
            due_date_str = task_dict.get("due_date")
            if not isinstance(due_date_str, str):
                return "due_date must be a string in ISO 8601 format or null"
            try:
                datetime.fromisoformat(due_date_str)
            except (ValueError, TypeError):
                return f"Invalid due_date format: {due_date_str}. Must be ISO 8601 format"

        # Validate optional description
        if "description" in task_dict and task_dict["description"] is not None:
            description = task_dict.get("description")
            if not isinstance(description, str):
                return "description must be a string or null"

        # Validate optional comments
        if "comments" in task_dict and task_dict["comments"] is not None:
            comments = task_dict.get("comments")
            if not isinstance(comments, list):
                return "comments must be an array or null"

            for comment_index, comment in enumerate(comments):
                if not isinstance(comment, dict):
                    return f"Comment {comment_index} must be an object"

                # Validate comment fields
                if "id" not in comment:
                    return f"Comment {comment_index}: missing required field 'id'"
                if "task_id" not in comment:
                    return f"Comment {comment_index}: missing required field 'task_id'"
                if "content" not in comment:
                    return f"Comment {comment_index}: missing required field 'content'"

                # Validate comment content is not empty
                content = comment.get("content")
                if not isinstance(content, str) or not content.strip():
                    # Skip empty comments but allow the task to proceed
                    continue

                # Validate comment created_at
                if "created_at" not in comment:
                    return f"Comment {comment_index}: missing required field 'created_at'"
                comment_created_at_str = comment.get("created_at")
                if not isinstance(comment_created_at_str, str):
                    return f"Comment {comment_index}: created_at must be a string in ISO 8601 format"
                try:
                    datetime.fromisoformat(comment_created_at_str)
                except (ValueError, TypeError):
                    return f"Comment {comment_index}: invalid created_at format. Must be ISO 8601 format"

        return None
