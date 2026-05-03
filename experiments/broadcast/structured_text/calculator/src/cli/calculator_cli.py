import sys
from typing import Optional

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService
from ..services.query_service import QueryService
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

    def __init__(
        self,
        service: CalculatorService,
        query_service: Optional[QueryService] = None,
        statistics_service: Optional[StatisticsService] = None,
    ) -> None:
        self.service = service
        self.query_service = query_service
        self.statistics_service = statistics_service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt   = len(self._MENU) + 1
            query_opt     = len(self._MENU) + 2
            stats_opt     = len(self._MENU) + 3
            exit_opt      = len(self._MENU) + 4

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(query_opt):
                if self.query_service is not None:
                    self._query_interactive()
                else:
                    print("  Query service not available.\n")
                continue

            if choice == str(stats_opt):
                if self.statistics_service is not None:
                    self._show_statistics()
                else:
                    print("  Statistics service not available.\n")
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
        print(f"  {len(self._MENU) + 2}. Query calculations")
        print(f"  {len(self._MENU) + 3}. View statistics")
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

    def _query_interactive(self) -> None:
        """Interactive query menu."""
        if self.query_service is None:
            print("  Query service not available.\n")
            return

        print("\n=== Query Calculations ===")
        print("  1. Query by operation type")
        print("  2. Query by result state")
        print("  3. Query with both filters")
        print("  4. Back to main menu")
        choice = input("Choose option: ").strip()

        if choice == "1":
            op = input("Enter operation type (add, subtract, multiply, divide, square, sqrt, power, modulo): ").strip().lower()
            if op:
                results = self.query_service.query_by_operation(op)
                print("\n" + self.query_service.format_results(results) + "\n")
        elif choice == "2":
            state = input("Enter result state (success, failed, all): ").strip().lower()
            if state:
                try:
                    results = self.query_service.query_by_state(state)
                    print("\n" + self.query_service.format_results(results) + "\n")
                except ValueError as exc:
                    print(f"\n  Error: {exc}\n")
        elif choice == "3":
            op = input("Enter operation type (or press Enter to skip): ").strip().lower() or None
            state = input("Enter result state (success, failed, all) [default: all]: ").strip().lower() or "all"
            try:
                results = self.query_service.query(operation_type=op, result_state=state)
                print("\n" + self.query_service.format_results(results) + "\n")
            except ValueError as exc:
                print(f"\n  Error: {exc}\n")
        elif choice == "4":
            pass
        else:
            print("  Invalid choice.\n")

    def _show_statistics(self) -> None:
        """Display calculation statistics."""
        if self.statistics_service is None:
            print("  Statistics service not available.\n")
            return

        report = self.statistics_service.compute_statistics()
        print("\n=== Calculation Statistics ===")
        print(f"  Total operations: {report.total_operations}")
        print(f"  Operations by type: {report.operation_count}")
        print(f"  Total errors: {report.total_errors}")
        print(f"  Error frequency: {report.error_frequency}")
        print(f"  Error rate: {report.error_rate:.2%}")
        print(f"  Average execution time: {report.average_execution_time_ms:.2f}ms")
        print(f"  Min execution time: {report.min_execution_time_ms:.2f}ms")
        print(f"  Max execution time: {report.max_execution_time_ms:.2f}ms\n")
