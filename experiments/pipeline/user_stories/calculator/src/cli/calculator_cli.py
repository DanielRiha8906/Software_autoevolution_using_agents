import sys
from json import JSONDecodeError

from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from ..services.calculator_service import CalculatorService
from ..services.statistics_service import StatisticsService
from ..services.import_export_service import ImportExportService


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

    def __init__(
        self,
        service: CalculatorService,
        statistics_service: StatisticsService,
        import_export_service: ImportExportService | None = None,
    ) -> None:
        self.service = service
        self.statistics_service = statistics_service
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
            filter_opt  = len(self._MENU) + 2
            statistics_opt = len(self._MENU) + 3
            export_opt  = len(self._MENU) + 4
            import_opt  = len(self._MENU) + 5
            exit_opt    = len(self._MENU) + 6

            if choice == str(exit_opt):
                print("Goodbye!")
                break

            if choice == str(history_opt):
                self._show_history()
                continue

            if choice == str(filter_opt):
                self._run_filter_menu()
                continue

            if choice == str(statistics_opt):
                self._show_statistics()
                continue

            if choice == str(export_opt):
                self._export_history()
                continue

            if choice == str(import_opt):
                self._import_history()
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

            result = self.service.perform(operation, a, b)
            if result.error:
                print(f"\n  Error: {result.error}\n")
            else:
                print(f"\n  Result: {result}\n")

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        try:
            operation = Operation.from_string(operation_str)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

        result = self.service.perform(operation, a, b)
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)
        else:
            print(result)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_menu(self) -> None:
        print("\nOperations:")
        for i, (_, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label}")
        print(f"  {len(self._MENU) + 1}. View history")
        print(f"  {len(self._MENU) + 2}. Filter history")
        print(f"  {len(self._MENU) + 3}. Show statistics")
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
            if entry.error:
                print(f"  {i}. {entry.operation} ({entry.operand_a}, {entry.operand_b}) = ERROR: {entry.error}")
            else:
                print(f"  {i}. {entry}  [{entry.timestamp}]")
        print()

    def _run_filter_menu(self) -> None:
        """Run the filter history submenu."""
        # Prompt for operation selection
        operations = self._prompt_operation_selection()
        if operations is None:
            return  # User cancelled

        # Prompt for state selection
        state = self._prompt_state_selection()
        if state is None:
            return  # User cancelled

        # Show filtered results
        self._show_filtered_history(operations, state)

    def _prompt_operation_selection(self) -> list[str] | None:
        """Prompt user to select operations to filter by.

        Returns:
            List of selected operation names, or None if user cancelled.
        """
        print("\nSelect operations to filter by (enter comma-separated numbers or 'all'):")
        for i, (op, label) in enumerate(self._MENU, 1):
            print(f"  {i}. {label} ({op.value})")
        print("  (or 'all' to include all operations)")

        raw_input = input("Enter selection: ").strip().lower()

        if raw_input == "all" or raw_input == "":
            return None  # None means all operations

        # Parse comma-separated numbers
        selected_ops = []
        try:
            indices = [s.strip() for s in raw_input.split(",")]
            for idx_str in indices:
                idx = int(idx_str) - 1
                if 0 <= idx < len(self._MENU):
                    selected_ops.append(self._MENU[idx][0].value)
                else:
                    print(f"Invalid selection: {idx + 1}")
                    return None
        except ValueError:
            print("Invalid input — please enter comma-separated numbers or 'all'.")
            return None

        return selected_ops if selected_ops else None

    def _prompt_state_selection(self) -> str | None:
        """Prompt user to select result state filter.

        Returns:
            One of 'success', 'error', or 'both', or None if user cancelled.
        """
        print("\nSelect result state:")
        print("  1. Success only")
        print("  2. Error only")
        print("  3. Both")

        raw_input = input("Enter selection (1-3): ").strip()

        state_map = {"1": "success", "2": "error", "3": "both"}
        if raw_input in state_map:
            return state_map[raw_input]

        print("Invalid selection — please enter 1, 2, or 3.")
        return None

    def _show_filtered_history(
        self,
        operations: list[str] | None,
        state: str | None,
    ) -> None:
        """Display filtered history.

        Args:
            operations: List of operation names to filter by, or None for all.
            state: One of 'success', 'error', or 'both', or None for both.
        """
        filtered = self.service.filter_history(operations=operations, state=state)

        if not filtered:
            print("\n  No matching calculations found.\n")
            return

        print()
        for i, entry in enumerate(filtered, 1):
            if entry.error:
                print(f"  {i}. {entry.operation} ({entry.operand_a}, {entry.operand_b}) = ERROR: {entry.error}")
            else:
                print(f"  {i}. {entry}  [{entry.timestamp}]")
        print()

    def _show_statistics(self) -> None:
        """Display calculation statistics."""
        stats = self.statistics_service.calculate_statistics()
        print()
        print("  === Calculation Statistics ===")
        print(f"  Total Calculations: {stats.total_calculations}")
        print(f"  Total Errors: {stats.total_errors}")
        print(f"  Error Rate: {stats.error_rate_percent}%")
        print(f"  Average Execution Time: {stats.average_execution_time_ms} ms")
        print("  Operations Count:")
        if stats.operations_count:
            for op_name in sorted(stats.operations_count.keys()):
                count = stats.operations_count[op_name]
                print(f"    {op_name}: {count}")
        else:
            print("    (none)")
        print()

    def _export_history(self) -> None:
        """Interactive menu option: prompt for export filepath, call service."""
        if self.import_export_service is None:
            print("\n  Export service not available.\n")
            return

        filepath = input("Enter export file path (must end with .json): ").strip()
        if not filepath:
            print("  Export cancelled.\n")
            return

        try:
            result = self.import_export_service.export_history(filepath)
            print(f"\n  Successfully exported {result['exported_count']} entries to {result['file_path']}\n")
        except (ValueError, OSError) as e:
            print(f"\n  Export error: {e}\n")

    def _import_history(self, filepath: str | None = None, mode: str = "merge") -> None:
        """Interactive menu option: prompt for import filepath, call service, show results."""
        if self.import_export_service is None:
            print("\n  Import service not available.\n")
            return

        if filepath is None:
            filepath = input("Enter import file path (must end with .json): ").strip()
            if not filepath:
                print("  Import cancelled.\n")
                return

            # Ask for mode
            print("\nSelect import mode:")
            print("  1. Merge (append to existing)")
            print("  2. Replace (overwrite all)")
            mode_choice = input("Enter selection (1-2): ").strip()

            if mode_choice == "2":
                mode = "replace"
            elif mode_choice != "1" and mode_choice != "":
                print("  Invalid selection — defaulting to merge.\n")
                mode = "merge"

        try:
            result = self.import_export_service.import_history(filepath, mode=mode)
            self._show_import_result(result)
        except (ValueError, OSError, JSONDecodeError) as e:
            print(f"\n  Import error: {e}\n")

    def _show_import_result(self, result: dict) -> None:
        """Display import operation results (counts, skipped entries, etc.)."""
        print()
        print(f"  Imported {result['imported_count']} entries")
        if result['skipped_count'] > 0:
            print(f"  Skipped {result['skipped_count']} entries:")
            print(f"    - {result['duplicates_count']} duplicates")
            print(f"    - {result['invalid_count']} invalid entries")
        print()
