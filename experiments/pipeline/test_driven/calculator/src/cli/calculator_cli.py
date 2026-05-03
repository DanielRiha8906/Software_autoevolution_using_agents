import sys

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService
from ..services.import_export_service import ImportExportService
from ..services.memory_service import MemoryService


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

    def __init__(self, service: CalculatorService, memory_service: MemoryService | None = None, import_export_service: ImportExportService | None = None) -> None:
        self.service = service
        self.memory_service = memory_service
        self.import_export_service = import_export_service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt = len(self._MENU) + 1
            export_opt  = len(self._MENU) + 2
            import_opt  = len(self._MENU) + 3
            exit_opt    = len(self._MENU) + 4

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(export_opt):
                self._prompt_and_export()
                continue

            if choice == str(import_opt):
                self._prompt_and_import()
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

    def export_memory(self, filepath: str) -> None:
        """Export memory to JSON file.

        Args:
            filepath: Path to write JSON file to.
        """
        if not self.memory_service or not self.import_export_service:
            print("Memory services not available", file=sys.stderr)
            return
        try:
            self.import_export_service.export(self.memory_service, filepath)
            print(f"Memory exported to {filepath}")
        except Exception as exc:
            print(f"Error exporting memory: {exc}", file=sys.stderr)

    def import_memory(self, filepath: str) -> None:
        """Import memory from JSON file.

        Args:
            filepath: Path to read JSON file from.
        """
        if not self.memory_service or not self.import_export_service:
            print("Memory services not available", file=sys.stderr)
            return
        try:
            self.import_export_service.import_from(self.memory_service, filepath)
            print(f"Memory imported from {filepath}")
        except Exception as exc:
            print(f"Error importing memory: {exc}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View history")
        print(f"  {len(self._MENU) + 2}. Export memory")
        print(f"  {len(self._MENU) + 3}. Import memory")
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

    def _prompt_and_export(self) -> None:
        filepath = input("Enter filepath to export to: ").strip()
        if filepath:
            self.export_memory(filepath)
        print()

    def _prompt_and_import(self) -> None:
        filepath = input("Enter filepath to import from: ").strip()
        if filepath:
            self.import_memory(filepath)
        print()
