import sys

from ..models.operation import Operation
from ..protocols import CalculationService, MemoryService


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
        (Operation.SIN,      "Sin"),
        (Operation.COS,      "Cos"),
        (Operation.TAN,      "Tan"),
        (Operation.LOG,      "Log"),
        (Operation.LN,       "Ln"),
        (Operation.EXP,      "Exp"),
    ]

    def __init__(self, service: CalculationService, memory_service: MemoryService | None = None) -> None:
        self.service = service
        self.memory_service = memory_service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt = len(self._MENU) + 1
            memory_opt  = len(self._MENU) + 2
            filter_op_opt = len(self._MENU) + 3
            filter_status_opt = len(self._MENU) + 4
            statistics_opt = len(self._MENU) + 5
            export_opt = len(self._MENU) + 6
            import_opt = len(self._MENU) + 7
            exit_opt    = len(self._MENU) + 8

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(memory_opt):
                self._show_memory()
                continue

            if choice == str(filter_op_opt):
                self._filter_memory_by_operation()
                continue

            if choice == str(filter_status_opt):
                self._filter_memory_by_status()
                continue

            if choice == str(statistics_opt):
                self._show_statistics()
                continue

            if choice == str(export_opt):
                self.export_memory()
                continue

            if choice == str(import_opt):
                self.import_memory()
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
        print(f"  {len(self._MENU) + 2}. View memory")
        print(f"  {len(self._MENU) + 3}. Filter memory by operation")
        print(f"  {len(self._MENU) + 4}. Filter memory by status")
        print(f"  {len(self._MENU) + 5}. View statistics")
        print(f"  {len(self._MENU) + 6}. Export memory to file")
        print(f"  {len(self._MENU) + 7}. Import memory from file")
        print(f"  {len(self._MENU) + 8}. Exit")

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

    def show_memory(self) -> None:
        """Display all stored memory entries (used in one-shot CLI mode)."""
        if self.memory_service is None:
            print("Memory service not available.")
            return
        self._show_memory()

    def show_statistics(self) -> None:
        """Display statistics (used in one-shot CLI mode)."""
        if self.memory_service is None:
            print("Memory service not available.")
            return
        self._show_statistics()

    def export_memory(self, filepath: str | None = None) -> None:
        """
        Export all memory entries to a JSON file.

        If filepath is not provided, prompts the user for one.

        Args:
            filepath: Optional file path. If None, user is prompted.
        """
        if self.memory_service is None:
            print("Memory service not available.")
            return

        if filepath is None:
            filepath = input("\n  Enter file path to export to: ").strip()
            if not filepath:
                print("  Export cancelled.\n")
                return

        try:
            count = self.memory_service.export_to_file(filepath)
            print(f"\n  Successfully exported {count} entries to {filepath}\n")
        except Exception as exc:
            print(f"\n  Error exporting memory: {exc}\n")

    def import_memory(self, filepath: str | None = None, skip_invalid: bool = False) -> None:
        """
        Import memory entries from a JSON file and append to storage.

        If filepath is not provided, prompts the user for one.

        Args:
            filepath: Optional file path. If None, user is prompted.
            skip_invalid: If True, skip malformed entries instead of failing.
        """
        if self.memory_service is None:
            print("Memory service not available.")
            return

        if filepath is None:
            filepath = input("\n  Enter file path to import from: ").strip()
            if not filepath:
                print("  Import cancelled.\n")
                return

        try:
            imported_count, skipped = self.memory_service.import_from_file(
                filepath, skip_invalid=skip_invalid
            )
            print(f"\n  Successfully imported {imported_count} entries from {filepath}")
            if skipped:
                print(f"  Skipped {len(skipped)} invalid entries:")
                for skip_entry in skipped:
                    print(f"    - {skip_entry['error']}")
            print()
        except FileNotFoundError as exc:
            print(f"\n  Error: File not found - {exc}\n")
        except ValueError as exc:
            print(f"\n  Error: {exc}\n")
        except Exception as exc:
            print(f"\n  Error importing memory: {exc}\n")

    def _show_memory(self) -> None:
        """Display all memory entries (internal method for interactive menu)."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        entries = self.memory_service.retrieve_all()
        if not entries:
            print("\n  No memory entries recorded yet.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry}")
        print()

    def _filter_memory_by_operation(self) -> None:
        """Filter and display memory entries by operation name."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        operation_name = input("\n  Enter operation name (add, subtract, multiply, divide, square, sqrt, power, modulo, sin, cos, tan, log, ln, exp): ").strip()
        entries = self.memory_service.filter_by_operation(operation_name)
        if not entries:
            print(f"\n  No memory entries match operation '{operation_name}'.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry}")
        print()

    def _filter_memory_by_status(self) -> None:
        """Filter and display memory entries by success status."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        print("\n  Filter by status:")
        print("    1. Successful")
        print("    2. Failed")
        choice = input("  Choose: ").strip()
        if choice == "1":
            success = True
            status_label = "successful"
        elif choice == "2":
            success = False
            status_label = "failed"
        else:
            print("  Invalid choice.\n")
            return
        entries = self.memory_service.filter_by_success(success)
        if not entries:
            print(f"\n  No memory entries match status '{status_label}'.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            print(f"  {i}. {entry}")
        print()

    def _show_statistics(self) -> None:
        """Display calculation statistics."""
        if self.memory_service is None:
            print("\n  Memory service not available.\n")
            return
        stats = self.memory_service.compute_statistics()
        if stats.total_calculations == 0:
            print("\n  No calculations recorded yet.\n")
            return

        print()
        print("  === Calculation Statistics ===")
        print()
        print(f"  Total Calculations: {stats.total_calculations}")
        print(f"  Successful: {stats.total_calculations - stats.error_count}")
        print(f"  Failed: {stats.error_count}")
        print(f"  Error Rate: {stats.error_percentage:.2f}%")
        print()
        print(f"  Average Execution Time: {stats.average_execution_time_ms:.2f} ms")
        print(f"  Min Execution Time: {stats.min_execution_time_ms:.2f} ms")
        print(f"  Max Execution Time: {stats.max_execution_time_ms:.2f} ms")
        print()
        print("  Operation Usage:")
        for operation, count in sorted(stats.operation_counts.items()):
            op_stats = stats.per_operation_stats.get(operation, {})
            error_rate = op_stats.get("error_rate", 0.0)
            print(f"    {operation}: {count} calculations ({error_rate:.2f}% error rate)")
        print()
