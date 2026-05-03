import json
import pytest
from pathlib import Path
from src.models.memory_entry import ResultEntry, ErrorEntry, _reset_id_counter
from src.services.calculator_service import CalculatorService
from src.services.memory_service import MemoryService
from src.services.calculator import Calculator
from src.storage.json_storage import JsonStorage
from src.cli.calculator_cli import CalculatorCLI


class TestCLIExportCommand:
    @pytest.fixture
    def cli(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "storage.json"
        calc_service = CalculatorService(Calculator(), JsonStorage(storage_path))
        memory_service = MemoryService(JsonStorage(storage_path))
        return CalculatorCLI(calc_service, memory_service), tmp_path

    def test_export_command_empty(self, cli):
        cli_instance, tmp_path = cli
        export_path = tmp_path / "export.json"
        cli_instance.export_command(str(export_path))
        assert export_path.exists()

    def test_export_command_with_entries(self, cli):
        cli_instance, tmp_path = cli
        # Add some entries
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00")
        e2 = ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T01:00:00")
        cli_instance.memory_service.store(e1)
        cli_instance.memory_service.store(e2)

        # Export
        export_path = tmp_path / "export.json"
        cli_instance.export_command(str(export_path))

        # Verify
        assert export_path.exists()
        with open(export_path) as f:
            data = json.load(f)
        assert len(data) == 2

    def test_export_command_creates_directory(self, cli):
        cli_instance, tmp_path = cli
        export_path = tmp_path / "subdir" / "export.json"
        cli_instance.export_command(str(export_path))
        assert export_path.exists()


class TestCLIImportCommand:
    @pytest.fixture
    def cli(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "storage.json"
        calc_service = CalculatorService(Calculator(), JsonStorage(storage_path))
        memory_service = MemoryService(JsonStorage(storage_path))
        return CalculatorCLI(calc_service, memory_service), tmp_path

    def test_import_command_empty_file(self, cli):
        cli_instance, tmp_path = cli
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump([], f)

        cli_instance.import_command(str(import_path))
        entries = cli_instance.memory_service.retrieve()
        assert len(entries) == 0

    def test_import_command_with_entries(self, cli):
        cli_instance, tmp_path = cli
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,
                "operation": "add",
                "operands": [1, 2],
                "result": 3,
                "timestamp": "2026-01-01T00:00:00",
                "execution_time_ms": 1.0,
            },
            {
                "type": "error",
                "entry_id": 2,
                "operation": "divide",
                "operands": [5, 0],
                "error_message": "Division by zero",
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.1,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        cli_instance.import_command(str(import_path))
        entries = cli_instance.memory_service.retrieve()
        assert len(entries) == 2
        assert entries[0].operation == "add"
        assert entries[1].operation == "divide"

    def test_import_command_skip_duplicates_by_default(self, cli):
        cli_instance, tmp_path = cli
        # Add an initial entry
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00", entry_id=1)
        cli_instance.memory_service.store(e1)

        # Try to import with duplicate
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,  # duplicate
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.5,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        cli_instance.import_command(str(import_path), overwrite=False)
        entries = cli_instance.memory_service.retrieve()
        # Should still have only 1 entry
        assert len(entries) == 1
        assert entries[0].operation == "add"

    def test_import_command_overwrite_enabled(self, cli):
        cli_instance, tmp_path = cli
        # Add an initial entry
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00", entry_id=1)
        cli_instance.memory_service.store(e1)

        # Try to import with duplicate but overwrite enabled
        import_path = tmp_path / "import.json"
        data = [
            {
                "type": "result",
                "entry_id": 1,  # duplicate
                "operation": "multiply",
                "operands": [3, 4],
                "result": 12,
                "timestamp": "2026-01-01T01:00:00",
                "execution_time_ms": 0.5,
            },
        ]
        with open(import_path, "w") as f:
            json.dump(data, f)

        cli_instance.import_command(str(import_path), overwrite=True)
        entries = cli_instance.memory_service.retrieve()
        # Should have 2 entries now
        assert len(entries) == 2

    def test_import_command_file_not_found(self, cli):
        cli_instance, tmp_path = cli
        with pytest.raises(SystemExit):
            cli_instance.import_command(str(tmp_path / "nonexistent.json"))

    def test_import_command_invalid_json(self, cli):
        cli_instance, tmp_path = cli
        import_path = tmp_path / "invalid.json"
        with open(import_path, "w") as f:
            f.write("not valid json {")

        with pytest.raises(SystemExit):
            cli_instance.import_command(str(import_path))


class TestCLIExportImportIntegration:
    def test_export_then_import(self, tmp_path):
        _reset_id_counter()
        storage_path = tmp_path / "storage.json"
        calc_service = CalculatorService(Calculator(), JsonStorage(storage_path))
        memory_service = MemoryService(JsonStorage(storage_path))
        cli = CalculatorCLI(calc_service, memory_service)

        # Add entries to first service
        e1 = ResultEntry(operation="add", operands=[1, 2], result=3, timestamp="2026-01-01T00:00:00")
        e2 = ErrorEntry(operation="divide", operands=[5, 0], error_message="Division by zero", timestamp="2026-01-01T01:00:00")
        e3 = ResultEntry(operation="multiply", operands=[3, 4], result=12, timestamp="2026-01-01T02:00:00")
        cli.memory_service.store(e1)
        cli.memory_service.store(e2)
        cli.memory_service.store(e3)

        # Export
        export_path = tmp_path / "export.json"
        cli.export_command(str(export_path))

        # Create new service and import
        _reset_id_counter()
        storage_path2 = tmp_path / "storage2.json"
        calc_service2 = CalculatorService(Calculator(), JsonStorage(storage_path2))
        memory_service2 = MemoryService(JsonStorage(storage_path2))
        cli2 = CalculatorCLI(calc_service2, memory_service2)

        cli2.import_command(str(export_path))

        # Verify
        entries = cli2.memory_service.retrieve()
        assert len(entries) == 3
        assert entries[0].operation == "add"
        assert entries[1].operation == "divide"
        assert entries[2].operation == "multiply"
