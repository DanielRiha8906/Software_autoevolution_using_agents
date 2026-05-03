import json
import pytest
from src.models.task import Task
from src.services.todo_service import TodoService
from src.services.comments_service import CommentsService
from src.services.import_export_service import TaskImportExportService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def setup(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    todo = TodoService(storage)
    comments = CommentsService(todo)
    task = todo.add_task("Task one")
    comments.add_comment(task.id, "A comment")
    return TaskImportExportService(todo, comments), todo, comments, task, tmp_path


def test_export_creates_json_file(setup):
    svc, _, _, _, tmp_path = setup
    path = tmp_path / "export.json"
    svc.export(str(path))
    assert path.exists()


def test_export_contains_tasks_and_comments(setup):
    svc, _, _, task, tmp_path = setup
    path = tmp_path / "export.json"
    svc.export(str(path))
    data = json.loads(path.read_text())
    assert any(t["id"] == task.id for t in data["tasks"])
    assert any(c["task_id"] == task.id for c in data["comments"])


def test_import_restores_tasks(setup, tmp_path):
    svc, todo, comments, task, tmp_path = setup
    path = tmp_path / "export.json"
    svc.export(str(path))
    todo2 = TodoService(JsonStorage(str(tmp_path / "tasks2.json")))
    svc2 = TaskImportExportService(todo2, CommentsService(todo2))
    svc2.import_from(str(path))
    assert any(t.id == task.id for t in todo2.list_tasks())


def test_import_validates_structure(tmp_path):
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    svc = TaskImportExportService(todo, CommentsService(todo))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"garbage": True}))
    with pytest.raises(Exception):
        svc.import_from(str(bad))

def test_import_restores_comments(setup, tmp_path):
    svc, todo, comments, task, tmp_path = setup
    path = tmp_path / "export.json"
    svc.export(str(path))

    todo2 = TodoService(JsonStorage(str(tmp_path / "tasks2.json")))
    comments2 = CommentsService(todo2)
    svc2 = TaskImportExportService(todo2, comments2)

    svc2.import_from(str(path))

    restored_comments = comments2.list_comments(task.id)
    assert any(c.content == "A comment" for c in restored_comments)

def test_import_skips_duplicates(setup, tmp_path):
    svc, todo, _, task, tmp_path = setup
    path = tmp_path / "export.json"
    svc.export(str(path))
    svc.import_from(str(path))
    assert len([t for t in todo.list_tasks() if t.id == task.id]) == 1
