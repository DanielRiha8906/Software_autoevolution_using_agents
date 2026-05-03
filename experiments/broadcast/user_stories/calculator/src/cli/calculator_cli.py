import sys

from ..models.operation import Operation
from ..models.memory_entry import ErrorEntry, ResultEntry
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService


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
            exit_opt           = len(self._MENU) + 4

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
        print(f"  {len(self._MENU) + 4}. Exit")

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
