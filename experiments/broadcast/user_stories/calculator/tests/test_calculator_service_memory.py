import pytest
from unittest.mock import MagicMock
from src.models.operation import Operation
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService


class TestCalculatorServiceMemory:
    def setup_method(self):
        _reset_id_counter()
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_with_memory_success(self):
        result = self.service.perform_with_memory(Operation.ADD, 3, 5)
        assert isinstance(result, ResultEntry)
        assert result.operation == "add"
        assert result.operands == [3, 5]
        assert result.result == 8
        assert result.is_error() is False

    def test_perform_with_memory_saves_entry(self):
        self.service.perform_with_memory(Operation.MULTIPLY, 2, 3)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert isinstance(saved, ResultEntry)
        assert saved.result == 6

    def test_perform_with_memory_divide_by_zero_error(self):
        with pytest.raises(ValueError, match="Division by zero"):
            self.service.perform_with_memory(Operation.DIVIDE, 5, 0)

    def test_perform_with_memory_divide_by_zero_saves_error(self):
        try:
            self.service.perform_with_memory(Operation.DIVIDE, 5, 0)
        except ValueError:
            pass
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        assert isinstance(saved, ErrorEntry)
        assert saved.operation == "divide"
        assert saved.error_message == "Division by zero is not allowed"
        assert saved.is_error() is True

    def test_perform_with_memory_sqrt_negative_error(self):
        try:
            self.service.perform_with_memory(Operation.SQRT, -1, 0)
        except ValueError:
            pass
        saved = self.storage.save.call_args[0][0]
        assert isinstance(saved, ErrorEntry)
        assert "negative" in saved.error_message.lower()

    def test_perform_with_memory_modulo_by_zero_error(self):
        try:
            self.service.perform_with_memory(Operation.MODULO, 10, 0)
        except ValueError:
            pass
        saved = self.storage.save.call_args[0][0]
        assert isinstance(saved, ErrorEntry)
        assert "zero" in saved.error_message.lower()

    def test_perform_with_memory_has_execution_time(self):
        result = self.service.perform_with_memory(Operation.ADD, 1, 1)
        assert result.execution_time_ms >= 0.0

    def test_perform_with_memory_has_timestamp(self):
        result = self.service.perform_with_memory(Operation.SUBTRACT, 5, 3)
        assert result.timestamp != ""
        assert "T" in result.timestamp

    def test_perform_with_memory_has_sequential_ids(self):
        _reset_id_counter()
        r1 = self.service.perform_with_memory(Operation.ADD, 1, 1)
        r2 = self.service.perform_with_memory(Operation.SUBTRACT, 5, 2)
        try:
            self.service.perform_with_memory(Operation.DIVIDE, 1, 0)
        except ValueError:
            pass
        e1 = self.storage.save.call_args_list[2][0][0]
        assert r1.entry_id == 1
        assert r2.entry_id == 2
        assert e1.entry_id == 3

    def test_get_memory_history(self):
        mock_history = [
            ResultEntry(operation="add", operands=[1, 2], result=3),
            ErrorEntry(operation="divide", operands=[5, 0], error_message="error"),
        ]
        self.storage.load_memory_all.return_value = mock_history
        history = self.service.get_memory_history()
        assert len(history) == 2
        assert history[0].is_error() is False
        assert history[1].is_error() is True

    def test_perform_vs_perform_with_memory(self):
        """Verify that perform() still works as before and doesn't save memory entries."""
        _reset_id_counter()
        self.service.perform(Operation.ADD, 3, 5)
        self.storage.save.assert_called_once()
        saved = self.storage.save.call_args[0][0]
        # Should be CalculationResult, not MemoryEntry
        assert not isinstance(saved, (ResultEntry, ErrorEntry))
