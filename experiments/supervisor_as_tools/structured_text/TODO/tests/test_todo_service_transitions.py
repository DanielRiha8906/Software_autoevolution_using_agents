import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


class TestServiceTransitionsWithTaskMethods:
    def test_service_start_updates_task_via_manager(self, service):
        """Verify that service.start_task works with TaskManager.set_status."""
        task = service.add_task("Start me")
        assert task.status == TaskStatus.PENDING

        started = service.start_task(task.id)
        assert started.status == TaskStatus.IN_PROGRESS

    def test_service_complete_updates_task_via_manager(self, service):
        """Verify that service.complete_task works with TaskManager.set_status."""
        task = service.add_task("Complete me")
        completed = service.complete_task(task.id)
        assert completed.status == TaskStatus.DONE

    def test_service_reopen_updates_task_via_manager(self, service):
        """Verify that service.reopen_task works with TaskManager.set_status."""
        task = service.add_task("Reopen me")
        service.complete_task(task.id)
        reopened = service.reopen_task(task.id)
        assert reopened.status == TaskStatus.PENDING

    def test_service_transitions_persist_to_storage(self, service, tmp_path):
        """Verify that status transitions are persisted to storage."""
        task = service.add_task("Persistent task")
        original_id = task.id

        # Transition
        service.start_task(task.id)
        service.complete_task(task.id)

        # Reload from storage
        new_service = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
        reloaded = new_service.get_task(original_id)
        assert reloaded.status == TaskStatus.DONE

    def test_service_updated_at_changes_on_transition(self, service):
        """Verify that service transitions update the updated_at field."""
        task = service.add_task("Update me")
        original_updated_at = task.updated_at

        # Small delay to ensure time advances
        started = service.start_task(task.id)
        assert started.updated_at >= original_updated_at

    def test_service_multiple_transitions_workflow(self, service):
        """Test a complete workflow through the service."""
        task = service.add_task("Full workflow")
        assert task.status == TaskStatus.PENDING

        task = service.start_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

        task = service.complete_task(task.id)
        assert task.status == TaskStatus.DONE

        task = service.reopen_task(task.id)
        assert task.status == TaskStatus.PENDING


class TestServiceWithIsCompletedMethod:
    def test_service_task_is_completed_after_complete_task(self, service):
        """Verify that is_completed() returns True after service.complete_task()."""
        task = service.add_task("Check completed")
        assert task.is_completed() is False

        completed = service.complete_task(task.id)
        assert completed.is_completed() is True

    def test_service_task_not_completed_after_start_task(self, service):
        """Verify that is_completed() returns False after service.start_task()."""
        task = service.add_task("Check in progress")
        started = service.start_task(task.id)
        assert started.is_completed() is False

    def test_service_task_not_completed_when_pending(self, service):
        """Verify that is_completed() returns False for pending tasks."""
        task = service.add_task("Check pending")
        assert task.is_completed() is False

    def test_service_task_not_completed_after_reopen(self, service):
        """Verify that is_completed() returns False after service.reopen_task()."""
        task = service.add_task("Check reopened")
        service.complete_task(task.id)
        reopened = service.reopen_task(task.id)
        assert reopened.is_completed() is False


class TestServiceTransitionsWithDueDate:
    def test_completed_task_still_checks_overdue_status(self, service):
        """Verify that completed tasks can still be overdue based on due_date."""
        # Create a task with a future due date
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        task = service.add_task("Future task")
        task_with_date = service.set_due_date(task.id, future)
        assert task_with_date.is_overdue() is False

        # Complete the task
        completed = service.complete_task(task.id)
        assert completed.is_completed() is True
        # is_overdue() should still work on completed tasks with future due_date
        reloaded = service.get_task(completed.id)
        assert reloaded.is_completed() is True
        assert reloaded.is_overdue() is False  # Still not overdue because due_date is in future

    def test_transition_updates_updated_at_not_due_date(self, service):
        """Verify that mark_done doesn't change the due_date."""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        task = service.add_task("Keep date")
        task_with_date = service.set_due_date(task.id, future)
        original_due_date = task_with_date.due_date

        completed = service.complete_task(task.id)
        assert completed.due_date == original_due_date


class TestServiceListFiltering:
    def test_list_by_completed_status_after_transitions(self, service):
        """Verify that listing by DONE status shows transitioned tasks."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")
        t3 = service.add_task("Task 3")

        service.complete_task(t1.id)
        service.complete_task(t3.id)

        done_tasks = service.list_tasks(TaskStatus.DONE)
        assert len(done_tasks) == 2
        assert t1.id in [t.id for t in done_tasks]
        assert t3.id in [t.id for t in done_tasks]
        assert t2.id not in [t.id for t in done_tasks]

    def test_list_by_in_progress_status_after_transitions(self, service):
        """Verify that listing by IN_PROGRESS status shows transitioned tasks."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")
        t3 = service.add_task("Task 3")

        service.start_task(t1.id)
        service.start_task(t3.id)
        service.complete_task(t3.id)

        in_progress_tasks = service.list_tasks(TaskStatus.IN_PROGRESS)
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0].id == t1.id

    def test_list_by_pending_after_transitions(self, service):
        """Verify that listing by PENDING status shows reopened and new tasks."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")
        t3 = service.add_task("Task 3")

        service.complete_task(t1.id)
        service.reopen_task(t1.id)
        service.start_task(t2.id)

        pending_tasks = service.list_tasks(TaskStatus.PENDING)
        pending_ids = [t.id for t in pending_tasks]
        assert t1.id in pending_ids  # reopened
        assert t3.id in pending_ids  # never transitioned
        assert t2.id not in pending_ids  # in progress


class TestServiceConcurrentOperations:
    def test_rapid_transitions_on_same_task(self, service):
        """Verify that rapid status transitions work correctly."""
        task = service.add_task("Rapid")
        assert task.status == TaskStatus.PENDING

        task = service.start_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

        task = service.complete_task(task.id)
        assert task.status == TaskStatus.DONE

        task = service.reopen_task(task.id)
        assert task.status == TaskStatus.PENDING

        task = service.start_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

    def test_multiple_tasks_different_transitions(self, service):
        """Verify that multiple tasks can have independent transitions."""
        t1 = service.add_task("One")
        t2 = service.add_task("Two")
        t3 = service.add_task("Three")

        service.complete_task(t1.id)
        service.start_task(t2.id)
        # t3 stays pending

        t1_final = service.get_task(t1.id)
        t2_final = service.get_task(t2.id)
        t3_final = service.get_task(t3.id)

        assert t1_final.status == TaskStatus.DONE
        assert t2_final.status == TaskStatus.IN_PROGRESS
        assert t3_final.status == TaskStatus.PENDING
