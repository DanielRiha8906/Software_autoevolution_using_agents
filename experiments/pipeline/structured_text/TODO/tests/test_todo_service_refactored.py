"""Tests for TodoService with repository injection (refactored architecture)."""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from src.services.todo_service import TodoService
from src.repositories.task_repository import TaskRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.project_repository import ProjectRepository
from src.models.task_status import TaskStatus
from src.exceptions import TaskNotFoundError, CommentNotFoundError, ProjectNotFoundError


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
    )


# ===== Task Management Tests =====

class TestTodoServiceTaskManagement:
    """Tests for task management methods."""

    def test_add_task(self, service):
        """add_task() creates a task."""
        task = service.add_task("Learn pytest")
        assert task.title == "Learn pytest"
        assert task.status == TaskStatus.PENDING

    def test_add_task_with_description(self, service):
        """add_task() supports description."""
        task = service.add_task("Title", "Long description")
        assert task.description == "Long description"

    def test_add_task_strips_whitespace(self, service):
        """add_task() strips title whitespace."""
        task = service.add_task("  padded  ")
        assert task.title == "padded"

    def test_add_task_empty_title_raises(self, service):
        """add_task() raises ValueError for empty title."""
        with pytest.raises(ValueError):
            service.add_task("   ")

    def test_add_task_none_title_raises(self, service):
        """add_task() raises ValueError for None title."""
        with pytest.raises(ValueError):
            service.add_task("")

    def test_get_task(self, service):
        """get_task() retrieves a task."""
        task = service.add_task("Task")
        retrieved = service.get_task(task.id)
        assert retrieved.id == task.id

    def test_get_task_by_prefix(self, service):
        """get_task() works with ID prefix."""
        task = service.add_task("Task")
        prefix = task.id[:8]
        retrieved = service.get_task(prefix)
        assert retrieved.id == task.id

    def test_get_nonexistent_task_raises(self, service):
        """get_task() raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.get_task("nonexistent")


class TestTodoServiceListTasks:
    """Tests for task listing and filtering."""

    def test_list_tasks_all(self, service):
        """list_tasks() returns all tasks."""
        service.add_task("Task1")
        service.add_task("Task2")
        tasks = service.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_empty(self, service):
        """list_tasks() returns empty list when no tasks."""
        assert service.list_tasks() == []

    def test_list_tasks_by_status(self, service):
        """list_tasks(status=...) filters by status."""
        t1 = service.add_task("Pending")
        t2 = service.add_task("Done")
        service.complete_task(t2.id)

        pending = service.list_tasks(status=TaskStatus.PENDING)
        done = service.list_tasks(status=TaskStatus.DONE)

        assert len(pending) == 1
        assert pending[0].id == t1.id
        assert len(done) == 1
        assert done[0].id == t2.id

    def test_list_tasks_by_due_date_range(self, service):
        """list_tasks(due_after=..., due_before=...) filters by date."""
        now = datetime.now(timezone.utc)

        t1 = service.add_task("Due yesterday")
        t2 = service.add_task("Due tomorrow")

        # Manually set due dates
        service._task_repository._items[t1.id].due_date = now - timedelta(days=1)
        service._task_repository._items[t2.id].due_date = now + timedelta(days=1)
        service._task_repository._persist()

        # Filter for future dates
        tasks = service.list_tasks(due_after=now)
        assert len(tasks) == 1
        assert tasks[0].id == t2.id

    def test_list_tasks_invalid_date_range_raises(self, service):
        """list_tasks() raises ValueError if due_after > due_before."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            service.list_tasks(due_after=now, due_before=now - timedelta(days=1))

    def test_list_tasks_by_overdue(self, service):
        """list_tasks(overdue=True/False) filters overdue tasks."""
        now = datetime.now(timezone.utc)

        t1 = service.add_task("Overdue")
        t2 = service.add_task("Not overdue")

        service._task_repository._items[t1.id].due_date = now - timedelta(days=1)
        service._task_repository._items[t2.id].due_date = now + timedelta(days=1)
        service._task_repository._persist()

        overdue = service.list_tasks(overdue=True)
        not_overdue = service.list_tasks(overdue=False)

        assert len(overdue) == 1
        assert overdue[0].id == t1.id
        assert len(not_overdue) == 1
        assert not_overdue[0].id == t2.id


