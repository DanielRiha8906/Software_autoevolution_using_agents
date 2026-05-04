import pytest

from src.models.project import Project


def test_project_creation():
    project = Project(name="My Project")
    assert project.name == "My Project"
    assert project.id is not None


def test_project_name_stripped():
    project = Project(name="  Project  ")
    assert project.name == "Project"


def test_project_empty_name_raises():
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="")


def test_project_whitespace_only_name_raises():
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="   ")


def test_project_unique_ids():
    p1 = Project(name="P1")
    p2 = Project(name="P2")
    assert p1.id != p2.id


def test_project_to_dict():
    project = Project(name="Test Project", id="test-id")
    data = project.to_dict()
    assert data == {"id": "test-id", "name": "Test Project"}


def test_project_from_dict():
    data = {"id": "test-id", "name": "Test Project"}
    project = Project.from_dict(data)
    assert project.id == "test-id"
    assert project.name == "Test Project"


def test_project_roundtrip():
    original = Project(name="Test")
    restored = Project.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.name == original.name
