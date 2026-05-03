import json
from pathlib import Path
from typing import Optional


class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"
        self._cached_comments: list[dict] = []

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[dict]:
        if not self._path.exists():
            self._cached_comments = []
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Support legacy format (list of tasks) and new format (dict with tasks and comments)
            if isinstance(data, list):
                self._cached_comments = []
                return data
            elif isinstance(data, dict) and "tasks" in data:
                self._cached_comments = data.get("comments", [])
                return data["tasks"]
            return []

    def save(self, tasks: list[dict]) -> None:
        """Save tasks, preserving any cached comments."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Always use the unified format
        data = {"tasks": tasks, "comments": self._cached_comments}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_comments(self) -> list[dict]:
        """Load all comments from storage."""
        if not self._path.exists():
            self._cached_comments = []
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Support new format (dict with tasks and comments)
            if isinstance(data, dict) and "comments" in data:
                self._cached_comments = data["comments"]
                return data["comments"]
            self._cached_comments = []
            return []

    def save_all(self, tasks: list[dict], comments: list[dict]) -> None:
        """Save both tasks and comments to storage."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._cached_comments = comments
        data = {"tasks": tasks, "comments": comments}
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