class TestTodoServiceTaskStatus:
    """Tests for task status transitions."""

    def test_start_task(self, service):
        """start_task() sets status to IN_PROGRESS."""
        task = service.add_task("Task")
        started = service.start_task(task.id)
        assert started.status == TaskStatus.IN_PROGRESS

    def test_start_task_by_prefix(self, service):
        """start_task() works with prefix."""
        task = service.add_task("Task")
        prefix = task.id[:8]
        started = service.start_task(prefix)
        assert started.status == TaskStatus.IN_PROGRESS

    def test_complete_task(self, service):
        """complete_task() sets status to DONE."""
        task = service.add_task("Task")
        done = service.complete_task(task.id)
        assert done.status == TaskStatus.DONE

    def test_reopen_task(self, service):
        """reopen_task() sets status to PENDING."""
        task = service.add_task("Task")
        service.complete_task(task.id)
        reopened = service.reopen_task(task.id)
        assert reopened.status == TaskStatus.PENDING


class TestTodoServiceUpdateTask:
    """Tests for task update."""

    def test_update_task_title(self, service):
        """update_task(title=...) changes title."""
        task = service.add_task("Old")
        updated = service.update_task(task.id, title="New")
        assert updated.title == "New"

    def test_update_task_description(self, service):
        """update_task(description=...) changes description."""
        task = service.add_task("Title")
        updated = service.update_task(task.id, description="New desc")
        assert updated.description == "New desc"

    def test_update_task_title_and_description(self, service):
        """update_task() can update both."""
        task = service.add_task("Old")
        updated = service.update_task(task.id, title="New", description="Desc")
        assert updated.title == "New"
        assert updated.description == "Desc"

    def test_update_task_empty_title_raises(self, service):
        """update_task(title='') raises ValueError."""
        task = service.add_task("Title")
        with pytest.raises(ValueError):
            service.update_task(task.id, title="")

    def test_update_task_empty_title_whitespace_raises(self, service):
        """update_task(title='  ') raises ValueError."""
        task = service.add_task("Title")
        with pytest.raises(ValueError):
            service.update_task(task.id, title="   ")

    def test_update_nonexistent_task_raises(self, service):
        """update_task() raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.update_task("nonexistent", title="New")


class TestTodoServiceDeleteTask:
    """Tests for task deletion."""

    def test_delete_task(self, service):
        """delete_task() removes a task."""
        task = service.add_task("ToDelete")
        service.delete_task(task.id)
        with pytest.raises(TaskNotFoundError):
            service.get_task(task.id)

    def test_delete_task_by_prefix(self, service):
        """delete_task() works with prefix."""
        task = service.add_task("ToDelete")
        prefix = task.id[:8]
        service.delete_task(prefix)
        with pytest.raises(TaskNotFoundError):
            service.get_task(task.id)

    def test_delete_task_cascade_deletes_comments(self, service):
        """delete_task() removes all comments for that task."""
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "Comment1")
        c2 = service.add_comment(task.id, "Comment2")

        service.delete_task(task.id)

        # Comments should be gone
        with pytest.raises(CommentNotFoundError):
            service.delete_comment(c1.id)

    def test_delete_task_does_not_cascade_other_tasks_comments(self, service):
        """delete_task() only deletes comments for that task."""
        task1 = service.add_task("Task1")
        task2 = service.add_task("Task2")
        c1 = service.add_comment(task1.id, "On task1")
        c2 = service.add_comment(task2.id, "On task2")

        service.delete_task(task1.id)

        # Task2 and its comment still exist
        assert service.get_task(task2.id) is not None
        assert len(service.get_comments(task2.id)) == 1


# ===== Comment Management Tests =====

class TestTodoServiceCommentManagement:
    """Tests for comment management."""

    def test_add_comment(self, service):
        """add_comment() creates a comment."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Great!")
        assert comment.task_id == task.id
        assert comment.content == "Great!"
        assert comment.author is None

    def test_add_comment_with_author(self, service):
        """add_comment(author=...) sets author."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Comment", author="Alice")
        assert comment.author == "Alice"

    def test_add_comment_strips_whitespace(self, service):
        """add_comment() strips content whitespace."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "  content  ")
        assert comment.content == "content"

    def test_add_comment_empty_content_raises(self, service):
        """add_comment('') raises ValueError."""
        task = service.add_task("Task")
        with pytest.raises(ValueError):
            service.add_comment(task.id, "")

    def test_add_comment_whitespace_only_raises(self, service):
        """add_comment('  ') raises ValueError."""
        task = service.add_task("Task")
        with pytest.raises(ValueError):
            service.add_comment(task.id, "   ")

    def test_add_comment_nonexistent_task_raises(self, service):
        """add_comment() on nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.add_comment("nonexistent", "Comment")

    def test_add_comment_with_task_prefix(self, service):
        """add_comment() works with task ID prefix."""
        task = service.add_task("Task")
        prefix = task.id[:8]
        comment = service.add_comment(prefix, "Comment")
        assert comment.task_id == task.id


class TestTodoServiceGetComments:
    """Tests for getting comments."""

    def test_get_comments_empty(self, service):
        """get_comments() returns empty list for task with no comments."""
        task = service.add_task("Task")
        comments = service.get_comments(task.id)
        assert comments == []

    def test_get_comments_all(self, service):
        """get_comments() returns all comments for task."""
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "First")
        c2 = service.add_comment(task.id, "Second")

        comments = service.get_comments(task.id)
        assert len(comments) == 2

    def test_get_comments_chronological(self, service):
        """get_comments() returns comments in chronological order."""
        import time
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "First")
        time.sleep(0.01)
        c2 = service.add_comment(task.id, "Second")
        time.sleep(0.01)
        c3 = service.add_comment(task.id, "Third")

        comments = service.get_comments(task.id)
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id
        assert comments[2].id == c3.id

    def test_get_comments_nonexistent_task_raises(self, service):
        """get_comments() raises TaskNotFoundError for nonexistent task."""
        with pytest.raises(TaskNotFoundError):
            service.get_comments("nonexistent")

    def test_get_comments_with_prefix(self, service):
        """get_comments() works with task ID prefix."""
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "Comment")
        prefix = task.id[:8]

        comments = service.get_comments(prefix)
        assert len(comments) == 1
        assert comments[0].id == c1.id


class TestTodoServiceDeleteComment:
    """Tests for comment deletion."""

    def test_delete_comment(self, service):
        """delete_comment() removes a comment."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "ToDelete")
        service.delete_comment(comment.id)

        comments = service.get_comments(task.id)
        assert len(comments) == 0

    def test_delete_comment_by_prefix(self, service):
        """delete_comment() works with prefix."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "ToDelete")
        prefix = comment.id[:8]

        service.delete_comment(prefix)
        comments = service.get_comments(task.id)
        assert len(comments) == 0

    def test_delete_comment_nonexistent_raises(self, service):
        """delete_comment() raises CommentNotFoundError."""
        with pytest.raises(CommentNotFoundError):
            service.delete_comment("nonexistent")

    def test_delete_comment_preserves_others(self, service):
        """delete_comment() only removes specified comment."""
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "Keep")
        c2 = service.add_comment(task.id, "Delete")

        service.delete_comment(c2.id)

        comments = service.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].id == c1.id


# ===== Statistics Tests =====

class TestTodoServiceStatistics:
    """Tests for task statistics."""

    def test_get_statistics_empty(self, service):
        """get_statistics() works with no tasks."""
        stats = service.get_statistics()
        assert stats.total_count == 0
        assert stats.pending_count == 0
        assert stats.in_progress_count == 0
        assert stats.done_count == 0

    def test_get_statistics_counts(self, service):
        """get_statistics() counts tasks by status."""
        service.add_task("T1")
        service.add_task("T2")
        t3 = service.add_task("T3")

        service.start_task(t3.id)
        service.complete_task(service.add_task("T4").id)

        stats = service.get_statistics()
        assert stats.total_count == 4
        assert stats.pending_count == 2
        assert stats.in_progress_count == 1
        assert stats.done_count == 1

    def test_get_statistics_overdue_count(self, service):
        """get_statistics() counts overdue tasks."""
        now = datetime.now(timezone.utc)
        t1 = service.add_task("Overdue")
        t2 = service.add_task("Not overdue")

        service._task_repository._items[t1.id].due_date = now - timedelta(days=1)
        service._task_repository._items[t2.id].due_date = now + timedelta(days=1)
        service._task_repository._persist()

        stats = service.get_statistics()
        assert stats.overdue_count == 1
        assert stats.with_due_date_count == 2


# ===== Project Management Tests =====

class TestTodoServiceProjectManagement:
    """Tests for project management."""

    def test_create_project(self, service):
        """create_project() creates a project."""
        project = service.create_project("Q1 Goals")
        assert project.name == "Q1 Goals"

    def test_create_project_strips_whitespace(self, service):
        """create_project() strips name whitespace."""
        project = service.create_project("  Project  ")
        assert project.name == "Project"

    def test_create_project_empty_raises(self, service):
        """create_project('') raises ValueError."""
        with pytest.raises(ValueError):
            service.create_project("")

    def test_create_project_whitespace_raises(self, service):
        """create_project('  ') raises ValueError."""
        with pytest.raises(ValueError):
            service.create_project("   ")

    def test_get_project(self, service):
        """get_project() retrieves a project."""
        project = service.create_project("Project")
        retrieved = service.get_project(project.id)
        assert retrieved.id == project.id

    def test_list_projects(self, service):
        """list_projects() returns all projects."""
        service.create_project("P1")
        service.create_project("P2")
        projects = service.list_projects()
        assert len(projects) == 2

    def test_delete_project(self, service):
        """delete_project() removes a project."""
        project = service.create_project("ToDelete")
        service.delete_project(project.id)
        with pytest.raises(ProjectNotFoundError):
            service.get_project(project.id)

    def test_delete_project_unassigns_tasks(self, service):
        """delete_project() unassigns all tasks."""
        project = service.create_project("Project")
        task = service.add_task("Task")
        service.assign_task_to_project(task.id, project.id)

        service.delete_project(project.id)

        # Task is still there but unassigned
        task = service.get_task(task.id)
        assert task.project_id is None

    def test_update_project(self, service):
        """update_project() changes project name."""
        project = service.create_project("Old")
        updated = service.update_project(project.id, "New")
        assert updated.name == "New"

    def test_update_project_empty_name_raises(self, service):
        """update_project() raises ValueError for empty name."""
        project = service.create_project("Project")
        with pytest.raises(ValueError):
            service.update_project(project.id, "")


class TestTodoServiceProjectTaskAssignment:
    """Tests for task-project assignment."""

    def test_list_tasks_by_project(self, service):
        """list_tasks_by_project() returns tasks in project."""
        project = service.create_project("Project")
        t1 = service.add_task("In project")
        t2 = service.add_task("Not in project")

        service.assign_task_to_project(t1.id, project.id)

        tasks = service.list_tasks_by_project(project.id)
        assert len(tasks) == 1
        assert tasks[0].id == t1.id

    def test_assign_task_to_project(self, service):
        """assign_task_to_project() assigns task to project."""
        project = service.create_project("Project")
        task = service.add_task("Task")

        updated = service.assign_task_to_project(task.id, project.id)
        assert updated.project_id == project.id

    def test_unassign_task_from_project(self, service):
        """unassign_task_from_project() removes assignment."""
        project = service.create_project("Project")
        task = service.add_task("Task")
        service.assign_task_to_project(task.id, project.id)

        updated = service.unassign_task_from_project(task.id)
        assert updated.project_id is None

    def test_assign_nonexistent_task_raises(self, service):
        """assign_task_to_project() raises TaskNotFoundError."""
        project = service.create_project("Project")
        with pytest.raises(TaskNotFoundError):
            service.assign_task_to_project("nonexistent", project.id)

    def test_assign_to_nonexistent_project_raises(self, service):
        """assign_task_to_project() raises ProjectNotFoundError."""
        task = service.add_task("Task")
        with pytest.raises(ProjectNotFoundError):
            service.assign_task_to_project(task.id, "nonexistent")
