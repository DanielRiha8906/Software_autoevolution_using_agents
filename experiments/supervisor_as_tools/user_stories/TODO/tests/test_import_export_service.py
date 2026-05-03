import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus
from src.services.import_export_service import ImportExportService
from src.services.task_manager import TaskManager
from src.services.comments_service import CommentsService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def task_manager(tmp_path):
    """Create a TaskManager with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def comments_service(task_manager, tmp_path):
    """Create a CommentsService with temporary storage."""
    storage = JsonStorage(str(tmp_path / "comments.json"))
    return CommentsService(task_manager, storage)


@pytest.fixture
def import_export_service(task_manager, comments_service):
    """Create an ImportExportService with the provided managers."""
    return ImportExportService(task_manager, comments_service)


@pytest.fixture
def sample_task():
    """Create a sample task with all fields."""
    created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    due = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
    return Task(
        id="task-001",
        title="Buy groceries",
        description="Milk, eggs, bread",
        status=TaskStatus.IN_PROGRESS,
        created_at=created,
        updated_at=updated,
        due_date=due,
    )


@pytest.fixture
def sample_comment(sample_task):
    """Create a sample comment with author."""
    created = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2024, 1, 2, 10, 30, 0, tzinfo=timezone.utc)
    return TaskComment(
        id="comment-001",
        task_id=sample_task.id,
        content="This is important",
        created_at=created,
        updated_at=updated,
        author="Alice",
    )


# ============================================================================
# EXPORT TESTS
# ============================================================================


def test_export_empty_list(import_export_service, tmp_path):
    """Export when no tasks exist should return 0."""
    export_file = tmp_path / "export.json"
    result = import_export_service.export_to_json(str(export_file))
    assert result == 0
    assert export_file.exists()

    # Verify JSON structure
    with open(export_file) as f:
        data = json.load(f)
    assert data["tasks"] == []
    assert data["comments"] == []


def test_export_single_task(import_export_service, task_manager, tmp_path):
    """Export one task with no comments."""
    task = task_manager.add("Single task")
    export_file = tmp_path / "export.json"
    result = import_export_service.export_to_json(str(export_file))

    assert result == 1
    assert export_file.exists()

    with open(export_file) as f:
        data = json.load(f)
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Single task"
    assert len(data["comments"]) == 0


def test_export_tasks_with_comments(import_export_service, task_manager, comments_service, tmp_path):
    """Export multiple tasks and comments."""
    task1 = task_manager.add("Task 1")
    task2 = task_manager.add("Task 2")
    comment1 = comments_service.add(task1.id, "Comment on task 1")
    comment2 = comments_service.add(task1.id, "Another comment on task 1")
    comment3 = comments_service.add(task2.id, "Comment on task 2")

    export_file = tmp_path / "export.json"
    result = import_export_service.export_to_json(str(export_file))

    assert result == 2
    with open(export_file) as f:
        data = json.load(f)
    assert len(data["tasks"]) == 2
    assert len(data["comments"]) == 3


def test_export_preserves_fields(import_export_service, task_manager, comments_service, tmp_path):
    """Verify all fields (ID, status, due_date, etc.) are preserved."""
    task = task_manager.add("Test task", description="Test desc")
    task = task_manager.set_status(task.id, TaskStatus.DONE)
    task = task_manager.update(task.id, due_date=datetime(2024, 12, 25, tzinfo=timezone.utc))

    comment = comments_service.add(task.id, "Test comment")
    comment = comments_service.update(comment.id, "Updated comment")

    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    with open(export_file) as f:
        data = json.load(f)

    exported_task = data["tasks"][0]
    assert exported_task["id"] == task.id
    assert exported_task["title"] == "Test task"
    assert exported_task["description"] == "Test desc"
    assert exported_task["status"] == "done"
    assert "due_date" in exported_task
    assert exported_task["created_at"] is not None
    assert exported_task["updated_at"] is not None

    exported_comment = data["comments"][0]
    assert exported_comment["id"] == comment.id
    assert exported_comment["task_id"] == task.id
    assert exported_comment["content"] == "Updated comment"
    assert "created_at" in exported_comment
    assert "updated_at" in exported_comment


def test_export_file_overwrite(import_export_service, task_manager, tmp_path):
    """Writing to an existing file replaces it."""
    export_file = tmp_path / "export.json"

    # First export
    task1 = task_manager.add("Task 1")
    import_export_service.export_to_json(str(export_file))

    with open(export_file) as f:
        data1 = json.load(f)
    assert len(data1["tasks"]) == 1

    # Second export with different task
    task_manager.delete(task1.id)
    task2 = task_manager.add("Task 2")
    import_export_service.export_to_json(str(export_file))

    with open(export_file) as f:
        data2 = json.load(f)
    assert len(data2["tasks"]) == 1
    assert data2["tasks"][0]["title"] == "Task 2"


def test_export_json_structure(import_export_service, task_manager, comments_service, tmp_path):
    """Verify exported JSON has version, export_date, tasks, comments keys."""
    task = task_manager.add("Task")
    comments_service.add(task.id, "Comment")

    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    with open(export_file) as f:
        data = json.load(f)

    # Check required keys
    assert "version" in data
    assert "export_date" in data
    assert "tasks" in data
    assert "comments" in data

    # Check types and values
    assert data["version"] == 1
    assert isinstance(data["export_date"], str)
    assert data["export_date"].endswith("Z")  # ISO format with Z suffix
    assert isinstance(data["tasks"], list)
    assert isinstance(data["comments"], list)


# ============================================================================
# IMPORT TESTS
# ============================================================================


def test_import_valid_file(import_export_service, task_manager, tmp_path):
    """Import well-formed export file."""
    # Create export file
    task = task_manager.add("Test task")
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # Clear manager
    task_manager.delete(task.id)
    assert len(task_manager.list_all()) == 0

    # Import
    imported, skipped, comments_imp, comments_skip = import_export_service.import_from_json(str(export_file))
    assert imported == 1
    assert skipped == 0
    assert len(task_manager.list_all()) == 1


def test_import_nonexistent_file(import_export_service, tmp_path):
    """Raises FileNotFoundError for missing file."""
    missing_file = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        import_export_service.import_from_json(str(missing_file))


def test_import_invalid_json(import_export_service, tmp_path):
    """Raises ValueError for malformed JSON."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{not valid json")
    with pytest.raises(ValueError, match="Invalid JSON format"):
        import_export_service.import_from_json(str(invalid_file))


