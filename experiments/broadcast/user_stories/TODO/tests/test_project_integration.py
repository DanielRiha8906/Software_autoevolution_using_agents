import pytest
import tempfile
from pathlib import Path

from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


def test_create_task_without_project():
    """Test that tasks can be created without a project (backward compatibility)."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        task = service.add_task("Buy milk")
        assert task.project_id is None
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_create_project_and_assign_task():
    """Test creating a project and assigning a task to it."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Create project and task
        project = service.create_project("Work")
        task = service.add_task("Finish report")
        
        # Assign task to project
        assigned = service.assign_task_to_project(task.id, project.id)
        assert assigned.project_id == project.id
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_list_tasks_by_project():
    """Test listing tasks in a specific project."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Create project and tasks
        project = service.create_project("Work")
        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2")
        task3 = service.add_task("Task 3")
        
        # Assign some tasks
        service.assign_task_to_project(task1.id, project.id)
        service.assign_task_to_project(task2.id, project.id)
        
        # List tasks in project
        tasks = service.list_tasks_by_project(project.id)
        assert len(tasks) == 2
        assert any(t.id == task1.id for t in tasks)
        assert any(t.id == task2.id for t in tasks)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_list_unassigned_tasks():
    """Test listing tasks not in any project."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Create project and tasks
        project = service.create_project("Work")
        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2")
        task3 = service.add_task("Task 3")
        
        # Assign some tasks
        service.assign_task_to_project(task1.id, project.id)
        
        # List unassigned
        unassigned = service.list_unassigned_tasks()
        assert len(unassigned) == 2
        assert any(t.id == task2.id for t in unassigned)
        assert any(t.id == task3.id for t in unassigned)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_unassign_task_from_project():
    """Test removing a task from a project."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Create project and task
        project = service.create_project("Work")
        task = service.add_task("Task")
        service.assign_task_to_project(task.id, project.id)
        
        # Unassign
        unassigned = service.unassign_task_from_project(task.id)
        assert unassigned.project_id is None
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_move_task_between_projects():
    """Test moving a task from one project to another."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Create projects and task
        project1 = service.create_project("Work")
        project2 = service.create_project("Personal")
        task = service.add_task("Task")
        
        # Assign to first project
        service.assign_task_to_project(task.id, project1.id)
        tasks_in_p1 = service.list_tasks_by_project(project1.id)
        assert len(tasks_in_p1) == 1
        
        # Move to second project
        service.assign_task_to_project(task.id, project2.id)
        tasks_in_p1 = service.list_tasks_by_project(project1.id)
        tasks_in_p2 = service.list_tasks_by_project(project2.id)
        assert len(tasks_in_p1) == 0
        assert len(tasks_in_p2) == 1
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_delete_project_keeps_tasks():
    """Test that deleting a project doesn't delete its tasks."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Create project and task
        project = service.create_project("Work")
        task = service.add_task("Task")
        service.assign_task_to_project(task.id, project.id)
        
        # Delete project
        service.delete_project(project.id)
        
        # Task should still exist but be unassigned
        retrieved_task = service.get_task(task.id)
        assert retrieved_task.project_id is None
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_backward_compatibility_old_tasks_without_project():
    """Test that tasks stored without project_id load correctly."""
    import json
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
        # Write old format data without project_id
        old_data = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Old task",
                    "description": None,
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    # Note: no project_id field
                }
            ],
            "comments": [],
            "projects": []
        }
        json.dump(old_data, f)
    
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        # Should load without error
        tasks = service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Old task"
        assert tasks[0].project_id is None
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_project_names_cannot_be_empty():
    """Test that empty project names are rejected."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    try:
        storage = JsonStorage(temp_path)
        service = TodoService(storage)
        
        with pytest.raises(ValueError):
            service.create_project("")
    finally:
        Path(temp_path).unlink(missing_ok=True)
