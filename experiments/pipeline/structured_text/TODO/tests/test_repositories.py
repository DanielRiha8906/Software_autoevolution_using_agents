"""Tests for repository layer (TaskRepository, CommentRepository, ProjectRepository)."""

import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from src.repositories.task_repository import TaskRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.project_repository import ProjectRepository
from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.project import Project
from src.models.task_status import TaskStatus
from src.exceptions import TaskNotFoundError, CommentNotFoundError, ProjectNotFoundError


# ===== Fixtures =====

@pytest.fixture
def task_repo(tmp_path):
    """Create a TaskRepository with a temporary storage file."""
    return TaskRepository(tmp_path / "tasks.json")


@pytest.fixture
def comment_repo(tmp_path):
    """Create a CommentRepository with a temporary storage file."""
    return CommentRepository(tmp_path / "comments.json")


@pytest.fixture
def project_repo(tmp_path):
    """Create a ProjectRepository with a temporary storage file."""
    return ProjectRepository(tmp_path / "projects.json")


# ===== TaskRepository Tests =====

class TestTaskRepositoryAdd:
    """Tests for TaskRepository.add()."""

    def test_add_task_basic(self, task_repo):
        """add() creates a task with required title."""
        task = task_repo.add("Test Task")
        assert task.title == "Test Task"
        assert task.id is not None
        assert task.status == TaskStatus.PENDING
        assert task.description is None

    def test_add_task_with_description(self, task_repo):
        """add() supports optional description."""
        task = task_repo.add("Title", "A description")
        assert task.title == "Title"
        assert task.description == "A description"

    def test_add_task_persists(self, task_repo, tmp_path):
        """add() writes task to storage."""
        task = task_repo.add("Persistent")
        # Create new repo instance pointing to same file
        repo2 = TaskRepository(tmp_path / "tasks.json")
        retrieved = repo2.get(task.id)
        assert retrieved.title == "Persistent"

    def test_add_multiple_tasks(self, task_repo):
        """add() can be called multiple times."""
        t1 = task_repo.add("First")
        t2 = task_repo.add("Second")
        assert t1.id != t2.id
        assert len(task_repo.list_all()) == 2


class TestTaskRepositoryGet:
    """Tests for TaskRepository.get()."""

    def test_get_exact_id(self, task_repo):
        """get() retrieves task by exact ID."""
        task = task_repo.add("Title")
        retrieved = task_repo.get(task.id)
        assert retrieved.id == task.id
        assert retrieved.title == "Title"

    def test_get_by_prefix(self, task_repo):
        """get() supports unique prefix matching."""
        task = task_repo.add("Title")
        prefix = task.id[:8]
        retrieved = task_repo.get(prefix)
        assert retrieved.id == task.id

    def test_get_nonexistent_raises(self, task_repo):
        """get() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            task_repo.get("nonexistent-id")

    def test_get_ambiguous_prefix_raises(self, task_repo):
        """get() raises TaskNotFoundError when prefix matches multiple tasks."""
        # Create tasks with overlapping UUIDs (very unlikely in practice, but test the error path)
        # We'll create two tasks and manually give them IDs that share a prefix
        t1 = task_repo.add("Task1")
        t2 = task_repo.add("Task2")
        # Manually modify IDs in the internal dict to create ambiguous prefix scenario
        original_t1_id = t1.id
        original_t2_id = t2.id
        # Use a common prefix for both
        prefix = "abc123"
        task_repo._items[prefix + "xxx"] = task_repo._items.pop(original_t1_id)
        task_repo._items[prefix + "yyy"] = task_repo._items.pop(original_t2_id)

        with pytest.raises(TaskNotFoundError) as excinfo:
            task_repo.get(prefix)
        assert "Ambiguous prefix" in str(excinfo.value)


class TestTaskRepositoryListAll:
    """Tests for TaskRepository.list_all()."""

    def test_list_all_empty(self, task_repo):
        """list_all() returns empty list when no tasks exist."""
        assert task_repo.list_all() == []

    def test_list_all_returns_all(self, task_repo):
        """list_all() returns all tasks."""
        t1 = task_repo.add("Task1")
        t2 = task_repo.add("Task2")
        t3 = task_repo.add("Task3")
        tasks = task_repo.list_all()
        assert len(tasks) == 3
        ids = {t.id for t in tasks}
        assert t1.id in ids and t2.id in ids and t3.id in ids


class TestTaskRepositoryDelete:
    """Tests for TaskRepository.delete()."""

    def test_delete_exact_id(self, task_repo):
        """delete() removes task by exact ID."""
        task = task_repo.add("ToDelete")
        task_repo.delete(task.id)
        assert len(task_repo.list_all()) == 0

    def test_delete_by_prefix(self, task_repo):
        """delete() supports prefix matching."""
        task = task_repo.add("ToDelete")
        prefix = task.id[:8]
        task_repo.delete(prefix)
        assert len(task_repo.list_all()) == 0

    def test_delete_nonexistent_raises(self, task_repo):
        """delete() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            task_repo.delete("nonexistent")

    def test_delete_persists(self, task_repo, tmp_path):
        """delete() persists removal to storage."""
        task = task_repo.add("ToDelete")
        task_repo.delete(task.id)
        repo2 = TaskRepository(tmp_path / "tasks.json")
        assert len(repo2.list_all()) == 0