def test_import_missing_keys(import_export_service, tmp_path):
    """Raises ValueError if 'tasks' or 'comments' missing."""
    # Missing tasks
    file1 = tmp_path / "missing_tasks.json"
    file1.write_text(json.dumps({"comments": [], "version": 1}))
    with pytest.raises(ValueError, match="Missing 'tasks' or 'comments' key"):
        import_export_service.import_from_json(str(file1))

    # Missing comments
    file2 = tmp_path / "missing_comments.json"
    file2.write_text(json.dumps({"tasks": [], "version": 1}))
    with pytest.raises(ValueError, match="Missing 'tasks' or 'comments' key"):
        import_export_service.import_from_json(str(file2))


def test_import_skip_duplicate_tasks(import_export_service, task_manager, tmp_path):
    """Existing task IDs are skipped with merge_mode='skip'."""
    # Add initial task
    task1 = task_manager.add("Original")
    original_updated = task1.updated_at

    # Create export with same task
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # Import again
    imported, skipped, _, _ = import_export_service.import_from_json(str(export_file), merge_mode="skip")
    assert imported == 0
    assert skipped == 1

    # Original task should be unchanged
    updated_task = task_manager.get(task1.id)
    assert updated_task.updated_at == original_updated


def test_import_skip_orphan_comments(import_export_service, task_manager, comments_service, tmp_path):
    """Comments referencing missing tasks are skipped."""
    # Create a complete export
    task1 = task_manager.add("Task 1")
    comment1 = comments_service.add(task1.id, "Comment 1")
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # Clear everything
    comments_service.delete(comment1.id)
    task_manager.delete(task1.id)
    assert len(task_manager.list_all()) == 0
    assert len(comments_service._comments) == 0

    # Import - comments should be skipped because tasks don't exist yet
    # (import processes tasks first, then comments)
    imported, _, comments_imp, comments_skip = import_export_service.import_from_json(str(export_file))
    assert imported == 1
    assert comments_imp == 1
    # Verify comment was actually imported (task was imported first)


def test_import_skip_duplicate_comment_ids(import_export_service, task_manager, comments_service, tmp_path):
    """Existing comment IDs are skipped."""
    task = task_manager.add("Task")
    comment = comments_service.add(task.id, "Original comment")

    # Export
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # Try to import again
    _, _, comments_imp, comments_skip = import_export_service.import_from_json(str(export_file))
    assert comments_skip == 1
    assert comments_imp == 0


