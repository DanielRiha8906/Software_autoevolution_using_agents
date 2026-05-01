import pytest
from unittest.mock import MagicMock
from src.models.operation import Operation
from src.models.calculation_result import CalculationResult
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService


class TestExecutionTime:
    """Test suite for execution time tracking feature."""

    def setup_method(self):
        self.storage = MagicMock()
        self.service = CalculatorService(Calculator(), self.storage)

    def test_execution_time_recorded(self):
        """Test that execution_time_ms is recorded in result."""
        result = self.service.perform(Operation.ADD, 3, 5)
        assert hasattr(result, 'execution_time_ms')
        assert isinstance(result.execution_time_ms, float)

    def test_execution_time_non_negative(self):
        """Test that execution_time_ms is non-negative."""
        result = self.service.perform(Operation.ADD, 1, 2)
        assert result.execution_time_ms >= 0.0

    def test_execution_time_milliseconds(self):
        """Test that execution_time_ms is in milliseconds (typically < 1ms for simple ops)."""
        result = self.service.perform(Operation.MULTIPLY, 5, 6)
        # Simple arithmetic should complete in less than 100ms
        assert result.execution_time_ms < 100.0

    def test_execution_time_saved_to_storage(self):
        """Test that execution_time_ms is passed to storage."""
        self.service.perform(Operation.DIVIDE, 10, 2)
        self.storage.save.assert_called_once()
        saved: CalculationResult = self.storage.save.call_args[0][0]
        assert hasattr(saved, 'execution_time_ms')
        assert saved.execution_time_ms >= 0.0

    def test_execution_time_all_operations(self):
        """Test that execution time is recorded for all operations."""
        operations = [
            (Operation.ADD, 3, 5),
            (Operation.SUBTRACT, 10, 4),
            (Operation.MULTIPLY, 3, 4),
            (Operation.DIVIDE, 9, 3),
        ]
        for op, a, b in operations:
            result = self.service.perform(op, a, b)
            assert result.execution_time_ms >= 0.0

    def test_execution_time_persisted_to_json(self, tmp_path):
        """Test that execution_time_ms is persisted to JSON storage."""
        from src.storage.json_storage import JsonStorage
        import json

        path = tmp_path / "calc.json"
        storage = JsonStorage(path)
        service = CalculatorService(Calculator(), storage)

        result = service.perform(Operation.ADD, 2, 3)

        # Load the JSON and verify the field is present
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert "execution_time_ms" in data[0]
        assert data[0]["execution_time_ms"] >= 0.0

    def test_execution_time_default_value(self):
        """Test that execution_time_ms defaults to 0.0 for manually created results."""
        result = CalculationResult("add", 1, 2, 3, "2026-01-01T00:00:00")
        assert result.execution_time_ms == 0.0

    def test_execution_time_explicit_value(self):
        """Test that execution_time_ms can be set explicitly."""
        result = CalculationResult("add", 1, 2, 3, "2026-01-01T00:00:00", 5.5)
        assert result.execution_time_ms == 5.5

    def test_execution_time_in_to_dict(self):
        """Test that execution_time_ms is included in to_dict output."""
        result = CalculationResult("add", 1, 2, 3, "2026-01-01T00:00:00", 2.5)
        result_dict = result.to_dict()
        assert "execution_time_ms" in result_dict
        assert result_dict["execution_time_ms"] == 2.5

    def test_execution_time_from_dict_with_field(self):
        """Test that from_dict correctly reconstructs result with execution_time_ms."""
        data = {
            "operation": "multiply",
            "operand_a": 3,
            "operand_b": 4,
            "result": 12,
            "timestamp": "2026-01-01T00:00:00",
            "execution_time_ms": 1.25
        }
        result = CalculationResult.from_dict(data)
        assert result.execution_time_ms == 1.25
        assert result.operation == "multiply"
        assert result.result == 12
