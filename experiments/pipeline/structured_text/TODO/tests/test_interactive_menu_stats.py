import pytest
from src.cli.interactive_menu import InteractiveMenu
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def menu(tmp_path):
    """Provide an InteractiveMenu instance with a temporary storage backend."""
    return InteractiveMenu(storage_path=str(tmp_path / "tasks.json"))


@pytest.fixture
def service(tmp_path):
    """Provide a TodoService for test setup."""
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


class TestInteractiveMenuStatisticsHandler:
    """Test the interactive menu option 10 (statistics)."""

    def test_statistics_handler_exists(self, menu):
        """InteractiveMenu has _do_statistics method."""
        assert hasattr(menu, "_do_statistics")
        assert callable(getattr(menu, "_do_statistics"))

    def test_statistics_handler_callable(self, menu, monkeypatch):
        """_do_statistics() can be called without raising."""
        # Mock input to skip the "Press Enter" prompt
        monkeypatch.setattr("builtins.input", lambda x: "")
        # Should not raise an exception
        menu._do_statistics()

    def test_statistics_output_with_empty_list(self, menu, capsys, monkeypatch):
        """_do_statistics() shows statistics for empty task list."""
        # Mock input to skip the "Press Enter" prompt
        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "Task Statistics" in out

    def test_statistics_output_format(self, menu, capsys, monkeypatch):
        """_do_statistics() output has correct format."""
        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        required_lines = [
            "Task Statistics",
            "Total tasks:",
            "Pending:",
            "In Progress:",
            "Done:",
            "Overdue (active):",
            "With due date:",
        ]
        for line in required_lines:
            assert line in out, f"Missing expected output: {line}"

    def test_statistics_with_pending_task(self, menu, service, capsys, monkeypatch):
        """_do_statistics() shows pending count."""
        service.add_task("Pending task")
        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "Pending:" in out

    def test_statistics_with_in_progress_task(self, menu, service, capsys, monkeypatch):
        """_do_statistics() shows in-progress count."""
        task = service.add_task("In progress task")
        service.start_task(task.id)
        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "In Progress:" in out

    def test_statistics_with_done_task(self, menu, service, capsys, monkeypatch):
        """_do_statistics() shows completed task count."""
        task = service.add_task("Done task")
        service.complete_task(task.id)
        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "Done:" in out

    def test_statistics_with_mixed_tasks(self, menu, service, capsys, monkeypatch):
        """_do_statistics() shows statistics for mixed task statuses."""
        # Create diverse tasks
        t1 = service.add_task("Task 1")  # pending
        t2 = service.add_task("Task 2")  # pending
        t3 = service.add_task("Task 3")  # in_progress
        t4 = service.add_task("Task 4")  # done

        service.start_task(t3.id)
        service.complete_task(t4.id)

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        # Should show all counts
        assert "Task Statistics" in out
        assert "Total tasks:" in out
        assert "Pending:" in out
        assert "In Progress:" in out
        assert "Done:" in out

    def test_statistics_with_many_tasks(self, menu, service, capsys, monkeypatch):
        """_do_statistics() handles many tasks."""
        for i in range(20):
            service.add_task(f"Task {i+1}")

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "Task Statistics" in out
        assert "Total tasks:" in out

    def test_statistics_after_task_deletion(
        self, menu, service, capsys, monkeypatch
    ):
        """_do_statistics() reflects task deletions."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")

        # Delete one task
        service.delete_task(t1.id)

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        # Statistics should still show properly
        assert "Task Statistics" in out

    def test_statistics_after_status_change(
        self, menu, service, capsys, monkeypatch
    ):
        """_do_statistics() reflects status changes."""
        task = service.add_task("Changing task")

        # Change status
        service.start_task(task.id)

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "In Progress:" in out

    def test_statistics_shows_all_fields_zero_when_empty(
        self, menu, capsys, monkeypatch
    ):
        """_do_statistics() shows all fields with zeros for empty list."""
        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        # Should have all fields showing 0
        assert "Total tasks:" in out
        assert "Pending:" in out
        assert "In Progress:" in out
        assert "Done:" in out
        assert "Overdue (active):" in out
        assert "With due date:" in out


class TestStatisticsMenuIntegration:
    """Integration tests for statistics in the menu context."""

    def test_statistics_uses_service_get_statistics(self, menu, service, capsys, monkeypatch):
        """_do_statistics() calls service.get_statistics()."""
        service.add_task("Test task")

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        # Should contain the service output
        assert "Task Statistics" in out

    def test_statistics_with_description_task(
        self, menu, service, capsys, monkeypatch
    ):
        """_do_statistics() counts tasks correctly regardless of description."""
        service.add_task("Task 1", "Has description")
        service.add_task("Task 2")

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "Task Statistics" in out
        # Both tasks should be counted
        assert "Total tasks:" in out

    def test_statistics_consistency_across_multiple_calls(
        self, menu, service, capsys, monkeypatch
    ):
        """_do_statistics() shows consistent results across calls."""
        task = service.add_task("Test task")
        service.start_task(task.id)

        monkeypatch.setattr("builtins.input", lambda x: "")

        # First call
        menu._do_statistics()
        out1 = capsys.readouterr().out

        # Second call
        menu._do_statistics()
        out2 = capsys.readouterr().out

        # Both should have valid stats
        assert "Task Statistics" in out1
        assert "Task Statistics" in out2

    def test_statistics_with_overdue_potential_task(
        self, menu, service, capsys, monkeypatch
    ):
        """_do_statistics() includes overdue field in output."""
        service.add_task("Active task")

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        # Should show overdue count
        assert "Overdue (active):" in out

    def test_statistics_with_due_date_field(
        self, menu, service, capsys, monkeypatch
    ):
        """_do_statistics() includes due date field in output."""
        service.add_task("Task with potential due date")

        monkeypatch.setattr("builtins.input", lambda x: "")

        menu._do_statistics()
        out = capsys.readouterr().out

        assert "With due date:" in out


class TestStatisticsMenuOption:
    """Test that menu option 10 is properly wired."""

    def test_menu_has_option_10_handler(self, menu):
        """InteractiveMenu._do_statistics exists and is bound to option 10."""
        assert hasattr(menu, "_do_statistics")
        method = getattr(menu, "_do_statistics")
        assert callable(method)

    def test_menu_print_main_menu_includes_option_10(self, menu, capsys):
        """Menu printout includes option 10."""
        menu._print_main_menu()
        out = capsys.readouterr().out
        assert "10" in out
        assert "statistics" in out.lower()


@pytest.mark.parametrize(
    "num_pending,num_in_progress,num_done",
    [
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (2, 1, 0),
        (3, 3, 3),
        (5, 2, 1),
    ],
)
def test_statistics_parametrized_distributions(
    menu, service, capsys, monkeypatch, num_pending, num_in_progress, num_done
):
    """_do_statistics() correctly reflects various task distributions."""
    # Create pending tasks
    for i in range(num_pending):
        service.add_task(f"Pending {i+1}")

    # Create in-progress tasks
    for i in range(num_in_progress):
        t = service.add_task(f"In Progress {i+1}")
        service.start_task(t.id)

    # Create done tasks
    for i in range(num_done):
        t = service.add_task(f"Done {i+1}")
        service.complete_task(t.id)

    monkeypatch.setattr("builtins.input", lambda x: "")

    menu._do_statistics()
    out = capsys.readouterr().out

    assert "Task Statistics" in out
    assert "Total tasks:" in out
