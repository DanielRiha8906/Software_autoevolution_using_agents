"""Tests for import/export services with repository injection."""

import pytest
import json
from pathlib import Path
from src.services.todo_service import TodoService
from src.services.import_export_service import ExportService, ImportService
from src.repositories.task_repository import TaskRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.project_repository import ProjectRepository
from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.project import Project
from src.exceptions import ImportExportError


@pytest.fixture
def service(tmp_path):
    """Create a TodoService with injected repositories."""
    task_repo = TaskRepository(tmp_path / "tasks.json")
    comment_repo = CommentRepository(tmp_path / "comments.json")
    project_repo = ProjectRepository(tmp_path / "projects.json")
    return TodoService(
        task_repository=task_repo,
        comment_repository=comment_repo,
        project_repository=project_repo,
    ), tmp_path


class TestExportService:
    """Tests for ExportService."""

    def test_export_empty_repositories(self, service, tmp_path):
        """export_to_file() exports empty repositories."""
        svc, _ = service
        export_path = tmp_path / "export.json"

        task_counts = svc.export_tasks_and_comments(str(export_path))
        assert task_counts == (0, 0, 0)

        assert export_path.exists()
        with open(export_path) as f:
            data = json.load(f)
        assert data["tasks"] == []
        assert data["comments"] == []
        assert data["projects"] == []

    def test_export_with_data(self, service, tmp_path):
        """export_to_file() exports tasks, comments, and projects."""
        svc, _ = service

        # Create data
        task = svc.add_task("Task1", "Description")
        comment = svc.add_comment(task.id, "Comment1", author="Alice")
        project = svc.create_project("Project1")

        export_path = tmp_path / "export.json"
        tasks_count, comments_count, projects_count = svc.export_tasks_and_comments(str(export_path))

        assert tasks_count == 1
        assert comments_count == 1
        assert projects_count == 1

        # Verify file structure
        with open(export_path) as f:
            data = json.load(f)

        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Task1"

        assert len(data["comments"]) == 1
        assert data["comments"][0]["content"] == "Comment1"

        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Project1"

    def test_export_creates_parent_directory(self, service, tmp_path):
        """export_to_file() creates parent directories if needed."""
        svc, _ = service
        svc.add_task("Task")

        nested_path = tmp_path / "nested" / "dir" / "export.json"
        svc.export_tasks_and_comments(str(nested_path))

        assert nested_path.exists()

    def test_export_multiple_entities(self, service, tmp_path):
        """export_to_file() exports multiple of each entity."""
        svc, _ = service

        # Create multiple tasks
        t1 = svc.add_task("T1")
        t2 = svc.add_task("T2")

        # Comments on both
        c1 = svc.add_comment(t1.id, "C1")
        c2 = svc.add_comment(t1.id, "C2")
        c3 = svc.add_comment(t2.id, "C3")

        # Projects
        p1 = svc.create_project("P1")
        p2 = svc.create_project("P2")

        export_path = tmp_path / "export.json"
        counts = svc.export_tasks_and_comments(str(export_path))

        assert counts == (2, 3, 2)

        with open(export_path) as f:
            data = json.load(f)

        assert len(data["tasks"]) == 2
        assert len(data["comments"]) == 3
        assert len(data["projects"]) == 2


class TestImportServiceBasic:
    """Tests for basic ImportService functionality."""

    def test_import_empty_file(self, tmp_path):
        """import_from_file() imports empty data."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Create empty export
        export_path = tmp_path / "empty.json"
        svc.export_tasks_and_comments(str(export_path))

        # Service to import to
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        counts = new_svc.import_tasks_and_comments(str(export_path))

        # 0 imported, 0 conflicts
        assert counts == (0, 0, 0, 0)

    def test_import_with_data(self, tmp_path):
        """import_from_file() imports tasks, comments, and projects."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Create and export
        task = svc.add_task("Task1")
        comment = svc.add_comment(task.id, "Comment1")
        project = svc.create_project("Project1")

        export_path = tmp_path / "export.json"
        svc.export_tasks_and_comments(str(export_path))

        # Service to import to (separate storage)
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        counts = new_svc.import_tasks_and_comments(str(export_path))

        # Should import 1 task, 1 comment, 1 project, 0 conflicts
        assert counts == (1, 1, 1, 0)

        # Verify imported data
        tasks = new_svc.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Task1"

        comments = new_svc.get_comments(tasks[0].id)
        assert len(comments) == 1
        assert comments[0].content == "Comment1"

        projects = new_svc.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "Project1"