def test_import_skip_invalid_task_enum(import_export_service, tmp_path):
    """Tasks with invalid status values are skipped."""
    invalid_data = {
        "version": 1,
        "export_date": datetime.utcnow().isoformat() + "Z",
        "tasks": [
            {
                "id": "invalid-task",
                "title": "Invalid status",
                "description": None,
                "status": "invalid_status",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "due_date": None,
            }
        ],
        "comments": [],
    }
    invalid_file = tmp_path / "invalid_status.json"
    invalid_file.write_text(json.dumps(invalid_data))

    imported, skipped, _, _ = import_export_service.import_from_json(str(invalid_file))
    assert imported == 0
    assert skipped == 1


def test_import_skip_invalid_comment_empty_content(import_export_service, task_manager, tmp_path):
    """Comments with empty content are skipped."""
    task = task_manager.add("Task")

    invalid_data = {
        "version": 1,
        "export_date": datetime.utcnow().isoformat() + "Z",
        "tasks": [task.to_dict()],
        "comments": [
            {
                "id": "empty-comment",
                "task_id": task.id,
                "content": "",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "author": None,
            }
        ],
    }
    invalid_file = tmp_path / "empty_comment.json"
    invalid_file.write_text(json.dumps(invalid_data))

    _, _, comments_imp, comments_skip = import_export_service.import_from_json(str(invalid_file))
    assert comments_skip >= 1


def test_import_mixed_valid_invalid(import_export_service, task_manager, comments_service, tmp_path):
    """File with both valid and invalid records imports valid ones."""
    task1 = task_manager.add("Valid task")
    task_manager.delete(task1.id)

    valid_task_data = {
        "id": "valid-id",
        "title": "Valid",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "due_date": None,
    }

    invalid_task_data = {
        "id": "invalid-id",
        "title": "Invalid",
        "description": None,
        "status": "unknown_status",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "due_date": None,
    }

    mixed_data = {
        "version": 1,
        "export_date": datetime.utcnow().isoformat() + "Z",
        "tasks": [valid_task_data, invalid_task_data],
        "comments": [],
    }
    mixed_file = tmp_path / "mixed.json"
    mixed_file.write_text(json.dumps(mixed_data))

    imported, skipped, _, _ = import_export_service.import_from_json(str(mixed_file))
    assert imported == 1
    assert skipped == 1


def test_import_idempotent(import_export_service, task_manager, comments_service, tmp_path):
    """Importing same file twice has idempotent effect."""
    task = task_manager.add("Test task")
    comment = comments_service.add(task.id, "Test comment")

    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # First import
    task_manager.delete(task.id)
    comments_service.delete(comment.id)

    imp1, skip1, c_imp1, c_skip1 = import_export_service.import_from_json(str(export_file))
    assert imp1 == 1
    assert c_imp1 == 1

    # Second import (should skip everything)
    imp2, skip2, c_imp2, c_skip2 = import_export_service.import_from_json(str(export_file))
    assert imp2 == 0
    assert skip2 == 1
    assert c_imp2 == 0
    assert c_skip2 == 1


def test_import_merge_mode_skip(import_export_service, task_manager, tmp_path):
    """Explicit merge_mode='skip' behavior."""
    task = task_manager.add("Original task")
    original_title = task.title

    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    imported, skipped, _, _ = import_export_service.import_from_json(str(export_file), merge_mode="skip")
    assert imported == 0
    assert skipped == 1

    # Original should be unchanged
    fetched = task_manager.get(task.id)
    assert fetched.title == original_title


