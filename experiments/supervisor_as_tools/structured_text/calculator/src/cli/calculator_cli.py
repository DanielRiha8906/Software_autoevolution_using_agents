import sys

from ..models.operation import Operation
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

    def __init__(
        self,
        service: CalculatorService,
        memory_service: MemoryService | None = None,
    ) -> None:
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

            # Calculate option numbers based on menu availability
            history_opt = len(self._MENU) + 1
            exit_opt = history_opt + 1

            # Memory options only available if memory_service is provided
            if self.memory_service is not None:
                memory_opt = history_opt + 2
                summary_opt = history_opt + 3
                exit_opt = history_opt + 4

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            # Only handle memory options if memory_service is available
            if self.memory_service is not None:
                if choice == str(memory_opt):
                    self.show_memory_list()
                    continue

                if choice == str(summary_opt):
                    self.show_memory_summary()
                    continue

            operation = self._resolve_menu_choice(choice)
            if operation is None:
                print("Invalid choice — try again.\n")
                continue

            a = self._prompt_number("Enter first number: ")
            if a is None:
                continue

            # Handle unary operations (only need one operand)
            if operation in (Operation.SQUARE, Operation.SQRT):
                b = 0
            else:
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
            # For unary operations, b should be unused; default to 0 if not provided
            if b is None:
                b = 0
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

        # Only show memory options if memory_service is available
        if self.memory_service is not None:
            print(f"  {len(self._MENU) + 2}. View memory")
            print(f"  {len(self._MENU) + 3}. Memory summary")
            print(f"  {len(self._MENU) + 4}. Exit")
        else:
            print(f"  {len(self._MENU) + 2}. Exit")

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

    # ------------------------------------------------------------------
    # Memory-related public methods
    # ------------------------------------------------------------------

    def show_memory_list(self) -> None:
        if not self.memory_service:
            print("\n  Memory service not available.\n")
            return

        entries = self.memory_service.retrieve_all()
        if not entries:
            print("\n  No memory entries recorded yet.\n")
            return

        print()
        for i, entry in enumerate(entries, 1):
            status = "✓" if entry.success else "✗"
            result_str = (
                f"= {entry.result}"
                if entry.success
                else f"error: {entry.error_message}"
            )
            print(
                f"  {i}. [{status}] {entry.operation} "
                f"({entry.operand_a}, {entry.operand_b}) {result_str}"
            )
            print(f"     ID: {entry.id[:8]}... | {entry.timestamp}")
        print()

    def show_memory_detail(self, entry_id: str) -> None:
        if not self.memory_service:
            print("\n  Memory service not available.\n")
            return

        entry = self.memory_service.retrieve_by_id(entry_id)
        if not entry:
            print(f"\n  Entry not found: {entry_id}\n")
            return

        print()
        print(f"  Operation: {entry.operation}")
        print(f"  ID: {entry.id}")
        print(f"  Operands: {entry.operand_a}, {entry.operand_b}")
        print(f"  Status: {'Success' if entry.success else 'Failure'}")
        if entry.success:
            print(f"  Result: {entry.result}")
        else:
            print(f"  Error: {entry.error_message}")
        print(f"  Execution time: {entry.execution_time_ms:.2f} ms")
        print(f"  Timestamp: {entry.timestamp}")
        print()

    def show_memory_failures(self) -> None:
        if not self.memory_service:
            print("\n  Memory service not available.\n")
            return

        failures = self.memory_service.retrieve_failures()
        if not failures:
            print("\n  No failures recorded.\n")
            return

        print()
        for i, entry in enumerate(failures, 1):
            print(f"  {i}. {entry.operation} ({entry.operand_a}, {entry.operand_b})")
            print(f"     Error: {entry.error_message}")
            print(f"     ID: {entry.id[:8]}... | {entry.timestamp}")
        print()

    def show_memory_summary(self) -> None:
        if not self.memory_service:
            print("\n  Memory service not available.\n")
            return

        total = self.memory_service.count()
        if total == 0:
            print("\n  No memory entries recorded yet.\n")
            return

        status_counts = self.memory_service.count_by_status()
        op_counts = self.memory_service.count_by_operation()

        print()
        print(f"  Total entries: {total}")
        print(
            f"  Success: {status_counts['success']} | "
            f"Failure: {status_counts['failure']}"
        )
        print()
        print("  By operation:")
        for op, count in sorted(op_counts.items()):
            print(f"    {op}: {count}")
        print()

    def clear_memory_confirm(self) -> None:
        if not self.memory_service:
            print("\n  Memory service not available.\n")
            return

        confirm = input("Clear all memory entries? (yes/no): ").strip().lower()
        if confirm == "yes":
            self.memory_service.clear()
            print("  Memory cleared.\n")
        else:
            print("  Cancelled.\n")
