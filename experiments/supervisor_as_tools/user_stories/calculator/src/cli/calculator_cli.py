import sys
from typing import TYPE_CHECKING

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService

if TYPE_CHECKING:
    from ..services.memory_service import MemoryService
    from ..services.statistics_service import StatisticsService


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
        (Operation.SIN,      "Sin"),
        (Operation.COS,      "Cos"),
        (Operation.TAN,      "Tan"),
        (Operation.LOG,      "Log"),
        (Operation.LN,       "Ln"),
        (Operation.EXP,      "Exp"),
    ]

    def __init__(
        self,
        service: CalculatorService,
        memory_service: "MemoryService | None" = None,
        statistics_service: "StatisticsService | None" = None,
    ) -> None:
        self.service = service
        self.memory_service = memory_service
        self.statistics_service = statistics_service

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_interactive(self) -> None:
        print("=== Calculator ===")
        while True:
            self._print_menu()
            choice = input("Choose option: ").strip()

            history_opt    = len(self._MENU) + 1
            memory_opt     = len(self._MENU) + 2
            statistics_opt = len(self._MENU) + 3
            exit_opt       = len(self._MENU) + 4

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(memory_opt):
                self._show_memory()
                continue

            if choice == str(statistics_opt):
                self._show_statistics()
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

    def show_filtered_memory_cli(self, operation_name: str | None = None, success: bool | None = None) -> None:
        """Display filtered memory entries to the console.

        Args:
            operation_name: Optional operation name to filter by.
            success: Optional success status to filter by.
        """
        if not self.memory_service:
            print("Memory service is not available.", file=sys.stderr)
            return
        entries = self.memory_service.filter(operation_name, success)
        if not entries:
            print("No matching memory entries.")
            return
        for entry in entries:
            result_str = str(entry.result) if entry.success else entry.error_message
            print(f"[ID: {entry.entry_id[:8]}...] {entry.operation_name}({entry.operand_a}, {entry.operand_b}) -> {result_str} | {entry.execution_time_ms}ms")

    def _show_memory(self) -> None:
        if not self.memory_service:
            print("\n  Memory service is not available.\n")
            return
        self._show_memory_filter_submenu()

    def _show_memory_filter_submenu(self) -> None:
        """Display interactive memory filter submenu."""
        while True:
            print("\n  Memory Filter Options:")
            print("    (1) View all")
            print("    (2) Filter by operation")
            print("    (3) Filter by success")
            print("    (4) Filter by error")
            print("    (5) Export memory")
            print("    (6) Import memory")
            print("    (7) Back")
            choice = input("  Choose option: ").strip()

            if choice == "1":
                entries = self.memory_service.get_all_entries()
                self._display_memory_entries(entries)
            elif choice == "2":
                operation = input("  Enter operation name (add/subtract/multiply/divide/square/sqrt/power/modulo/sin/cos/tan/log/ln/exp): ").strip()
                if operation:
                    entries = self.memory_service.filter_by_operation(operation)
                    self._display_memory_entries(entries)
            elif choice == "3":
                entries = self.memory_service.filter_by_success(True)
                self._display_memory_entries(entries)
            elif choice == "4":
                entries = self.memory_service.filter_by_success(False)
                self._display_memory_entries(entries)
            elif choice == "5":
                self._export_memory_interactive()
            elif choice == "6":
                self._import_memory_interactive()
            elif choice == "7":
                break
            else:
                print("  Invalid choice — try again.")

    def _display_memory_entries(self, entries: list) -> None:
        """Display a list of memory entries."""
        if not entries:
            print("\n  No matching memory entries.\n")
            return
        print()
        for i, entry in enumerate(entries, 1):
            result_str = str(entry.result) if entry.success else entry.error_message
            print(f"  {i}. [ID: {entry.entry_id[:8]}...] {entry.operation_name}({entry.operand_a}, {entry.operand_b}) -> {result_str} | {entry.execution_time_ms}ms")
        print()

    def _show_statistics(self) -> None:
        """Display calculation statistics."""
        if not self.statistics_service:
            print("\n  Statistics service is not available.\n")
            return
        stats = self.statistics_service.generate()
        print("\n=== Calculation Statistics ===\n")
        print("Operations performed:")
        print(f"  Add:      {stats.operation_counts['add']}")
        print(f"  Subtract: {stats.operation_counts['subtract']}")
        print(f"  Multiply: {stats.operation_counts['multiply']}")
        print(f"  Divide:   {stats.operation_counts['divide']}")
        print(f"  Square:   {stats.operation_counts['square']}")
        print(f"  Sqrt:     {stats.operation_counts['sqrt']}")
        print(f"  Power:    {stats.operation_counts['power']}")
        print(f"  Modulo:   {stats.operation_counts['modulo']}")
        print(f"  Sin:      {stats.operation_counts['sin']}")
        print(f"  Cos:      {stats.operation_counts['cos']}")
        print(f"  Tan:      {stats.operation_counts['tan']}")
        print(f"  Log:      {stats.operation_counts['log']}")
        print(f"  Ln:       {stats.operation_counts['ln']}")
        print(f"  Exp:      {stats.operation_counts['exp']}")
        print(f"\nTotal errors: {stats.total_errors}")
        print(f"Error rate: {stats.error_rate:.1f}%")
        print(f"Average execution time: {stats.avg_execution_time_ms:.2f} ms\n")

    def _export_memory_interactive(self) -> None:
        """Interactively export memory entries to a file."""
        if not self.memory_service:
            print("\n  Memory service is not available.\n")
            return

        output_path = input("  Enter output file path: ").strip()
        if not output_path:
            print("  Export cancelled.\n")
            return

        try:
            count = self.memory_service.storage.export_memory_entries(output_path)
            print(f"\n  Exported {count} memory entries to {output_path}\n")
        except (IOError, OSError) as exc:
            print(f"\n  Error exporting memory entries: {exc}\n", file=sys.stderr)

    def _import_memory_interactive(self) -> None:
        """Interactively import memory entries from a file."""
        if not self.memory_service:
            print("\n  Memory service is not available.\n")
            return

        input_path = input("  Enter input file path: ").strip()
        if not input_path:
            print("  Import cancelled.\n")
            return

        overwrite_str = input("  Overwrite existing entries? (yes/no): ").strip().lower()
        overwrite = overwrite_str in ("yes", "y")

        try:
            imported, skipped = self.memory_service.storage.import_memory_entries(
                input_path, overwrite=overwrite
            )
            print(f"\n  Imported {imported} memory entries (skipped {skipped} invalid entries)\n")
        except (FileNotFoundError, IOError, OSError) as exc:
            print(f"\n  Error importing memory entries: {exc}\n", file=sys.stderr)
        except Exception as exc:
            print(f"\n  Unexpected error during import: {exc}\n", file=sys.stderr)