class TestTaskRepositoryUpdate:
    """Tests for TaskRepository.update()."""

    def test_update_title(self, task_repo):
        """update() changes task title."""
        task = task_repo.add("Old")
        updated = task_repo.update(task.id, title="New")
        assert updated.title == "New"

    def test_update_description(self, task_repo):
        """update() changes task description."""
        task = task_repo.add("Title", "Old desc")
        updated = task_repo.update(task.id, description="New desc")
        assert updated.description == "New desc"

    def test_update_title_and_description(self, task_repo):
        """update() can change both title and description."""
        task = task_repo.add("Old", "Old desc")
        updated = task_repo.update(task.id, title="New", description="New desc")
        assert updated.title == "New"
        assert updated.description == "New desc"

    def test_update_sets_updated_at(self, task_repo):
        """update() updates the updated_at timestamp."""
        task = task_repo.add("Title")
        original_updated_at = task.updated_at
        import time
        time.sleep(0.01)
        updated = task_repo.update(task.id, title="New")
        assert updated.updated_at > original_updated_at

    def test_update_nonexistent_raises(self, task_repo):
        """update() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            task_repo.update("nonexistent", title="New")


class TestTaskRepositorySetStatus:
    """Tests for TaskRepository.set_status()."""

    @pytest.mark.parametrize("status", [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.DONE])
    def test_set_status(self, task_repo, status):
        """set_status() changes task status."""
        task = task_repo.add("Task")
        updated = task_repo.set_status(task.id, status)
        assert updated.status == status

    def test_set_status_nonexistent_raises(self, task_repo):
        """set_status() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            task_repo.set_status("nonexistent", TaskStatus.DONE)


class TestTaskRepositoryListByStatus:
    """Tests for TaskRepository.list_by_status()."""

    def test_list_by_status_empty(self, task_repo):
        """list_by_status() returns empty list when no tasks match."""
        task_repo.add("Task")
        tasks = task_repo.list_by_status(TaskStatus.DONE)
        assert tasks == []

    def test_list_by_status_returns_matching(self, task_repo):
        """list_by_status() returns only tasks with given status."""
        t1 = task_repo.add("Pending")
        t2 = task_repo.add("Done")
        task_repo.set_status(t2.id, TaskStatus.DONE)

        pending = task_repo.list_by_status(TaskStatus.PENDING)
        done = task_repo.list_by_status(TaskStatus.DONE)

        assert len(pending) == 1
        assert pending[0].id == t1.id
        assert len(done) == 1
        assert done[0].id == t2.id