class TestImportServiceConflictModes:
    """Tests for import conflict handling modes."""

    def test_import_fail_mode_with_conflicts(self, tmp_path):
        """import_from_file(mode='fail') raises on conflicts."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Export with data
        task = svc.add_task("Task1")
        export_path = tmp_path / "export.json"
        svc.export_tasks_and_comments(str(export_path))

        # New service with same task title but different ID
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        new_svc.add_task("Task1")  # Same title, different ID

        # This should succeed (no ID conflict, only title is same)
        counts = new_svc.import_tasks_and_comments(str(export_path), mode="fail")
        # Should import without conflict (different IDs)
        assert counts[0] == 1  # 1 task imported

    def test_import_fail_mode_detects_id_conflict(self, tmp_path):
        """import_from_file(mode='fail') raises on ID conflict."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Create task with known ID
        task = svc.add_task("Task1")
        export_path = tmp_path / "export.json"
        svc.export_tasks_and_comments(str(export_path))

        # New service and add task with same ID (manually)
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        new_task = Task(id=task.id, title="Different")
        new_svc._task_repository.add_many([new_task])

        # Import should fail with conflict
        with pytest.raises(ImportExportError) as excinfo:
            new_svc.import_tasks_and_comments(str(export_path), mode="fail")
        assert "conflict" in str(excinfo.value).lower()

    def test_import_skip_mode_skips_conflicts(self, tmp_path):
        """import_from_file(mode='skip') skips conflicting items."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Create export with 2 tasks
        t1 = svc.add_task("Task1")
        t2 = svc.add_task("Task2")
        export_path = tmp_path / "export.json"
        svc.export_tasks_and_comments(str(export_path))

        # New service with conflicting task
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        conflict_task = Task(id=t1.id, title="Conflict")
        new_svc._task_repository.add_many([conflict_task])

        # Import with skip mode
        counts = new_svc.import_tasks_and_comments(str(export_path), mode="skip")

        # 1 imported (t2), 1 conflict (t1)
        assert counts == (1, 0, 0, 1)

        # Verify only t2 was imported
        tasks = new_svc.list_tasks()
        assert len(tasks) == 2
        task_ids = {t.id for t in tasks}
        assert t1.id in task_ids  # Original conflict task
        assert t2.id in task_ids  # Imported non-conflicting task

    def test_import_replace_mode_overwrites(self, tmp_path):
        """import_from_file(mode='replace') overwrites conflicting items."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Export with task
        t1 = svc.add_task("Original")
        export_path = tmp_path / "export.json"
        svc.export_tasks_and_comments(str(export_path))

        # New service with conflicting task
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        original_task = Task(id=t1.id, title="Different")
        new_svc._task_repository.add_many([original_task])

        # Import with replace mode
        counts = new_svc.import_tasks_and_comments(str(export_path), mode="replace")

        # 1 imported (replaced), 1 conflict detected but replaced
        assert counts == (1, 0, 0, 1)

        # Verify task was replaced
        tasks = new_svc.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Original"


