import pytest
from unittest.mock import MagicMock
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService


class TestCalculatorService:
    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_perform_add_returns_result(self):
        result = self.service.perform(Operation.ADD, 3, 5)
        assert result.result == 8
        assert result.operation == "add"
        assert result.operand_a == 3
        assert result.operand_b == 5

    def test_perform_subtract(self):
        assert self.service.perform(Operation.SUBTRACT, 10, 4).result == 6

    def test_perform_multiply(self):
        assert self.service.perform(Operation.MULTIPLY, 3, 4).result == 12

    def test_perform_divide(self):
        assert self.service.perform(Operation.DIVIDE, 9, 3).result == 3.0

    def test_perform_saves_to_storage(self):
        self.service.perform(Operation.ADD, 3, 5)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert saved.result == 8

    def test_perform_divide_by_zero_raises(self):
        with pytest.raises(ValueError, match="Division by zero"):
            self.service.perform(Operation.DIVIDE, 5, 0)

    def test_perform_divide_by_zero_does_not_save(self):
        with pytest.raises(ValueError):
            self.service.perform(Operation.DIVIDE, 5, 0)
        self.storage.save.assert_not_called()

    def test_get_history_delegates_to_storage(self):
        mock_history = [CalculationResult("add", 1, 2, 3, "2026-01-01T00:00:00")]
        self.storage.load_all.return_value = mock_history
        assert self.service.get_history() == mock_history

    def test_result_has_timestamp(self):
        result = self.service.perform(Operation.ADD, 1, 1)
        assert result.timestamp != ""

    def test_calculation_result_has_execution_time_ms(self):
        result = self.service.perform(Operation.ADD, 3, 5)
        assert hasattr(result, "execution_time_ms")
        assert result.execution_time_ms is not None

    def test_execution_time_ms_is_numeric(self):
        result = self.service.perform(Operation.ADD, 3, 5)
        assert isinstance(result.execution_time_ms, (int, float))

    def test_execution_time_ms_is_non_negative(self):
        result = self.service.perform(Operation.ADD, 3, 5)
        assert result.execution_time_ms >= 0

    def test_service_sets_execution_time_ms(self):
        result = self.service.perform(Operation.MULTIPLY, 4, 5)
        assert result.execution_time_ms >= 0
        assert isinstance(result.execution_time_ms, (int, float))

    def test_execution_time_ms_included_in_serialization(self):
        result = self.service.perform(Operation.SUBTRACT, 10, 3)
        result_dict = result.to_dict()
        assert "execution_time_ms" in result_dict
        assert result_dict["execution_time_ms"] == result.execution_time_ms

    def test_execution_time_ms_restored_from_serialization(self):
        original = self.service.perform(Operation.DIVIDE, 12, 3)
        original_execution_time = original.execution_time_ms

        serialized = original.to_dict()
        restored = CalculationResult.from_dict(serialized)

        assert restored.execution_time_ms == original_execution_time

    def test_existing_fields_unchanged(self):
        result = self.service.perform(Operation.ADD, 2, 3)
        assert result.operation == "add"
        assert result.operand_a == 2
        assert result.operand_b == 3
        assert result.result == 5
        assert result.timestamp != ""
