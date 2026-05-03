import sys
from typing import Optional

from ..models.operation import Operation
from ..models.statistics_report import StatisticsReport
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService
from ..services.statistics_service import StatisticsService
from ..services.import_export_service import ImportExportService


class CalculatorCLI:
    _MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square Root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    def __init__(self, service: CalculatorService, memory_service: Optional[MemoryService] = None) -> None:
        self.service = service
        self.memory_service = memory_service or MemoryService()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt = len(self._MENU) + 1
            query_opt   = len(self._MENU) + 2
            stats_opt   = len(self._MENU) + 3
            export_opt  = len(self._MENU) + 4
            import_opt  = len(self._MENU) + 5
            exit_opt    = len(self._MENU) + 6

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(query_opt):
                self._query_history()
                continue

            if choice == str(stats_opt):
                self._show_statistics()
                continue

            if choice == str(export_opt):
                self._export_entries()
                continue

            if choice == str(import_opt):
                self._import_entries()
                continue

            operation = self._resolve_menu_choice(choice)
            if operation is None:
                print("Invalid choice — try again.\n")
                continue

            a = self._prompt_number("Enter first number: ")
            if a is None:
                continue
            b = self._prompt_number("Enter second number: ")
            if b is None:
                continue

            try:
                result = self.service.perform(operation, a, b)
                print(f"\n  Result: {result}\n")
            except ValueError as exc:
                print(f"\n  Error: {exc}\n")

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        try:
            operation = Operation.from_string(operation_str)
            result = self.service.perform(operation, a, b)
            print(result)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View history")
        print(f"  {len(self._MENU) + 2}. Query memory")
        print(f"  {len(self._MENU) + 3}. Show statistics")
        print(f"  {len(self._MENU) + 4}. Export entries")
        print(f"  {len(self._MENU) + 5}. Import entries")
        print(f"  {len(self._MENU) + 6}. Exit")

    def _resolve_menu_choice(self, choice: str) -> Operation | None:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self._MENU):
                return self._MENU[idx][0]
        except ValueError:
            pass
        return None

    def _prompt_number(self, prompt: str) -> float | None:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  Invalid number: '{raw}' — please enter a numeric value.")
            return None

    def _show_history(self) -> None:
        history = self.service.get_history()
        if not history:
            print("\n  No calculations recorded yet.\n")
            return
        print()
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry}  [{entry.timestamp}]")
        print()

    def _query_history(self) -> None:
        """Interactive query interface for memory entries."""
        operation_filter = self._prompt_optional_filter("Enter operation to filter by (or press Enter to skip): ")
        success_filter = self._prompt_success_filter("Filter by success state? (y/n/skip): ")

        results = self.memory_service.query(operation=operation_filter, success=success_filter)
        if not results:
            print("\n  No matching entries found.\n")
            return

        print()
        for i, entry in enumerate(results, 1):
            print(f"  {i}. {entry.operation} {entry.operands} = {entry.result} (success: {entry.success})  [{entry.timestamp}]")
        print()

    def _prompt_optional_filter(self, prompt: str) -> Optional[str]:
        """Prompt for an optional string filter, return None if empty."""
        raw = input(prompt).strip()
        return raw if raw else None

    def _prompt_success_filter(self, prompt: str) -> Optional[bool]:
        """Prompt for optional success state filter."""
        raw = input(prompt).strip().lower()
        if raw == "y":
            return True
        elif raw == "n":
            return False
        else:
            return None

    def run_query(self, operation: Optional[str] = None, success: Optional[bool] = None) -> None:
        """One-shot query interface for memory entries."""
        results = self.memory_service.query(operation=operation, success=success)
        if not results:
            print("No matching entries found.")
            return

        for entry in results:
            print(f"{entry.operation} {entry.operands} = {entry.result} (success: {entry.success}) [{entry.timestamp}]")

    def _show_statistics(self) -> None:
        """Display statistics in interactive mode."""
        stats_service = StatisticsService(self.memory_service)
        report = stats_service.compute()
        self.show_statistics(report)

    def show_statistics(self, report: StatisticsReport) -> None:
        """Format and display statistics report."""
        print("\n=== Statistics ===")
        if not report.count_per_operation:
            print("  No data available.\n")
            return
        print(f"  Operations: {report.count_per_operation}")
        print(f"  Total errors: {report.total_errors}")
        print(f"  Error rate: {report.error_rate:.2f}%")
        print(f"  Average execution time: {report.avg_execution_time_ms:.2f} ms\n")

    def _export_entries(self) -> None:
        """Export memory entries to a JSON file in interactive mode."""
        filepath = input("Enter filepath for export (or press Enter to skip): ").strip()
        if not filepath:
            print()
            return

        try:
            service = ImportExportService()
            count = service.export(self.memory_service, filepath)
            print(f"\n  Exported {count} entries to {filepath}\n")
        except Exception as exc:
            print(f"\n  Error exporting: {exc}\n")

    def _import_entries(self) -> None:
        """Import memory entries from a JSON file in interactive mode."""
        filepath = input("Enter filepath for import (or press Enter to skip): ").strip()
        if not filepath:
            print()
            return

        try:
            service = ImportExportService()
            count = service.import_from(self.memory_service, filepath)
            print(f"\n  Imported {count} entries from {filepath}\n")
        except Exception as exc:
            print(f"\n  Error importing: {exc}\n")
