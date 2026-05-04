import sys

from ..models.operation import Operation
from ..models.memory_entry import ErrorEntry, ResultEntry
from ..services.calculator_service import CalculatorService
from ..services.memory_store import MemoryStore
from ..services.statistics_service import StatisticsService


class CalculatorCLI:
    _STANDARD_OPS: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    _SCIENTIFIC_OPS: list[tuple[Operation, str]] = [
        (Operation.SIN,      "Sine"),
        (Operation.COS,      "Cosine"),
        (Operation.TAN,      "Tangent"),
        (Operation.LOG,      "Logarithm (base 10)"),
        (Operation.LN,       "Natural logarithm"),
        (Operation.EXP,      "Exponential (e^x)"),
    ]

    def __init__(self, service: CalculatorService, memory_store: MemoryStore) -> None:
        self.service = service
        self.memory_store = memory_store
        self.statistics_service = StatisticsService(memory_store.get_memory_service())
        self.mode = "standard"  # "standard" or "scientific"
        self._menu = self._STANDARD_OPS

    @property
    def memory_service(self):
        """Backward compatibility property returning the underlying memory service.

        Returns:
            The MemoryService instance from the memory store
        """
        return self.memory_store.get_memory_service()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            # Calculate menu option indices
            num_ops = len(self._menu)
            mode_opt           = num_ops + 1
            memory_history_opt = num_ops + 2
            history_opt        = num_ops + 3
            filter_opt         = num_ops + 4
            statistics_opt     = num_ops + 5
            export_opt         = num_ops + 6
            import_opt         = num_ops + 7
            exit_opt           = num_ops + 8

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(mode_opt):
                self._toggle_mode()
                continue

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

            # Prompt for operands based on arity
            a = self._prompt_number("Enter first number: ")
            if a is None:
                continue

            if operation.is_unary():
                # Unary operation: don't ask for second operand
                try:
                    result = self.service.perform(operation, a, None)
                    print(f"\n  Result: {result}\n")
                except ValueError as exc:
                    print(f"\n  Error: {exc}\n")
            else:
                # Binary operation: ask for second operand
                b = self._prompt_number("Enter second number: ")
                if b is None:
                    continue
                try:
                    result = self.service.perform(operation, a, b)
                    print(f"\n  Result: {result}\n")
                except ValueError as exc:
                    print(f"\n  Error: {exc}\n")

    def run_command(self, operation_str: str, a: float, b: float | None = None) -> None:
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
        entries = self.memory_store.retrieve()
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
            self.memory_store.store(entry)
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
            results = self.memory_store.filter_entries(operation=operation, state=state)
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
            self.memory_store.export_history(filepath)
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
            count, errors = self.memory_store.import_history(filepath, overwrite=overwrite)
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
        print(f"\nOperations ({self.mode.capitalize()} Mode):")
        for i, (_, label) in enumerate(self._menu, 1):
            print(f"  {i}. {label}")
        num_ops = len(self._menu)
        print(f"  {num_ops + 1}. Toggle mode (currently {self.mode})")
        print(f"  {num_ops + 2}. View memory history")
        print(f"  {num_ops + 3}. View calculation history")
        print(f"  {num_ops + 4}. Filter calculations")
        print(f"  {num_ops + 5}. View statistics")
        print(f"  {num_ops + 6}. Export history to JSON")
        print(f"  {num_ops + 7}. Import history from JSON")
        print(f"  {num_ops + 8}. Exit")

    def _toggle_mode(self) -> None:
        """Toggle between standard and scientific mode."""
        if self.mode == "standard":
            self.mode = "scientific"
            self._menu = self._STANDARD_OPS + self._SCIENTIFIC_OPS
            print("\nSwitched to scientific mode.\n")
        else:
            self.mode = "standard"
            self._menu = self._STANDARD_OPS
            print("\nSwitched to standard mode.\n")

    def _resolve_menu_choice(self, choice: str) -> Operation | None:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self._menu):
                return self._menu[idx][0]
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
        valid_ops = self.memory_store.get_valid_operations()
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
            results = self.memory_store.filter_entries(operation=operation, state=state)
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
            self.memory_store.export_history(filepath)
            entries = self.memory_store.retrieve()
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
            count, errors = self.memory_store.import_history(filepath, overwrite=overwrite)
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
