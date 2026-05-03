import sys

from ..models.operation import Operation
from ..models.memory_entry import ErrorEntry, ResultEntry
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService
from ..services.statistics_service import StatisticsService


class CalculatorCLI:
    _MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    def __init__(self, service: CalculatorService, memory_service: MemoryService) -> None:
        self.service = service
        self.memory_service = memory_service
        self.statistics_service = StatisticsService(memory_service)

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            memory_history_opt = len(self._MENU) + 1
            history_opt        = len(self._MENU) + 2
            filter_opt         = len(self._MENU) + 3
            statistics_opt     = len(self._MENU) + 4
            export_opt         = len(self._MENU) + 5
            import_opt         = len(self._MENU) + 6
            exit_opt           = len(self._MENU) + 7

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(memory_history_opt):
                self._show_memory_history()
                continue

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(filter_opt):
                self._filter_interactive()
                continue

            if choice == str(statistics_opt):
                self._show_statistics()
                continue

            if choice == str(export_opt):
                self._export_interactive()
                continue

            if choice == str(import_opt):
                self._import_interactive()
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

    def show_memory_history_command(self) -> None:
        """Show memory history and exit (one-shot mode)."""
        self._show_memory_history()

    def show_history_command(self) -> None:
        """Show calculation history and exit (one-shot mode)."""
        self._show_history()

    def memory_retrieve_command(self) -> None:
        """Retrieve and display all memory entries (one-shot mode)."""
        entries = self.memory_service.retrieve()
        if not entries:
            print("No memory entries recorded yet.")
            return
        print(f"Retrieved {len(entries)} memory entries:")
        for entry in entries:
            self._print_memory_entry(entry)

    def memory_store_command(self, operation_str: str, operands: list[float], result: float | None = None, error: str | None = None) -> None:
        """Store a memory entry (one-shot mode).

        Args:
            operation_str: The operation name
            operands: List of operands
            result: Optional result value (for success)
            error: Optional error message (for failure)
        """
        from ..models.memory_entry import ResultEntry, ErrorEntry

        try:
            if error is not None:
                entry = ErrorEntry(
                    operation=operation_str,
                    operands=operands,
                    error_message=error,
                )
            else:
                if result is None:
                    print("Error: result required for successful entry", file=sys.stderr)
                    sys.exit(1)
                entry = ResultEntry(
                    operation=operation_str,
                    operands=operands,
                    result=result,
                )
            self.memory_service.store(entry)
            print(f"Stored {entry}")
        except Exception as exc:
            print(f"Error storing entry: {exc}", file=sys.stderr)
            sys.exit(1)

    def filter_command(self, operation: str | None = None, state: str | None = None) -> None:
        """Filter and display memory entries (one-shot mode).

        Args:
            operation: Operation type to filter by (e.g., 'add')
            state: Result state to filter by ('success' or 'error')
        """
        try:
            results = self.memory_service.filter_entries(operation=operation, state=state)
            if not results:
                print("No entries match the specified filters.")
                return
            print(f"Found {len(results)} matching entries:")
            for entry in results:
                self._print_memory_entry(entry)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    def statistics_command(self) -> None:
        """Display statistics from stored calculations (one-shot mode)."""
        stats = self.statistics_service.compute_statistics()
        self._print_statistics_output(stats)

    def export_command(self, filepath: str) -> None:
        """Export history to a JSON file (one-shot mode).

        Args:
            filepath: Path where the JSON file will be saved
        """
        try:
            self.memory_service.export_history(filepath)
            print(f"History exported successfully to {filepath}")
        except Exception as exc:
            print(f"Error exporting history: {exc}", file=sys.stderr)
            sys.exit(1)

    def import_command(self, filepath: str, overwrite: bool = False) -> None:
        """Import history from a JSON file (one-shot mode).

        Args:
            filepath: Path to the JSON file to import
            overwrite: If True, import all entries even if IDs exist; if False (default), skip duplicates
        """
        try:
            count, errors = self.memory_service.import_history(filepath, overwrite=overwrite)
            print(f"Imported {count} entries from {filepath}")
            if errors:
                print(f"Skipped {len(errors)} invalid entries:")
                for error in errors:
                    print(f"  - {error}")
        except (IOError, ValueError) as exc:
            print(f"Error importing history: {exc}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View memory history")
        print(f"  {len(self._MENU) + 2}. View calculation history")
        print(f"  {len(self._MENU) + 3}. Filter calculations")
        print(f"  {len(self._MENU) + 4}. View statistics")
        print(f"  {len(self._MENU) + 5}. Export history to JSON")
        print(f"  {len(self._MENU) + 6}. Import history from JSON")
        print(f"  {len(self._MENU) + 7}. Exit")

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

    def _show_memory_history(self) -> None:
        """Display the memory entry history (both results and errors)."""
        history = self.service.get_memory_history()
        if not history:
            print("\n  No operations recorded yet.\n")
            return
        print()
        for entry in history:
            self._print_memory_entry(entry)
        print()

    def _filter_interactive(self) -> None:
        """Interactive filter dialog."""
        print("\n=== Filter Calculations ===")

        # Get available operations
        valid_ops = self.memory_service.get_valid_operations()
        if not valid_ops:
            print("  No operations recorded yet.\n")
            return

        # Prompt for operation filter
        print(f"\n  Available operations: {', '.join(valid_ops)}")
        op_input = input("  Filter by operation (or press Enter to skip): ").strip()
        operation = op_input if op_input else None

        # Prompt for state filter
        state_input = input("  Filter by state (success/error, or press Enter to skip): ").strip().lower()
        state = None
        if state_input:
            if state_input not in ("success", "error"):
                print("  Invalid state. Skipping state filter.\n")
                state = None
            else:
                state = state_input

        # Perform filtering
        try:
            results = self.memory_service.filter_entries(operation=operation, state=state)
            if not results:
                print("\n  No entries match the specified filters.\n")
                return
            print(f"\n  Found {len(results)} matching entries:\n")
            for entry in results:
                self._print_memory_entry(entry)
        except ValueError as exc:
            print(f"  Error: {exc}\n")

    def _show_statistics(self) -> None:
        """Display statistics in interactive mode."""
        stats = self.statistics_service.compute_statistics()
        self._print_statistics_output(stats)

    def _print_statistics_output(self, stats) -> None:
        """Format and print statistics output."""
        print("\n=== Statistics ===")

        if not stats.operation_counts:
            print("  No operations recorded yet.\n")
            return

        print("\n  Operation Counts:")
        for op, count in sorted(stats.operation_counts.items()):
            print(f"    {op}: {count}")

        print(f"\n  Total errors: {stats.total_errors}")
        print(f"  Error rate: {stats.error_rate_percentage:.2f}%")
        print(f"  Average execution time: {stats.average_execution_time_ms:.2f}ms\n")

    def _print_memory_entry(self, entry: ResultEntry | ErrorEntry) -> None:
        """Format and print a single memory entry."""
        operands_str = " ".join(str(op) for op in entry.operands)
        if isinstance(entry, ResultEntry):
            print(
                f"  #{entry.entry_id}. {entry.operation}({operands_str}) = {entry.result} "
                f"[{entry.timestamp}] ({entry.execution_time_ms:.2f}ms)"
            )
        elif isinstance(entry, ErrorEntry):
            print(
                f"  #{entry.entry_id}. {entry.operation}({operands_str}) -> ERROR: {entry.error_message} "
                f"[{entry.timestamp}] ({entry.execution_time_ms:.2f}ms)"
            )

    def _export_interactive(self) -> None:
        """Interactive export dialog."""
        print("\n=== Export History to JSON ===")
        filepath = input("  Enter file path (e.g., history.json): ").strip()
        if not filepath:
            print("  Export cancelled.\n")
            return

        try:
            self.memory_service.export_history(filepath)
            entries = self.memory_service.retrieve()
            print(f"  Exported {len(entries)} entries to {filepath}\n")
        except Exception as exc:
            print(f"  Error exporting history: {exc}\n")

    def _import_interactive(self) -> None:
        """Interactive import dialog."""
        print("\n=== Import History from JSON ===")
        filepath = input("  Enter file path to import from: ").strip()
        if not filepath:
            print("  Import cancelled.\n")
            return

        overwrite_input = input("  Overwrite existing entries with same ID? (y/n): ").strip().lower()
        overwrite = overwrite_input == 'y'

        try:
            count, errors = self.memory_service.import_history(filepath, overwrite=overwrite)
            print(f"  Imported {count} entries from {filepath}")
            if errors:
                print(f"  Skipped {len(errors)} invalid/duplicate entries:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"    - {error}")
                if len(errors) > 5:
                    print(f"    ... and {len(errors) - 5} more")
            print()
        except (IOError, ValueError) as exc:
            print(f"  Error importing history: {exc}\n")
