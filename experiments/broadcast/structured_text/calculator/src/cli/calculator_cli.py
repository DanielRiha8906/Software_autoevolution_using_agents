import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService
from ..services.query_service import QueryService
from ..services.statistics_service import StatisticsService
from ..protocols import CalculatorUI

if TYPE_CHECKING:
    from ..services.history_manager import HistoryManager


class CalculatorCLI(CalculatorUI):
    """Concrete implementation of the CalculatorUI protocol.

    Provides command-line interface for calculator operations.
    No knowledge of calculation logic or persistence internals.
    """
    _STANDARD_MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
    ]

    _SCIENTIFIC_MENU: list[tuple[Operation, str]] = [
        (Operation.ADD,      "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE,   "Divide"),
        (Operation.SQUARE,   "Square"),
        (Operation.SQRT,     "Square root"),
        (Operation.POWER,    "Power"),
        (Operation.MODULO,   "Modulo"),
        (Operation.SIN,      "Sine"),
        (Operation.COS,      "Cosine"),
        (Operation.TAN,      "Tangent"),
        (Operation.LOG,      "Logarithm (base 10)"),
        (Operation.LN,       "Natural logarithm"),
        (Operation.EXP,      "Exponential (e^x)"),
    ]

    def __init__(
        self,
        service: CalculatorService,
        query_service: Optional[QueryService] = None,
        statistics_service: Optional[StatisticsService] = None,
        history_manager: Optional["HistoryManager"] = None,
        scientific_mode: bool = False,
    ) -> None:
        self.service = service
        self.query_service = query_service
        self.statistics_service = statistics_service
        self.history_manager = history_manager
        self.scientific_mode = scientific_mode
        self._MENU = self._SCIENTIFIC_MENU if scientific_mode else self._STANDARD_MENU

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
            export_opt    = len(self._MENU) + 4
            import_opt    = len(self._MENU) + 5
            exit_opt      = len(self._MENU) + 6

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

            if choice == str(export_opt):
                self._export_history_interactive()
                continue

            if choice == str(import_opt):
                self._import_history_interactive()
                continue

            operation = self._resolve_menu_choice(choice)
            if operation is None:
                print("Invalid choice — try again.\n")
                continue

            a = self._prompt_number("Enter first number: ")
            if a is None:
                continue

            # Scientific operations need only one operand
            scientific_ops = {Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP}
            if operation in scientific_ops:
                b = 0.0
            else:
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
        print(f"  {len(self._MENU) + 4}. Export history")
        print(f"  {len(self._MENU) + 5}. Import history")
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
            if self.scientific_mode:
                op_help = "add, subtract, multiply, divide, square, sqrt, power, modulo, sin, cos, tan, log, ln, exp"
            else:
                op_help = "add, subtract, multiply, divide, square, sqrt, power, modulo"
            op = input(f"Enter operation type ({op_help}): ").strip().lower()
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

    def _export_history_interactive(self) -> None:
        """Interactive menu for exporting calculation history."""
        if self.history_manager is None:
            print("  History manager not available.\n")
            return

        filepath = input("Enter file path to export to: ").strip()
        if not filepath:
            print("  Export cancelled.\n")
            return

        try:
            count, errors = self.history_manager.export_to_file(filepath)
            if errors:
                print(f"\n  Warning: {len(errors)} entries could not be exported:")
                for err in errors[:3]:
                    print(f"    - {err}")
                if len(errors) > 3:
                    print(f"    ... and {len(errors) - 3} more\n")
            print(f"  Successfully exported {count} entries to {filepath}\n")
        except IOError as exc:
            print(f"\n  Error exporting history: {exc}\n")

    def _import_history_interactive(self) -> None:
        """Interactive menu for importing calculation history."""
        if self.history_manager is None:
            print("  History manager not available.\n")
            return

        filepath = input("Enter file path to import from: ").strip()
        if not filepath:
            print("  Import cancelled.\n")
            return

        print("\n  Import mode:")
        print("    1. Append to existing records (default)")
        print("    2. Replace existing records")
        choice = input("  Choose mode (1 or 2): ").strip()
        mode = "replace" if choice == "2" else "append"

        if mode == "replace":
            confirm = input("  WARNING: This will replace all existing records. Continue? (y/n): ").strip().lower()
            if confirm != "y":
                print("  Import cancelled.\n")
                return

        try:
            count, errors = self.history_manager.import_from_file(filepath, choice=mode)

            if errors:
                print(f"\n  Warning: {len(errors)} entries could not be imported:")
                for err in errors[:3]:
                    print(f"    - {err}")
                if len(errors) > 3:
                    print(f"    ... and {len(errors) - 3} more")

            if mode == "replace":
                print(f"\n  Successfully replaced history with {count} imported entries\n")
            else:
                print(f"\n  Successfully appended {count} entries to history\n")
        except FileNotFoundError as exc:
            print(f"\n  Error: {exc}\n")
        except (IOError, ValueError) as exc:
            print(f"\n  Error importing history: {exc}\n")
