import sys
from typing import TYPE_CHECKING

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService

if TYPE_CHECKING:
    from ..services.memory_service import MemoryService


class CalculatorCLI:
    _MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Sqrt"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    def __init__(self, service: CalculatorService, memory_service: "MemoryService | None" = None) -> None:
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
            exit_opt    = len(self._MENU) + 3

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(memory_opt):
                self._show_memory()
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
        print(f"  {len(self._MENU) + 2}. View memory entries")
        print(f"  {len(self._MENU) + 3}. Exit")

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

    def show_memory_cli(self) -> None:
        if not self.memory_service:
            print("Memory service is not available.", file=sys.stderr)
            return
        entries = self.memory_service.get_all_entries()
        if not entries:
            print("No memory entries recorded yet.")
            return
        for entry in entries:
            result_str = str(entry.result) if entry.success else entry.error_message
            print(f"[ID: {entry.entry_id[:8]}...] {entry.operation_name}({entry.operand_a}, {entry.operand_b}) -> {result_str} | {entry.execution_time_ms}ms")

    def _show_memory(self) -> None:
        if not self.memory_service:
            print("\n  Memory service is not available.\n")
            return
        entries = self.memory_service.get_all_entries()
        if not entries:
            print("\n  No memory entries recorded yet.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            result_str = str(entry.result) if entry.success else entry.error_message
            print(f"  {i}. [ID: {entry.entry_id[:8]}...] {entry.operation_name}({entry.operand_a}, {entry.operand_b}) -> {result_str} | {entry.execution_time_ms}ms")
        print()
