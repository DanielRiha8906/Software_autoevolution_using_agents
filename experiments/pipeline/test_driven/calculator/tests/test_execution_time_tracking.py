import pytest
from src.models.calculation_result import CalculationResult
from src.models.operation import Operation
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.storage.json_storage import JsonStorage


def test_calculation_result_has_execution_time_ms():
    result = CalculationResult(operation="add", operand_a=1, operand_b=2, result=3)
    assert hasattr(result, "execution_time_ms")


def test_execution_time_ms_is_numeric():
    result = CalculationResult(operation="add", operand_a=1, operand_b=2, result=3)
    assert isinstance(result.execution_time_ms, (int, float))


def test_execution_time_ms_is_non_negative():
    result = CalculationResult(operation="add", operand_a=1, operand_b=2, result=3)
    assert result.execution_time_ms >= 0


def test_service_sets_execution_time_ms(tmp_path):
    storage = JsonStorage(str(tmp_path / "calc.json"))
    service = CalculatorService(Calculator(), storage)
    result = service.perform(Operation.ADD, 2, 3)
    assert result.execution_time_ms >= 0


def test_execution_time_ms_included_in_serialization():
    result = CalculationResult(operation="add", operand_a=1, operand_b=2, result=3)
    d = result.to_dict()
    assert "execution_time_ms" in d


def test_execution_time_ms_restored_from_serialization():
    result = CalculationResult(
        operation="add", operand_a=1, operand_b=2, result=3, execution_time_ms=12.5
    )
    restored = CalculationResult.from_dict(result.to_dict())
    assert restored.execution_time_ms == pytest.approx(12.5)


def test_existing_fields_unchanged():
    result = CalculationResult(operation="add", operand_a=1.0, operand_b=2.0, result=3.0)
    assert result.operation == "add"
    assert result.operand_a == 1.0
    assert result.operand_b == 2.0
    assert result.result == 3.0
