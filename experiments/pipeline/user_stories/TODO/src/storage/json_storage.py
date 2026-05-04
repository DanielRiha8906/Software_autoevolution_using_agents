import json
from pathlib import Path
from typing import Optional, Union


class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Union[dict, list[dict]]:
        """Load data from JSON file.

        Returns:
            Union[dict, list[dict]]: Data with "tasks" and "projects" keys (new format),
            or legacy list format (old format).

        Auto-migrates old format (list of dicts) to new format (dict with keys).
        """
        if not self._path.exists():
            return {"tasks": [], "projects": []}
        try:
            with self._path.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {"tasks": [], "projects": []}
                data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return {"tasks": [], "projects": []}

        # Auto-migrate old format (simple list) to new format (dict)
        if isinstance(data, list):
            return {"tasks": data, "projects": []}
        return data

    def save(self, data: Union[dict, list[dict]]) -> None:
        """Save data to JSON file.

        Args:
            data: Dict with "tasks" and "projects" keys, or legacy list format.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
