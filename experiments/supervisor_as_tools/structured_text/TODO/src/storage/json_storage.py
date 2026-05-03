import json
from pathlib import Path
from typing import Optional


class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Support backward compatibility: if data is a list, assume it's tasks
            if isinstance(data, list):
                return data
            # New format: {"tasks": [...], "comments": [...]}
            if isinstance(data, dict):
                return data.get("tasks", [])
        return []

    def save(self, tasks: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing comments to preserve them
        comments = self.load_comments()
        data = {"tasks": tasks, "comments": comments}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_comments(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Support backward compatibility: if data is a list, no comments exist
            if isinstance(data, list):
                return []
            # New format: {"tasks": [...], "comments": [...]}
            if isinstance(data, dict):
                return data.get("comments", [])
        return []

    def save_comments(self, comments: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing tasks to preserve them
        tasks = self.load()
        data = {"tasks": tasks, "comments": comments}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_data(self, tasks: list[dict], comments: list[dict]) -> None:
        """Import tasks and comments, replacing all existing data.

        Args:
            tasks: List of task dictionaries.
            comments: List of comment dictionaries.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"tasks": tasks, "comments": comments}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
