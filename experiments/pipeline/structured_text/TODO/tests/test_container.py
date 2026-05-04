"""Tests for the dependency injection Container."""

import pytest
from pathlib import Path
from src.container import Container
from src.repositories.task_repository import TaskRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.project_repository import ProjectRepository
from src.services.todo_service import TodoService


class TestContainerInitialization:
    """Tests for Container initialization."""

    def test_container_default_initialization(self):
        """Container() initializes with default storage path."""
        container = Container()
        assert container is not None

    def test_container_custom_storage_path(self, tmp_path):
        """Container(storage_path) uses custom path."""
        custom_path = tmp_path / "custom_tasks.json"
        container = Container(str(custom_path))
        assert container is not None


class TestContainerRepositoryCreation:
    """Tests for Container repository creation and injection."""

    def test_get_task_repository(self, tmp_path):
        """get_task_repository() returns a TaskRepository."""
        container = Container(str(tmp_path / "tasks.json"))
        repo = container.get_task_repository()
        assert isinstance(repo, TaskRepository)

    def test_get_task_repository_singleton(self, tmp_path):
        """get_task_repository() returns same instance on multiple calls."""
        container = Container(str(tmp_path / "tasks.json"))
        repo1 = container.get_task_repository()
        repo2 = container.get_task_repository()
        assert repo1 is repo2

    def test_get_comment_repository(self, tmp_path):
        """get_comment_repository() returns a CommentRepository."""
        container = Container(str(tmp_path / "tasks.json"))
        repo = container.get_comment_repository()
        assert isinstance(repo, CommentRepository)

    def test_get_comment_repository_singleton(self, tmp_path):
        """get_comment_repository() returns same instance on multiple calls."""
        container = Container(str(tmp_path / "tasks.json"))
        repo1 = container.get_comment_repository()
        repo2 = container.get_comment_repository()
        assert repo1 is repo2

    def test_get_project_repository(self, tmp_path):
        """get_project_repository() returns a ProjectRepository."""
        container = Container(str(tmp_path / "tasks.json"))
        repo = container.get_project_repository()
        assert isinstance(repo, ProjectRepository)

    def test_get_project_repository_singleton(self, tmp_path):
        """get_project_repository() returns same instance on multiple calls."""
        container = Container(str(tmp_path / "tasks.json"))
        repo1 = container.get_project_repository()
        repo2 = container.get_project_repository()
        assert repo1 is repo2


class TestContainerServiceCreation:
    """Tests for Container service creation and injection."""

    def test_get_todo_service(self, tmp_path):
        """get_todo_service() returns a TodoService."""
        container = Container(str(tmp_path / "tasks.json"))
        service = container.get_todo_service()
        assert isinstance(service, TodoService)

    def test_get_todo_service_singleton(self, tmp_path):
        """get_todo_service() returns same instance on multiple calls."""
        container = Container(str(tmp_path / "tasks.json"))
        service1 = container.get_todo_service()
        service2 = container.get_todo_service()
        assert service1 is service2

    def test_todo_service_has_repositories(self, tmp_path):
        """get_todo_service() returns service with injected repositories."""
        container = Container(str(tmp_path / "tasks.json"))
        service = container.get_todo_service()

        # Verify the service has repositories injected
        assert service._task_repository is not None
        assert service._comment_repository is not None
        assert service._project_repository is not None

        # Verify they are the correct types
        assert isinstance(service._task_repository, TaskRepository)
        assert isinstance(service._comment_repository, CommentRepository)
        assert isinstance(service._project_repository, ProjectRepository)


class TestContainerStoragePathProvider:
    """Tests for Container's path provider integration."""

    def test_task_and_comment_paths_are_related(self, tmp_path):
        """Container derives comment path from task path."""
        base_path = tmp_path / "tasks.json"
        container = Container(str(base_path))

        task_repo = container.get_task_repository()
        comment_repo = container.get_comment_repository()

        # Comment path should be .todo_comments.json in same directory
        # This is an indirect test; we verify by checking both repos work
        task = task_repo.add("Task")
        comment = comment_repo.add(task.id, "Comment")

        assert comment.task_id == task.id

    def test_custom_storage_path_affects_all_repos(self, tmp_path):
        """Custom storage path is used for all repositories."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        base_path = custom_dir / "my_tasks.json"

        container = Container(str(base_path))

        # Add data through all repos
        task = container.get_task_repository().add("Task")
        comment = container.get_comment_repository().add(task.id, "Comment")
        project = container.get_project_repository().add("Project")

        # Verify files are created in custom location
        assert (custom_dir / "my_tasks.json").exists()
        assert (custom_dir / ".todo_comments.json").exists()
        assert (custom_dir / ".todo_projects.json").exists()


class TestContainerIntegration:
    """Integration tests for Container with TodoService."""

    def test_full_workflow_through_container(self, tmp_path):
        """Container enables full workflow: add task, comment, project, export."""
        container = Container(str(tmp_path / "tasks.json"))
        service = container.get_todo_service()

        # Add task
        task = service.add_task("Important Task")
        assert task.id is not None

        # Add comment
        comment = service.add_comment(task.id, "Looks good")
        assert comment.task_id == task.id

        # Create project
        project = service.create_project("Q1 Work")
        assert project.id is not None

        # Assign task to project
        updated = service.assign_task_to_project(task.id, project.id)
        assert updated.project_id == project.id

        # List all
        tasks = service.list_tasks()
        comments = service.get_comments(task.id)
        projects = service.list_projects()

        assert len(tasks) == 1
        assert len(comments) == 1
        assert len(projects) == 1

    def test_container_with_no_custom_path(self):
        """Container works with default path (uses home directory)."""
        # Just verify it doesn't crash; we won't actually write to home
        container = Container(None)
        assert container is not None
        # Don't create service as it would write to real home dir

    def test_repositories_share_same_storage_base(self, tmp_path):
        """All repositories created by container use related storage paths."""
        base = tmp_path / "app_data.json"
        container = Container(str(base))

        task_repo = container.get_task_repository()
        comment_repo = container.get_comment_repository()
        project_repo = container.get_project_repository()

        # Verify repos are in place and working
        t = task_repo.add("Task")
        c = comment_repo.add(t.id, "Comment")
        p = project_repo.add("Project")

        # All data should be persistent
        assert task_repo.list_all() == [t]
        assert comment_repo.list_all() == [c]
        assert project_repo.list_all() == [p]