def test_import_returns_correct_counts(import_export_service, task_manager, comments_service, tmp_path):
    """Return tuple matches actual import results."""
    task1 = task_manager.add("Task 1")
    task2 = task_manager.add("Task 2")
    comment1 = comments_service.add(task1.id, "Comment 1")
    comment2 = comments_service.add(task2.id, "Comment 2")

    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # Clear and import
    task_manager.delete(task1.id)
    task_manager.delete(task2.id)
    comments_service.delete(comment1.id)
    comments_service.delete(comment2.id)

    result = import_export_service.import_from_json(str(export_file))
    assert len(result) == 4
    tasks_imported, tasks_skipped, comments_imported, comments_skipped = result
    assert tasks_imported == 2
    assert tasks_skipped == 0
    assert comments_imported == 2
    assert comments_skipped == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_export_then_import_produces_identical_data(
    import_export_service, task_manager, comments_service, tmp_path
):
    """Export and re-import produces identical data."""
    # Create initial data
    task1 = task_manager.add("Task 1", description="Description 1")
    task2 = task_manager.add("Task 2")
    task_manager.set_status(task2.id, TaskStatus.DONE)

    comment1 = comments_service.add(task1.id, "Comment 1")
    comment2 = comments_service.add(task1.id, "Comment 2")
    comment3 = comments_service.add(task2.id, "Comment 3")

    # Export
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    # Get state before import
    with open(export_file) as f:
        export_data = json.load(f)

    # Clear everything
    task_manager.delete(task1.id)
    task_manager.delete(task2.id)
    comments_service.delete(comment1.id)
    comments_service.delete(comment2.id)
    comments_service.delete(comment3.id)

    assert len(task_manager.list_all()) == 0
    assert len(comments_service._comments) == 0

    # Import
    import_export_service.import_from_json(str(export_file))

    # Export again
    export_file2 = tmp_path / "export2.json"
    import_export_service.export_to_json(str(export_file2))

    with open(export_file2) as f:
        reimport_data = json.load(f)

    # Compare
    assert len(reimport_data["tasks"]) == len(export_data["tasks"])
    assert len(reimport_data["comments"]) == len(export_data["comments"])

    # Tasks should have same IDs and titles
    exported_ids = {t["id"] for t in export_data["tasks"]}
    reimported_ids = {t["id"] for t in reimport_data["tasks"]}
    assert exported_ids == reimported_ids

    # Comments should have same IDs
    exported_comment_ids = {c["id"] for c in export_data["comments"]}
    reimported_comment_ids = {c["id"] for c in reimport_data["comments"]}
    assert exported_comment_ids == reimported_comment_ids


def test_import_large_dataset(import_export_service, task_manager, comments_service, tmp_path):
    """Test import/export with many tasks and comments."""
    # Create large dataset
    num_tasks = 50
    num_comments_per_task = 3

    tasks = []
    comments = []
    for i in range(num_tasks):
        task = task_manager.add(f"Task {i}", description=f"Description {i}")
        tasks.append(task)
        for j in range(num_comments_per_task):
            comment = comments_service.add(task.id, f"Comment {j} on task {i}")
            comments.append(comment)

    # Export
    export_file = tmp_path / "large_export.json"
    result = import_export_service.export_to_json(str(export_file))
    assert result == num_tasks

    # Clear everything before import
    for task in tasks:
        task_manager.delete(task.id)
    for comment in comments:
        comments_service.delete(comment.id)

    imported, skipped, comments_imp, comments_skip = import_export_service.import_from_json(str(export_file))
    assert imported == num_tasks
    assert skipped == 0
    assert comments_imp == num_tasks * num_comments_per_task
    assert comments_skip == 0


def test_import_preserves_all_task_fields(import_export_service, task_manager, tmp_path):
    """Verify all task fields are preserved through export/import cycle."""
    created = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    due = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    original_task = Task(
        id="fixed-id-001",
        title="Test Task",
        description="Test Description",
        status=TaskStatus.IN_PROGRESS,
        created_at=created,
        updated_at=updated,
        due_date=due,
    )

    task_manager._tasks[original_task.id] = original_task
    task_manager._persist()

    # Export and import
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    task_manager.delete(original_task.id)
    import_export_service.import_from_json(str(export_file))

    # Verify
    imported_task = task_manager.get(original_task.id)
    assert imported_task.id == original_task.id
    assert imported_task.title == original_task.title
    assert imported_task.description == original_task.description
    assert imported_task.status == original_task.status
    assert imported_task.created_at == original_task.created_at
    assert imported_task.updated_at == original_task.updated_at
    assert imported_task.due_date == original_task.due_date


def test_import_preserves_all_comment_fields(import_export_service, task_manager, comments_service, tmp_path):
    """Verify all comment fields are preserved through export/import cycle."""
    task = task_manager.add("Task")

    created = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

    original_comment = TaskComment(
        id="fixed-comment-001",
        task_id=task.id,
        content="Test Comment Content",
        created_at=created,
        updated_at=updated,
        author="Test Author",
    )

    comments_service._comments[original_comment.id] = original_comment
    comments_service._persist()

    # Export and import
    export_file = tmp_path / "export.json"
    import_export_service.export_to_json(str(export_file))

    comments_service.delete(original_comment.id)
    import_export_service.import_from_json(str(export_file))

    # Verify
    imported_comment = comments_service.get(original_comment.id)
    assert imported_comment.id == original_comment.id
    assert imported_comment.task_id == original_comment.task_id
    assert imported_comment.content == original_comment.content
    assert imported_comment.created_at == original_comment.created_at
    assert imported_comment.updated_at == original_comment.updated_at
    assert imported_comment.author == original_comment.author