class TestImportServiceValidation:
    """Tests for import validation."""

    def test_import_file_not_found(self, service):
        """import_from_file() raises for missing file."""
        svc, _ = service
        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments("/nonexistent/path.json")
        assert "not found" in str(excinfo.value).lower()

    def test_import_invalid_json(self, service, tmp_path):
        """import_from_file() raises for invalid JSON."""
        svc, _ = service
        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text("{ invalid json ")

        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments(str(invalid_path))
        assert "json" in str(excinfo.value).lower()

    def test_import_missing_tasks_key(self, service, tmp_path):
        """import_from_file() raises if 'tasks' key missing."""
        svc, _ = service
        invalid_path = tmp_path / "missing_tasks.json"
        invalid_path.write_text(json.dumps({"comments": []}))

        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments(str(invalid_path))
        assert "tasks" in str(excinfo.value).lower()

    def test_import_missing_comments_key(self, service, tmp_path):
        """import_from_file() raises if 'comments' key missing."""
        svc, _ = service
        invalid_path = tmp_path / "missing_comments.json"
        invalid_path.write_text(json.dumps({"tasks": []}))

        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments(str(invalid_path))
        assert "comments" in str(excinfo.value).lower()

    def test_import_tasks_not_list(self, service, tmp_path):
        """import_from_file() raises if 'tasks' is not a list."""
        svc, _ = service
        invalid_path = tmp_path / "bad_tasks.json"
        invalid_path.write_text(json.dumps({"tasks": "not a list", "comments": []}))

        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments(str(invalid_path))
        assert "list" in str(excinfo.value).lower()

    def test_import_invalid_mode(self, service, tmp_path):
        """import_from_file(mode=...) raises for invalid mode."""
        svc, _ = service
        export_path = tmp_path / "export.json"
        svc.export_tasks_and_comments(str(export_path))

        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments(str(export_path), mode="invalid")
        assert "mode" in str(excinfo.value).lower()

    def test_import_projects_not_list(self, service, tmp_path):
        """import_from_file() raises if 'projects' is not a list."""
        svc, _ = service
        invalid_path = tmp_path / "bad_projects.json"
        invalid_path.write_text(json.dumps({
            "tasks": [],
            "comments": [],
            "projects": "not a list"
        }))

        with pytest.raises(ImportExportError) as excinfo:
            svc.import_tasks_and_comments(str(invalid_path))
        assert "list" in str(excinfo.value).lower()


class TestImportExportRoundTrip:
    """Integration tests for export and import round trips."""

    def test_round_trip_preserves_data(self, tmp_path):
        """Export and import preserves all data."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        # Create complex data
        t1 = svc.add_task("Task1", "Desc1")
        t2 = svc.add_task("Task2")
        svc.start_task(t2.id)

        c1 = svc.add_comment(t1.id, "Comment1", author="Alice")
        c2 = svc.add_comment(t1.id, "Comment2")
        c3 = svc.add_comment(t2.id, "Comment3", author="Bob")

        p1 = svc.create_project("Project1")
        p2 = svc.create_project("Project2")

        svc.assign_task_to_project(t1.id, p1.id)

        # Export
        export_path = tmp_path / "round_trip.json"
        svc.export_tasks_and_comments(str(export_path))

        # Service to import to
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        counts = new_svc.import_tasks_and_comments(str(export_path))

        assert counts[0] == 2  # 2 tasks
        assert counts[1] == 3  # 3 comments
        assert counts[2] == 2  # 2 projects

        # Verify all data matches
        new_tasks = new_svc.list_tasks()
        assert len(new_tasks) == 2

        # Find tasks by title
        imported_t1 = [t for t in new_tasks if t.title == "Task1"][0]
        imported_t2 = [t for t in new_tasks if t.title == "Task2"][0]

        assert imported_t1.description == "Desc1"
        assert imported_t2.status.value == "in_progress"

        # Check comments
        t1_comments = new_svc.get_comments(imported_t1.id)
        assert len(t1_comments) == 2

        # Check projects
        new_projects = new_svc.list_projects()
        assert len(new_projects) == 2

    def test_round_trip_with_empty_repository(self, tmp_path):
        """Export and import empty repository works."""
        # Service to export from
        svc = TodoService(
            TaskRepository(tmp_path / "export_tasks.json"),
            CommentRepository(tmp_path / "export_comments.json"),
            ProjectRepository(tmp_path / "export_projects.json"),
        )

        export_path = tmp_path / "empty.json"
        svc.export_tasks_and_comments(str(export_path))

        # Service to import to
        new_svc = TodoService(
            TaskRepository(tmp_path / "import_tasks.json"),
            CommentRepository(tmp_path / "import_comments.json"),
            ProjectRepository(tmp_path / "import_projects.json"),
        )
        counts = new_svc.import_tasks_and_comments(str(export_path))

        assert counts == (0, 0, 0, 0)
        assert len(new_svc.list_tasks()) == 0
