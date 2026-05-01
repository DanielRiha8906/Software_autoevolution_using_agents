import json
import pytest
from pathlib import Path
from src.storage.json_storage import JsonStorage


def test_load_missing_file(tmp_path):
    storage = JsonStorage(str(tmp_path / "nonexistent.json"))
    assert storage.load() == []


def test_save_and_load(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JsonStorage(str(path))
    data = [{"id": "1", "title": "hello"}]
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
    storage.save([{"id": "1"}])
    storage.save([{"id": "2"}])
    assert storage.load() == [{"id": "2"}]
