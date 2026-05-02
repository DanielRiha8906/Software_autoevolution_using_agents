import sys

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService


class CalculatorCLI:
    _MENU: list[tuple[Operation, str, int]] = [
        (Operation.ADD,      "Add", 2),
        (Operation.SUBTRACT, "Subtract", 2),
        (Operation.MULTIPLY, "Multiply", 2),
        (Operation.DIVIDE,   "Divide", 2),
        (Operation.SQUARE,   "Square", 1),
        (Operation.SQRT,     "Square Root", 1),
        (Operation.POWER,    "Power", 2),
        (Operation.MODULO,   "Modulo", 2),
    ]

    def __init__(self, service: CalculatorService) -> None:
        self.service = service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt = len(self._MENU) + 1
            exit_opt    = len(self._MENU) + 2

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            menu_entry = self._resolve_menu_choice(choice)
            if menu_entry is None:
                print("Invalid choice — try again.\n")
                continue

            operation, _, arity = menu_entry
            operands = []

            # Prompt for operands based on arity
            for i in range(arity):
                if i == 0:
                    prompt = "Enter first number: "
                else:
                    prompt = "Enter second number: "
                operand = self._prompt_number(prompt)
                if operand is None:
                    break
                operands.append(operand)

            if len(operands) != arity:
                continue

            try:
                result = self.service.perform(operation, *operands)
                print(f"\n  Result: {result}\n")
            except ValueError as exc:
                print(f"\n  Error: {exc}\n")

    def run_command(self, operation_str: str, *operands: float) -> None:
        try:
            operation = Operation.from_string(operation_str)
            result = self.service.perform(operation, *operands)
            print(result)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label, _) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View history")
        print(f"  {len(self._MENU) + 2}. Exit")

    def _resolve_menu_choice(self, choice: str) -> tuple[Operation, str, int] | None:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self._MENU):
                return self._MENU[idx]
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
