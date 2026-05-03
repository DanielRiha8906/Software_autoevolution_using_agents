import pytest
from datetime import datetime, timezone

from src.models.project import Project


def test_project_defaults():
    project = Project(name="Work")
    assert project.name == "Work"
    assert project.id is not None
    assert project.created_at is not None
    assert isinstance(project.created_at, datetime)


def test_project_unique_ids():
    a = Project(name="A")
    b = Project(name="B")
    assert a.id != b.id


def test_project_name_stripped():
    project = Project(name="  Work  ")
    # The project stores the name as-is; validation happens in ProjectManager
    assert project.name == "  Work  "


def test_project_empty_name_raises():
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="")


def test_project_whitespace_only_name_raises():
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="   ")


def test_project_roundtrip():
    project = Project(name="Work")
    restored = Project.from_dict(project.to_dict())
    assert restored.id == project.id
    assert restored.name == project.name
    assert restored.created_at == project.created_at


def test_project_serialization():
    project = Project(name="Work")
    project_dict = project.to_dict()
    assert "id" in project_dict
    assert "name" in project_dict
    assert "created_at" in project_dict
    assert project_dict["name"] == "Work"


def test_project_deserialization():
    data = {
        "id": "test-id",
        "name": "Work",
        "created_at": "2026-01-01T10:00:00+00:00",
    }
    project = Project.from_dict(data)
    assert project.id == "test-id"
    assert project.name == "Work"
    assert project.created_at == datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
