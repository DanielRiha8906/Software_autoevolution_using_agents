import pytest
from src.models.project import Project


class TestProjectCreation:
    """Test basic Project model creation and validation."""

    def test_project_creation(self):
        """Test creating a project with valid name."""
        project = Project(name="My Project")
        assert project.name == "My Project"
        assert project.id is not None
        assert isinstance(project.id, str)
        assert len(project.id) > 0

    def test_project_name_empty_validation(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            Project(name="")

    def test_project_name_whitespace_validation(self):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            Project(name="   ")

    def test_project_name_stripped(self):
        """Test that project name is stripped of leading/trailing whitespace."""
        project = Project(name="  My Project  ")
        assert project.name == "My Project"

    def test_project_to_dict(self):
        """Test serializing project to dict."""
        project = Project(name="Test Project", id="test-123")
        data = project.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "test-123"
        assert data["name"] == "Test Project"
        assert len(data) == 2  # Only id and name

    def test_project_from_dict(self):
        """Test deserializing project from dict."""
        data = {"id": "proj-456", "name": "Restored Project"}
        project = Project.from_dict(data)

        assert project.id == "proj-456"
        assert project.name == "Restored Project"

    def test_project_unique_ids(self):
        """Test that each project gets a unique ID."""
        p1 = Project(name="Project 1")
        p2 = Project(name="Project 2")
        assert p1.id != p2.id
