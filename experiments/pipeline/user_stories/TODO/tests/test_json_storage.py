import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from src.storage.json_storage import JsonStorage


def test_load_missing_file(tmp_path):
    storage = JsonStorage(str(tmp_path / "nonexistent.json"))
    assert storage.load() == {"tasks": [], "projects": []}


def test_save_and_load(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JsonStorage(str(path))
    data = {"tasks": [{"id": "1", "title": "hello"}], "projects": []}
    storage.save(data)
    assert storage.load() == data


def test_save_creates_parent_dirs(tmp_path):
    path = tmp_path / "deep" / "nested" / "tasks.json"
    storage = JsonStorage(str(path))
    storage.save([])
    assert path.exists()


def test_overwrite(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JsonStorage(str(path))
    storage.save({"tasks": [{"id": "1"}], "projects": []})
    storage.save({"tasks": [{"id": "2"}], "projects": []})
    assert storage.load() == {"tasks": [{"id": "2"}], "projects": []}


# ─── Backward compatibility tests ───────────────────────────────────────────

def test_load_legacy_task_without_due_date():
    """Test loading legacy tasks that don't have due_date field"""
    from src.models.task import Task

    # Simulate legacy data without due_date key
    legacy_data = {
        "id": "legacy-id",
        "title": "Old task",
        "description": "Created before due_date feature",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Should not raise, due_date should be None
    task = Task.from_dict(legacy_data)
    assert task.due_date is None
    assert task.title == "Old task"


def test_load_mixed_legacy_and_new_tasks(tmp_path):
    """Test loading a file with mixed legacy and new tasks"""
    from src.models.task import Task

    path = tmp_path / "mixed_tasks.json"
    storage = JsonStorage(str(path))

    # Create mixed data: legacy without due_date, new with due_date
    legacy = {
        "id": "legacy-1",
        "title": "Legacy",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    new = {
        "id": "new-1",
        "title": "New",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "due_date": "2026-05-15T14:30:00+00:00",
    }

    storage.save({"tasks": [legacy, new], "projects": []})
    loaded = storage.load()

    assert "tasks" in loaded
    assert "projects" in loaded
    tasks = loaded["tasks"]
    assert len(tasks) == 2
    assert tasks[0]["id"] == "legacy-1"
    assert "due_date" not in tasks[0]
    assert tasks[1]["id"] == "new-1"
    assert tasks[1]["due_date"] == "2026-05-15T14:30:00+00:00"
