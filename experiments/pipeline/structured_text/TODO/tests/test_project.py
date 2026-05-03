"""Tests for Project model (Task 08).

Tests cover:
- Project dataclass creation and defaults
- to_dict() and from_dict() round-trip
- Validation (empty names)
- Datetime serialization (ISO8601 format in UTC)
"""

import pytest
from datetime import datetime, timezone
from src.models.project import Project


class TestProjectCreation:
    """Test Project dataclass instantiation."""

    def test_project_requires_name(self):
        """Project requires a name at construction."""
        project = Project(name="Test Project")
        assert project.name == "Test Project"

    def test_project_id_generated(self):
        """Project ID is auto-generated as UUID string."""
        project = Project(name="Test")
        assert project.id is not None
        assert isinstance(project.id, str)
        assert len(project.id) > 0

    def test_project_ids_unique(self):
        """Each project gets a unique ID."""
        p1 = Project(name="A")
        p2 = Project(name="B")
        assert p1.id != p2.id

    def test_project_created_at_default(self):
        """Project has created_at timestamp set to now(UTC)."""
        before = datetime.now(timezone.utc)
        project = Project(name="Test")
        after = datetime.now(timezone.utc)

        assert project.created_at is not None
        assert project.created_at.tzinfo is not None
        assert before <= project.created_at <= after

    def test_project_with_explicit_id(self):
        """Project can be created with explicit ID."""
        explicit_id = "custom-id-12345"
        project = Project(name="Test", id=explicit_id)
        assert project.id == explicit_id

    def test_project_with_explicit_created_at(self):
        """Project can be created with explicit created_at."""
        explicit_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        project = Project(name="Test", created_at=explicit_time)
        assert project.created_at == explicit_time


class TestProjectToDict:
    """Test Project.to_dict() serialization."""

    def test_to_dict_includes_id(self):
        """to_dict() includes project ID."""
        project = Project(name="Test")
        result = project.to_dict()
        assert "id" in result
        assert result["id"] == project.id

    def test_to_dict_includes_name(self):
        """to_dict() includes project name."""
        project = Project(name="My Project")
        result = project.to_dict()
        assert "name" in result
        assert result["name"] == "My Project"

    def test_to_dict_includes_created_at(self):
        """to_dict() includes created_at as ISO8601 string."""
        project = Project(name="Test")
        result = project.to_dict()
        assert "created_at" in result
        assert isinstance(result["created_at"], str)

    def test_to_dict_created_at_isoformat(self):
        """created_at is serialized in ISO8601 format."""
        explicit_time = datetime(2025, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
        project = Project(name="Test", created_at=explicit_time)
        result = project.to_dict()
        assert result["created_at"] == explicit_time.isoformat()

    def test_to_dict_returns_dict_with_three_keys(self):
        """to_dict() returns dict with exactly 3 keys."""
        project = Project(name="Test")
        result = project.to_dict()
        assert len(result) == 3
        assert set(result.keys()) == {"id", "name", "created_at"}


class TestProjectFromDict:
    """Test Project.from_dict() deserialization."""

    def test_from_dict_basic(self):
        """from_dict() reconstructs Project from dict."""
        data = {
            "id": "test-id-123",
            "name": "Reconstructed",
            "created_at": "2025-01-01T12:00:00+00:00",
        }
        project = Project.from_dict(data)
        assert project.id == "test-id-123"
        assert project.name == "Reconstructed"

    def test_from_dict_created_at_parsing(self):
        """from_dict() parses created_at from ISO8601 string."""
        iso_time = "2025-05-15T14:30:45+00:00"
        data = {
            "id": "test-id",
            "name": "Test",
            "created_at": iso_time,
        }
        project = Project.from_dict(data)
        assert project.created_at == datetime.fromisoformat(iso_time)

    def test_from_dict_preserves_timezone(self):
        """from_dict() preserves UTC timezone info."""
        data = {
            "id": "test-id",
            "name": "Test",
            "created_at": "2025-01-01T00:00:00+00:00",
        }
        project = Project.from_dict(data)
        assert project.created_at.tzinfo is not None


class TestProjectRoundTrip:
    """Test round-trip conversion: Project → to_dict() → from_dict() → Project."""

    def test_roundtrip_preserves_all_fields(self):
        """Round-trip conversion preserves all fields."""
        original = Project(name="Test Project")
        restored = Project.from_dict(original.to_dict())

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.created_at == original.created_at

    def test_roundtrip_with_explicit_time(self):
        """Round-trip with explicit timestamp preserves datetime exactly."""
        explicit_time = datetime(2025, 3, 15, 9, 45, 30, tzinfo=timezone.utc)
        original = Project(name="Timed", created_at=explicit_time)
        restored = Project.from_dict(original.to_dict())

        assert restored.created_at == explicit_time

    def test_roundtrip_multiple_cycles(self):
        """Multiple round-trips preserve data integrity."""
        original = Project(name="Cycle Test")
        cycle1 = Project.from_dict(original.to_dict())
        cycle2 = Project.from_dict(cycle1.to_dict())
        cycle3 = Project.from_dict(cycle2.to_dict())

        assert cycle3.id == original.id
        assert cycle3.name == original.name
        assert cycle3.created_at == original.created_at


class TestProjectValidation:
    """Test Project validation and constraints."""

    def test_project_name_can_contain_special_chars(self):
        """Project name can contain special characters."""
        special_names = [
            "Project with spaces",
            "Project-with-dashes",
            "Project_with_underscores",
            "Project (2025)",
            "Project #1",
        ]
        for name in special_names:
            project = Project(name=name)
            assert project.name == name

    def test_project_name_can_be_long(self):
        """Project name can be arbitrarily long."""
        long_name = "A" * 1000
        project = Project(name=long_name)
        assert project.name == long_name

    def test_project_empty_string_name_allowed_at_construction(self):
        """Note: empty name is allowed at construction (validation done at service level)."""
        # The Project dataclass itself doesn't validate; validation is in ProjectManager
        project = Project(name="")
        assert project.name == ""


class TestProjectDatetimeHandling:
    """Test datetime serialization and parsing edge cases."""

    def test_created_at_isoformat_roundtrip(self):
        """ISO format round-trip preserves datetime exactly."""
        time = datetime(2026, 5, 3, 21, 55, 0, tzinfo=timezone.utc)
        project = Project(name="Test", created_at=time)

        dict_repr = project.to_dict()
        iso_str = dict_repr["created_at"]

        restored = Project.from_dict({"id": project.id, "name": project.name, "created_at": iso_str})
        assert restored.created_at == time

    def test_created_at_with_microseconds(self):
        """Datetime with microseconds round-trips correctly."""
        time = datetime(2025, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        project = Project(name="Test", created_at=time)
        restored = Project.from_dict(project.to_dict())
        assert restored.created_at == time
        assert restored.created_at.microsecond == 123456
