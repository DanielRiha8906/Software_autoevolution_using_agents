from datetime import datetime
from ..models.task import Task
from ..models.task_status import TaskStatus


class TaskSerializer:
    """Static methods for serializing and deserializing Task objects."""

    @staticmethod
    def to_dict(task: Task) -> dict:
        """Convert a Task to a dictionary representation.

        Args:
            task: The Task to serialize

        Returns:
            Dictionary with task data, omitting optional fields if None
        """
        result = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
        if task.due_date is not None:
            result["due_date"] = task.due_date.isoformat()
        if task.project_id is not None:
            result["project_id"] = task.project_id
        return result

    @staticmethod
    def from_dict(data: dict) -> Task:
        """Construct a Task from a dictionary representation.

        Args:
            data: Dictionary with task data

        Returns:
            Task instance reconstructed from the dictionary
        """
        due_date_str = data.get("due_date")
        due_date = None
        if due_date_str is not None:
            due_date = datetime.fromisoformat(due_date_str)

        return Task(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=due_date,
            project_id=data.get("project_id"),
        )
