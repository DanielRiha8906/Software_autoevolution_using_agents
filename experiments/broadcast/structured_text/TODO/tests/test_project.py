import pytest
from src.models.project import Project


def test_project_defaults():
    project = Project(name="Work")
    assert project.name == "Work"
    assert project.id is not None


def test_project_unique_ids():
    p1 = Project(name="A")
    p2 = Project(name="B")
    assert p1.id != p2.id


def test_project_roundtrip():
    project = Project(name="Test Project")
    restored = Project.from_dict(project.to_dict())
    assert restored.id == project.id
    assert restored.name == project.name
