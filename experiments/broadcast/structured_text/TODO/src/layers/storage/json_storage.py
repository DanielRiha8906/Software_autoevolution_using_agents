"""JSON file storage implementation."""

import json
from pathlib import Path
from typing import Optional, Union


class JsonStorage:
    """Persistent JSON storage for task data."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Union[list[dict], dict]:
        """Load data from storage.

        Returns:
            If the file contains a list of dicts (legacy tasks format),
            returns the list. If it contains a dict with 'tasks' key,
            returns the entire dict. If file doesn't exist, returns empty list.
        """
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Support both formats: list (legacy tasks) or dict (with tasks/comments)
        return data

    def save(self, data: Union[list[dict], dict]) -> None:
        """Save data to storage.

        Args:
            data: Either a list of task dicts (legacy format) or
                  a dict with 'tasks' and/or 'comments' keys.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
