import pytest
from src.models.task_comment import TaskComment
from src.services.comments_service import CommentsService
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def services(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    todo = TodoService(storage)
    task = todo.add_task("Test task")
    return task, CommentsService(todo)


def test_add_comment(services):
    task, svc = services
    comment = svc.add_comment(task.id, "First comment")
    assert comment.content == "First comment"
    assert comment.task_id == task.id


def test_add_empty_comment_raises(services):
    task, svc = services
    with pytest.raises(Exception):
        svc.add_comment(task.id, "")


def test_comments_service_does_not_contain_file_io():
    import inspect
    from src.services import comments_service as mod
    source = inspect.getsource(mod)
    assert "open(" not in source
    assert "json.dump" not in source


def test_list_comments_ordered_by_created_at(services):
    task, svc = services
    svc.add_comment(task.id, "First")
    svc.add_comment(task.id, "Second")
    comments = svc.list_comments(task.id)
    assert comments[0].content == "First"
    assert comments[1].content == "Second"


def test_delete_comment(services):
    task, svc = services
    comment = svc.add_comment(task.id, "To delete")
    svc.delete_comment(comment.id)
    assert all(c.id != comment.id for c in svc.list_comments(task.id))


def test_add_comment_to_nonexistent_task_raises(tmp_path):
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    svc = CommentsService(todo)
    with pytest.raises(Exception):
        svc.add_comment("nonexistent-id", "Hi")


def test_delete_task_cascades_to_comments(services):
    task, svc = services
    svc.add_comment(task.id, "Should be removed")
    svc.delete_comments_for_task(task.id)
    assert svc.list_comments(task.id) == []
