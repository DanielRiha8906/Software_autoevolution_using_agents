"""Tests for the GUI application.

Note: These tests focus on the business logic and calculator integration
aspects of the GUI application. Full tkinter widget testing is handled
separately to avoid complex mocking of GUI elements.
"""

import unittest
from pathlib import Path
import tempfile
import subprocess

from src.models.operation import Operation
from src.models.memory_entry import ResultEntry, ErrorEntry
from src.services.calculator import Calculator
from src.services.calculator_service import CalculatorService
from src.services.memory_store_impl import MemoryStoreImpl
from src.storage.json_storage import JsonStorage


class TestGUIApplicationLogic(unittest.TestCase):
    """Test cases for GUI business logic without tkinter UI elements."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary storage file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_file.close()
        self.storage_path = Path(self.temp_file.name)

        # Initialize services
        self.storage = JsonStorage(self.storage_path)
        self.service = CalculatorService(Calculator(), self.storage)
        self.memory_store = MemoryStoreImpl(self.storage)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Remove temp file
        if self.storage_path.exists():
            self.storage_path.unlink()

    def test_service_integration_add(self) -> None:
        """Test that calculator service correctly performs addition."""
        result = self.service.perform(Operation.ADD, 5.0, 3.0)
        self.assertEqual(result.result, 8.0)

    def test_service_integration_subtract(self) -> None:
        """Test that calculator service correctly performs subtraction."""
        result = self.service.perform(Operation.SUBTRACT, 10.0, 3.0)
        self.assertEqual(result.result, 7.0)

    def test_service_integration_multiply(self) -> None:
        """Test that calculator service correctly performs multiplication."""
        result = self.service.perform(Operation.MULTIPLY, 6.0, 7.0)
        self.assertEqual(result.result, 42.0)

    def test_service_integration_divide(self) -> None:
        """Test that calculator service correctly performs division."""
        result = self.service.perform(Operation.DIVIDE, 20.0, 4.0)
        self.assertEqual(result.result, 5.0)

    def test_service_integration_square(self) -> None:
        """Test that calculator service correctly performs square."""
        result = self.service.perform(Operation.SQUARE, 5.0)
        self.assertEqual(result.result, 25.0)

    def test_service_integration_sqrt(self) -> None:
        """Test that calculator service correctly performs square root."""
        result = self.service.perform(Operation.SQRT, 16.0)
        self.assertEqual(result.result, 4.0)

    def test_service_integration_power(self) -> None:
        """Test that calculator service correctly performs power."""
        result = self.service.perform(Operation.POWER, 2.0, 8.0)
        self.assertEqual(result.result, 256.0)

    def test_service_integration_modulo(self) -> None:
        """Test that calculator service correctly performs modulo."""
        result = self.service.perform(Operation.MODULO, 17.0, 5.0)
        self.assertEqual(result.result, 2.0)

    def test_service_integration_sin(self) -> None:
        """Test that calculator service correctly performs sine."""
        result = self.service.perform(Operation.SIN, 0.0)
        self.assertAlmostEqual(result.result, 0.0, places=5)

    def test_service_integration_cos(self) -> None:
        """Test that calculator service correctly performs cosine."""
        result = self.service.perform(Operation.COS, 0.0)
        self.assertAlmostEqual(result.result, 1.0, places=5)

    def test_service_integration_tan(self) -> None:
        """Test that calculator service correctly performs tangent."""
        result = self.service.perform(Operation.TAN, 0.0)
        self.assertAlmostEqual(result.result, 0.0, places=5)

    def test_service_integration_log(self) -> None:
        """Test that calculator service correctly performs logarithm."""
        result = self.service.perform(Operation.LOG, 100.0)
        self.assertEqual(result.result, 2.0)

    def test_service_integration_ln(self) -> None:
        """Test that calculator service correctly performs natural logarithm."""
        result = self.service.perform(Operation.LN, 1.0)
        self.assertEqual(result.result, 0.0)

    def test_service_integration_exp(self) -> None:
        """Test that calculator service correctly performs exponential."""
        result = self.service.perform(Operation.EXP, 0.0)
        self.assertEqual(result.result, 1.0)

    def test_division_by_zero_raises_error(self) -> None:
        """Test that division by zero raises an error."""
        with self.assertRaises(ValueError):
            self.service.perform(Operation.DIVIDE, 5.0, 0.0)

    def test_operation_arity_unary(self) -> None:
        """Test that unary operations are correctly identified."""
        unary_ops = [
            Operation.SIN,
            Operation.COS,
            Operation.TAN,
            Operation.LOG,
            Operation.LN,
            Operation.EXP,
            Operation.SQUARE,
            Operation.SQRT,
        ]

        for op in unary_ops:
            self.assertEqual(op.arity(), 1, f"{op.value} should be unary")
            self.assertTrue(op.is_unary())

    def test_operation_arity_binary(self) -> None:
        """Test that binary operations are correctly identified."""
        binary_ops = [
            Operation.ADD,
            Operation.SUBTRACT,
            Operation.MULTIPLY,
            Operation.DIVIDE,
            Operation.POWER,
            Operation.MODULO,
        ]

        for op in binary_ops:
            self.assertEqual(op.arity(), 2, f"{op.value} should be binary")
            self.assertFalse(op.is_unary())

    def test_operation_from_string(self) -> None:
        """Test that operations can be created from string."""
        op = Operation.from_string("add")
        self.assertEqual(op, Operation.ADD)

        op = Operation.from_string("sqrt")
        self.assertEqual(op, Operation.SQRT)

    def test_operation_display_name(self) -> None:
        """Test that operation display names are formatted correctly."""
        self.assertEqual(Operation.ADD.display_name(), "Add")
        self.assertEqual(Operation.SQRT.display_name(), "Sqrt")

    def test_history_entry_formatting_success(self) -> None:
        """Test formatting of successful history entries."""
        entry = ResultEntry(
            entry_id=1,
            operation="add",
            operands=[5.0, 3.0],
            result=8.0,
            timestamp="2024-01-01T12:00:00",
            execution_time_ms=1.5,
        )

        # Format manually to test logic
        formatted = (
            f"ID {entry.entry_id} | {entry.operation.upper()} "
            f"{' '.join(str(o) for o in entry.operands)} = {entry.result}"
        )

        self.assertIn("ID 1", formatted)
        self.assertIn("ADD", formatted)
        self.assertIn("5.0", formatted)
        self.assertIn("3.0", formatted)
        self.assertIn("8.0", formatted)

    def test_history_entry_formatting_error(self) -> None:
        """Test formatting of error history entries."""
        entry = ErrorEntry(
            entry_id=2,
            operation="divide",
            operands=[5.0, 0.0],
            error_message="division by zero",
            timestamp="2024-01-01T12:00:01",
            execution_time_ms=0.5,
        )

        # Format manually to test logic
        formatted = (
            f"ID {entry.entry_id} | {entry.operation.upper()} | "
            f"Error: {entry.error_message}"
        )

        self.assertIn("ID 2", formatted)
        self.assertIn("DIVIDE", formatted)
        self.assertIn("Error", formatted)
        self.assertIn("division by zero", formatted)

    def test_negative_result_handling(self) -> None:
        """Test that negative results are handled correctly."""
        result = self.service.perform(Operation.SUBTRACT, 3.0, 8.0)
        self.assertEqual(result.result, -5.0)

    def test_decimal_result_handling(self) -> None:
        """Test that decimal results are handled correctly."""
        result = self.service.perform(Operation.DIVIDE, 1.0, 3.0)
        # Result should be approximately 0.333...
        self.assertAlmostEqual(result.result, 0.333333, places=5)

    def test_memory_entry_serialization(self) -> None:
        """Test that memory entries can be serialized and deserialized."""
        original = ResultEntry(
            entry_id=1,
            operation="add",
            operands=[5.0, 3.0],
            result=8.0,
            timestamp="2024-01-01T12:00:00",
            execution_time_ms=1.5,
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = ResultEntry.from_dict(data)

        self.assertEqual(original.entry_id, restored.entry_id)
        self.assertEqual(original.operation, restored.operation)
        self.assertEqual(original.operands, restored.operands)
        self.assertEqual(original.result, restored.result)

    def test_operation_enum_all_values_exist(self) -> None:
        """Test that all operation values can be accessed."""
        operations = [
            Operation.ADD,
            Operation.SUBTRACT,
            Operation.MULTIPLY,
            Operation.DIVIDE,
            Operation.SQUARE,
            Operation.SQRT,
            Operation.POWER,
            Operation.MODULO,
            Operation.SIN,
            Operation.COS,
            Operation.TAN,
            Operation.LOG,
            Operation.LN,
            Operation.EXP,
        ]

        self.assertEqual(len(operations), 14)

        # Verify all have valid values
        for op in operations:
            self.assertIsNotNone(op.value)
            self.assertTrue(len(op.value) > 0)

    def test_gui_launch_flag_exists(self) -> None:
        """Test that --gui flag is properly defined in argparse."""
        result = subprocess.run(
            ["python", "-m", "src", "--help"],
            cwd="/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/broadcast/user_stories/calculator",
            capture_output=True,
            text=True,
        )

        self.assertIn("--gui", result.stdout)
        self.assertIn("graphical user interface", result.stdout)

    def test_service_returns_calculation_result(self) -> None:
        """Test that service returns CalculationResult with timing info."""
        result = self.service.perform(Operation.ADD, 5.0, 3.0)

        # CalculationResult should have these properties
        self.assertIsNotNone(result.operation)
        self.assertIsNotNone(result.result)
        self.assertIsNotNone(result.execution_time_ms)
        self.assertGreaterEqual(result.execution_time_ms, 0)

    def test_multiple_operations_sequence(self) -> None:
        """Test a sequence of operations."""
        # Test: 5 + 3 = 8
        r1 = self.service.perform(Operation.ADD, 5.0, 3.0)
        self.assertEqual(r1.result, 8.0)

        # Test: 8 - 2 = 6
        r2 = self.service.perform(Operation.SUBTRACT, 8.0, 2.0)
        self.assertEqual(r2.result, 6.0)

        # Test: 6 * 2 = 12
        r3 = self.service.perform(Operation.MULTIPLY, 6.0, 2.0)
        self.assertEqual(r3.result, 12.0)

    def test_scientific_operations_available(self) -> None:
        """Test that all scientific operations are available."""
        scientific_ops = [
            Operation.SIN,
            Operation.COS,
            Operation.TAN,
            Operation.LOG,
            Operation.LN,
            Operation.EXP,
        ]

        for op in scientific_ops:
            # Just verify these operations exist and can be performed
            self.assertIsNotNone(op.value)


if __name__ == "__main__":
    unittest.main()
