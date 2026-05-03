"""Tests for Project model."""
import pytest
import uuid
from datetime import datetime, timezone
from src.models.project import Project


def test_project_can_be_created():
    """Test basic project creation."""
    assert Project(name="Work") is not None


def test_project_defaults():
    """Test that Project has sensible defaults."""
    project = Project(name="Work")
    assert project.name == "Work"
    assert project.id is not None
    assert project.description is None
    assert project.created_at is not None


def test_project_has_unique_ids():
    """Test that each Project gets a unique ID."""
    p1 = Project(name="Work")
    p2 = Project(name="Work")
    assert p1.id != p2.id


def test_project_id_is_uuid_string():
    """Test that project IDs are valid UUID strings."""
    project = Project(name="Work")
    parsed = uuid.UUID(project.id)
    assert str(parsed) == project.id


def test_empty_project_name_raises():
    """Test that empty project name raises ValueError."""
    with pytest.raises(ValueError):
        Project(name="")


def test_whitespace_only_name_raises():
    """Test that whitespace-only project name raises ValueError."""
    with pytest.raises(ValueError):
        Project(name="   ")


def test_project_with_description():
    """Test creating a project with a description."""
    project = Project(name="Work", description="Work-related tasks")
    assert project.description == "Work-related tasks"


def test_project_to_dict():
    """Test converting a project to dict."""
    project = Project(name="Work")
    d = project.to_dict()
    assert d["id"] == project.id
    assert d["name"] == "Work"
    assert d["created_at"] == project.created_at.isoformat()
    assert "description" not in d  # Not included when None


def test_project_to_dict_with_description():
    """Test converting a project with description to dict."""
    project = Project(name="Work", description="My tasks")
    d = project.to_dict()
    assert d["description"] == "My tasks"


def test_project_from_dict():
    """Test creating a project from dict."""
    data = {
        "id": "test-id-123",
        "name": "Work",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    project = Project.from_dict(data)
    assert project.id == "test-id-123"
    assert project.name == "Work"
    assert project.description is None


def test_project_from_dict_with_description():
    """Test creating a project from dict with description."""
    data = {
        "id": "test-id-123",
        "name": "Work",
        "description": "My work tasks",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    project = Project.from_dict(data)
    assert project.description == "My work tasks"


def test_project_roundtrip():
    """Test that a project survives to_dict -> from_dict roundtrip."""
    original = Project(name="Work", description="Tasks")
    restored = Project.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.description == original.description
    assert restored.created_at == original.created_at


def test_project_roundtrip_without_description():
    """Test roundtrip for project without description."""
    original = Project(name="Work")
    restored = Project.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.description is None


def test_project_created_at_defaults_to_now():
    """Test that created_at defaults to current time."""
    before = datetime.now(timezone.utc)
    project = Project(name="Work")
    after = datetime.now(timezone.utc)
    assert before <= project.created_at <= after


def test_project_created_at_can_be_set():
    """Test that created_at can be explicitly set."""
    specific_time = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
    project = Project(name="Work", created_at=specific_time)
    assert project.created_at == specific_time
