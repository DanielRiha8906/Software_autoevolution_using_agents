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
        # Support both list format (legacy) and dict format with "tasks" key
        if isinstance(data, list):
            return data
        return data.get("tasks", []) if isinstance(data, dict) else []

    def save(self, tasks: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing data to preserve comments if they exist
        existing_data = {}
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    file_data = json.load(f)
                if isinstance(file_data, dict):
                    existing_data = file_data
            except (json.JSONDecodeError, IOError):
                pass

        # Merge tasks with existing data
        existing_data["tasks"] = tasks

        with self._path.open("w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

    def load_comments(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # If data is a list (old format), return empty
        if isinstance(data, list):
            return []
        # If data is a dict with "comments" key, return comments
        return data.get("comments", []) if isinstance(data, dict) else []

    def save_comments(self, comments: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing data
        existing_data = {}
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    file_data = json.load(f)
                if isinstance(file_data, dict):
                    existing_data = file_data
                elif isinstance(file_data, list):
                    existing_data = {"tasks": file_data}
            except (json.JSONDecodeError, IOError):
                pass

        # Update comments
        existing_data["comments"] = comments

        # Save back
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

    def load_projects(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # If data is a list (old format), return empty
        if isinstance(data, list):
            return []
        # If data is a dict with "projects" key, return projects
        return data.get("projects", []) if isinstance(data, dict) else []

    def save_projects(self, projects: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing data
        existing_data = {}
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    file_data = json.load(f)
                if isinstance(file_data, dict):
                    existing_data = file_data
                elif isinstance(file_data, list):
                    existing_data = {"tasks": file_data}
            except (json.JSONDecodeError, IOError):
                pass

        # Update projects
        existing_data["projects"] = projects

        # Save back
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
