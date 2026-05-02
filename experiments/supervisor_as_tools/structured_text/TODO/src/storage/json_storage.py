import json
from pathlib import Path
from typing import Optional


class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"

    @property
    def path(self) -> Path:
        return self._path

    def _load_raw_data(self) -> list[dict] | dict:
        """Load raw data from file, handling both old list and new dict formats."""
        if not self._path.exists():
            return {"tasks": [], "comments": []}
        with self._path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"tasks": [], "comments": []}
            data = json.loads(content)
        return data

    def load(self) -> list[dict]:
        """Load tasks only, for backward compatibility.

        Returns:
            List of task dicts. Automatically migrates from old list format if needed.
        """
        raw = self._load_raw_data()
        # If raw is a list, it's old format - return as-is
        if isinstance(raw, list):
            return raw
        # If raw is a dict with 'tasks' key, it's new format
        return raw.get("tasks", [])

    def save(self, tasks: list[dict]) -> None:
        """Save tasks only, preserving existing comments in storage.

        Args:
            tasks: List of task dicts to save.
        """
        # Load existing data to preserve comments
        raw = self._load_raw_data()
        comments = []
        if isinstance(raw, dict):
            comments = raw.get("comments", [])

        # Save in new format
        data = {"tasks": tasks, "comments": comments}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_all(self) -> dict:
        """Load all data (tasks and comments) in new format.

        Returns:
            Dict with "tasks" and "comments" keys. Automatically migrates
            from old list format if needed.
        """
        raw = self._load_raw_data()
        # If raw is a list, it's old format - migrate to new format
        if isinstance(raw, list):
            return {"tasks": raw, "comments": []}
        # If raw is a dict, it's already in new format
        return raw

    def save_all(self, data: dict) -> None:
        """Save all data (tasks and comments) in new format.

        Args:
            data: Dict with "tasks" and "comments" keys.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