class TestTaskRepositoryListByFilter:
    """Tests for TaskRepository.list_by_filter()."""

    def test_list_by_filter_no_filters(self, task_repo):
        """list_by_filter() with no filters returns all tasks."""
        t1 = task_repo.add("T1")
        t2 = task_repo.add("T2")
        tasks = task_repo.list_by_filter()
        assert len(tasks) == 2

    def test_list_by_filter_status(self, task_repo):
        """list_by_filter() filters by status."""
        t1 = task_repo.add("T1")
        t2 = task_repo.add("T2")
        task_repo.set_status(t2.id, TaskStatus.DONE)

        tasks = task_repo.list_by_filter(status=TaskStatus.DONE)
        assert len(tasks) == 1
        assert tasks[0].id == t2.id

    def test_list_by_filter_due_date_range(self, task_repo):
        """list_by_filter() filters by due date range."""
        now = datetime.now(timezone.utc)
        t1 = task_repo.add("T1")
        t2 = task_repo.add("T2")

        t1.due_date = now - timedelta(days=1)
        t2.due_date = now + timedelta(days=1)
        task_repo._persist()

        # Tasks due in the future
        tasks = task_repo.list_by_filter(due_after=now)
        assert len(tasks) == 1
        assert tasks[0].id == t2.id

    def test_list_by_filter_invalid_date_range_raises(self, task_repo):
        """list_by_filter() raises ValueError if due_after > due_before."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            task_repo.list_by_filter(due_after=now, due_before=now - timedelta(days=1))

    def test_list_by_filter_overdue(self, task_repo):
        """list_by_filter() filters by overdue status."""
        now = datetime.now(timezone.utc)
        t1 = task_repo.add("T1")
        t2 = task_repo.add("T2")

        t1.due_date = now - timedelta(days=1)  # overdue
        t2.due_date = now + timedelta(days=1)  # not overdue
        task_repo._persist()

        overdue = task_repo.list_by_filter(overdue=True)
        assert len(overdue) == 1
        assert overdue[0].id == t1.id

        not_overdue = task_repo.list_by_filter(overdue=False)
        assert len(not_overdue) == 1
        assert not_overdue[0].id == t2.id


class TestTaskRepositoryProjectAssignment:
    """Tests for TaskRepository.assign_to_project() and unassign_from_project()."""

    def test_assign_to_project(self, task_repo):
        """assign_to_project() sets the project_id."""
        task = task_repo.add("Task")
        updated = task_repo.assign_to_project(task.id, "project-123")
        assert updated.project_id == "project-123"

    def test_unassign_from_project(self, task_repo):
        """unassign_from_project() clears the project_id."""
        task = task_repo.add("Task")
        task_repo.assign_to_project(task.id, "project-123")
        updated = task_repo.unassign_from_project(task.id)
        assert updated.project_id is None

    def test_assign_by_prefix(self, task_repo):
        """assign_to_project() supports task ID prefix."""
        task = task_repo.add("Task")
        prefix = task.id[:8]
        updated = task_repo.assign_to_project(prefix, "project-123")
        assert updated.project_id == "project-123"


class TestTaskRepositoryListByProject:
    """Tests for TaskRepository.list_by_project()."""

    def test_list_by_project_empty(self, task_repo):
        """list_by_project() returns empty list when no tasks assigned."""
        tasks = task_repo.list_by_project("project-123")
        assert tasks == []

    def test_list_by_project_returns_assigned(self, task_repo):
        """list_by_project() returns only tasks assigned to given project."""
        t1 = task_repo.add("T1")
        t2 = task_repo.add("T2")
        t3 = task_repo.add("T3")

        task_repo.assign_to_project(t1.id, "proj-A")
        task_repo.assign_to_project(t2.id, "proj-B")
        # t3 not assigned

        tasks = task_repo.list_by_project("proj-A")
        assert len(tasks) == 1
        assert tasks[0].id == t1.id


class TestTaskRepositoryBulkOperations:
    """Tests for TaskRepository.add_many() and replace_all()."""

    def test_add_many_empty_list(self, task_repo):
        """add_many() with empty list returns 0."""
        count = task_repo.add_many([])
        assert count == 0
        assert len(task_repo.list_all()) == 0

    def test_add_many_tasks(self, task_repo):
        """add_many() adds multiple tasks at once."""
        tasks = [Task(title=f"Task{i}") for i in range(3)]
        count = task_repo.add_many(tasks)
        assert count == 3
        assert len(task_repo.list_all()) == 3

    def test_add_many_persists(self, task_repo, tmp_path):
        """add_many() persists to storage."""
        tasks = [Task(title=f"Task{i}") for i in range(3)]
        task_repo.add_many(tasks)

        repo2 = TaskRepository(tmp_path / "tasks.json")
        assert len(repo2.list_all()) == 3

    def test_replace_all_empty(self, task_repo):
        """replace_all() with empty list clears all tasks."""
        task_repo.add("Task1")
        task_repo.add("Task2")
        count = task_repo.replace_all([])
        assert count == 0
        assert len(task_repo.list_all()) == 0

    def test_replace_all_replaces(self, task_repo):
        """replace_all() replaces all existing tasks."""
        task_repo.add("Old1")
        task_repo.add("Old2")

        new_tasks = [Task(title="New1"), Task(title="New2"), Task(title="New3")]
        count = task_repo.replace_all(new_tasks)

        assert count == 3
        all_tasks = task_repo.list_all()
        assert len(all_tasks) == 3
        titles = {t.title for t in all_tasks}
        assert titles == {"New1", "New2", "New3"}


# ===== CommentRepository Tests =====

class TestCommentRepositoryAdd:
    """Tests for CommentRepository.add()."""

    def test_add_comment_basic(self, comment_repo):
        """add() creates a comment with task_id and content."""
        comment = comment_repo.add("task-123", "Great job!")
        assert comment.task_id == "task-123"
        assert comment.content == "Great job!"
        assert comment.author is None

    def test_add_comment_with_author(self, comment_repo):
        """add() supports optional author."""
        comment = comment_repo.add("task-123", "Comment", author="Alice")
        assert comment.author == "Alice"

    def test_add_comment_persists(self, comment_repo, tmp_path):
        """add() writes comment to storage."""
        comment = comment_repo.add("task-123", "Content")
        repo2 = CommentRepository(tmp_path / "comments.json")
        retrieved = repo2.get(comment.id)
        assert retrieved.content == "Content"


class TestCommentRepositoryGet:
    """Tests for CommentRepository.get()."""

    def test_get_exact_id(self, comment_repo):
        """get() retrieves comment by exact ID."""
        comment = comment_repo.add("task-123", "Content")
        retrieved = comment_repo.get(comment.id)
        assert retrieved.id == comment.id

    def test_get_by_prefix(self, comment_repo):
        """get() supports unique prefix matching."""
        comment = comment_repo.add("task-123", "Content")
        prefix = comment.id[:8]
        retrieved = comment_repo.get(prefix)
        assert retrieved.id == comment.id

    def test_get_nonexistent_raises(self, comment_repo):
        """get() raises CommentNotFoundError for missing comment."""
        with pytest.raises(CommentNotFoundError):
            comment_repo.get("nonexistent")


class TestCommentRepositoryListAll:
    """Tests for CommentRepository.list_all()."""

    def test_list_all_empty(self, comment_repo):
        """list_all() returns empty list when no comments exist."""
        assert comment_repo.list_all() == []

    def test_list_all_returns_all(self, comment_repo):
        """list_all() returns all comments."""
        c1 = comment_repo.add("task-1", "Comment1")
        c2 = comment_repo.add("task-2", "Comment2")
        comments = comment_repo.list_all()
        assert len(comments) == 2


class TestCommentRepositoryDelete:
    """Tests for CommentRepository.delete()."""

    def test_delete_comment(self, comment_repo):
        """delete() removes a comment."""
        comment = comment_repo.add("task-123", "Content")
        comment_repo.delete(comment.id)
        assert len(comment_repo.list_all()) == 0

    def test_delete_by_prefix(self, comment_repo):
        """delete() supports prefix matching."""
        comment = comment_repo.add("task-123", "Content")
        prefix = comment.id[:8]
        comment_repo.delete(prefix)
        assert len(comment_repo.list_all()) == 0

    def test_delete_nonexistent_raises(self, comment_repo):
        """delete() raises CommentNotFoundError for missing comment."""
        with pytest.raises(CommentNotFoundError):
            comment_repo.delete("nonexistent")


class TestCommentRepositoryListByTask:
    """Tests for CommentRepository.list_by_task()."""

    def test_list_by_task_empty(self, comment_repo):
        """list_by_task() returns empty list when no comments for task."""
        comments = comment_repo.list_by_task("task-123")
        assert comments == []

    def test_list_by_task_returns_all_for_task(self, comment_repo):
        """list_by_task() returns all comments for a task."""
        c1 = comment_repo.add("task-1", "Comment1")
        c2 = comment_repo.add("task-1", "Comment2")
        c3 = comment_repo.add("task-2", "Comment3")

        comments = comment_repo.list_by_task("task-1")
        assert len(comments) == 2
        ids = {c.id for c in comments}
        assert c1.id in ids and c2.id in ids

    def test_list_by_task_chronological_order(self, comment_repo):
        """list_by_task() returns comments in chronological order (oldest first)."""
        import time
        c1 = comment_repo.add("task-1", "First")
        time.sleep(0.01)
        c2 = comment_repo.add("task-1", "Second")
        time.sleep(0.01)
        c3 = comment_repo.add("task-1", "Third")

        comments = comment_repo.list_by_task("task-1")
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id
        assert comments[2].id == c3.id


class TestCommentRepositoryDeleteAllByTask:
    """Tests for CommentRepository.delete_all_by_task()."""

    def test_delete_all_by_task_empty_task(self, comment_repo):
        """delete_all_by_task() succeeds even if task has no comments."""
        comment_repo.delete_all_by_task("task-123")
        assert len(comment_repo.list_all()) == 0

    def test_delete_all_by_task_removes_all_for_task(self, comment_repo):
        """delete_all_by_task() removes all comments for given task."""
        c1 = comment_repo.add("task-1", "Comment1")
        c2 = comment_repo.add("task-1", "Comment2")
        c3 = comment_repo.add("task-2", "Comment3")

        comment_repo.delete_all_by_task("task-1")

        # Task 1 comments gone
        comments = comment_repo.list_by_task("task-1")
        assert len(comments) == 0

        # Task 2 comment still exists
        comments = comment_repo.list_by_task("task-2")
        assert len(comments) == 1
        assert comments[0].id == c3.id

    def test_delete_all_by_task_persists(self, comment_repo, tmp_path):
        """delete_all_by_task() persists deletion to storage."""
        c1 = comment_repo.add("task-1", "Comment1")
        comment_repo.delete_all_by_task("task-1")

        repo2 = CommentRepository(tmp_path / "comments.json")
        assert len(repo2.list_by_task("task-1")) == 0


class TestCommentRepositoryBulkOperations:
    """Tests for CommentRepository.add_many() and replace_all()."""

    def test_add_many_comments(self, comment_repo):
        """add_many() adds multiple comments at once."""
        comments = [TaskComment(task_id="task-1", content=f"Comment{i}") for i in range(3)]
        count = comment_repo.add_many(comments)
        assert count == 3
        assert len(comment_repo.list_all()) == 3

    def test_replace_all_comments(self, comment_repo):
        """replace_all() replaces all existing comments."""
        comment_repo.add("task-1", "Old1")
        comment_repo.add("task-1", "Old2")

        new_comments = [
            TaskComment(task_id="task-2", content="New1"),
            TaskComment(task_id="task-2", content="New2"),
        ]
        count = comment_repo.replace_all(new_comments)

        assert count == 2
        assert len(comment_repo.list_all()) == 2
        assert len(comment_repo.list_by_task("task-1")) == 0
        assert len(comment_repo.list_by_task("task-2")) == 2


# ===== ProjectRepository Tests =====

class TestProjectRepositoryAdd:
    """Tests for ProjectRepository.add()."""

    def test_add_project(self, project_repo):
        """add() creates a project with name."""
        project = project_repo.add("My Project")
        assert project.name == "My Project"
        assert project.id is not None

    def test_add_project_persists(self, project_repo, tmp_path):
        """add() persists to storage."""
        project = project_repo.add("My Project")
        repo2 = ProjectRepository(tmp_path / "projects.json")
        retrieved = repo2.get(project.id)
        assert retrieved.name == "My Project"


class TestProjectRepositoryGet:
    """Tests for ProjectRepository.get()."""

    def test_get_exact_id(self, project_repo):
        """get() retrieves project by exact ID."""
        project = project_repo.add("Project")
        retrieved = project_repo.get(project.id)
        assert retrieved.id == project.id

    def test_get_by_prefix(self, project_repo):
        """get() supports unique prefix matching."""
        project = project_repo.add("Project")
        prefix = project.id[:8]
        retrieved = project_repo.get(prefix)
        assert retrieved.id == project.id

    def test_get_nonexistent_raises(self, project_repo):
        """get() raises ProjectNotFoundError for missing project."""
        with pytest.raises(ProjectNotFoundError):
            project_repo.get("nonexistent")


class TestProjectRepositoryListAll:
    """Tests for ProjectRepository.list_all()."""

    def test_list_all_empty(self, project_repo):
        """list_all() returns empty list when no projects exist."""
        assert project_repo.list_all() == []

    def test_list_all_returns_all(self, project_repo):
        """list_all() returns all projects."""
        p1 = project_repo.add("Project1")
        p2 = project_repo.add("Project2")
        projects = project_repo.list_all()
        assert len(projects) == 2


class TestProjectRepositoryDelete:
    """Tests for ProjectRepository.delete()."""

    def test_delete_project(self, project_repo):
        """delete() removes a project."""
        project = project_repo.add("Project")
        project_repo.delete(project.id)
        assert len(project_repo.list_all()) == 0

    def test_delete_nonexistent_raises(self, project_repo):
        """delete() raises ProjectNotFoundError for missing project."""
        with pytest.raises(ProjectNotFoundError):
            project_repo.delete("nonexistent")


class TestProjectRepositoryUpdate:
    """Tests for ProjectRepository.update()."""

    def test_update_name(self, project_repo):
        """update() changes project name."""
        project = project_repo.add("Old Name")
        updated = project_repo.update(project.id, "New Name")
        assert updated.name == "New Name"

    def test_update_by_prefix(self, project_repo):
        """update() supports ID prefix matching."""
        project = project_repo.add("Old Name")
        prefix = project.id[:8]
        updated = project_repo.update(prefix, "New Name")
        assert updated.name == "New Name"

    def test_update_nonexistent_raises(self, project_repo):
        """update() raises ProjectNotFoundError for missing project."""
        with pytest.raises(ProjectNotFoundError):
            project_repo.update("nonexistent", "Name")


class TestProjectRepositoryBulkOperations:
    """Tests for ProjectRepository.add_many() and replace_all()."""

    def test_add_many_projects(self, project_repo):
        """add_many() adds multiple projects at once."""
        projects = [Project(name=f"Project{i}") for i in range(3)]
        count = project_repo.add_many(projects)
        assert count == 3
        assert len(project_repo.list_all()) == 3

    def test_replace_all_projects(self, project_repo):
        """replace_all() replaces all projects."""
        project_repo.add("Old1")
        project_repo.add("Old2")

        new_projects = [Project(name="New1"), Project(name="New2")]
        count = project_repo.replace_all(new_projects)

        assert count == 2
        assert len(project_repo.list_all()) == 2
        names = {p.name for p in project_repo.list_all()}
        assert names == {"New1", "New2"}
