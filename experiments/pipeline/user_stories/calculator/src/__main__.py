import argparse
import sys
from pathlib import Path
from json import JSONDecodeError

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
from .services.statistics_service import StatisticsService
from .services.import_export_service import ImportExportService
from .services.memory.history_filter import OperationFilter, StateFilter
from .storage.json_storage import JsonStorage
from .cli.calculator_cli import CalculatorCLI
from .cli.commands.calculate_command import CalculateCommand
from .cli.commands.history_command import HistoryCommand
from .cli.commands.statistics_command import StatisticsCommand
from .cli.commands.filter_command import FilterCommand
from .cli.commands.export_command import ExportCommand
from .cli.commands.import_command import ImportCommand
from .cli.formatters.memory_entry_formatter import MemoryEntryListFormatter


def _build_services() -> tuple[CalculatorService, MemoryService, StatisticsService, ImportExportService]:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    storage = JsonStorage(storage_path)
    memory_service = MemoryService(storage)
    calculator_service = CalculatorService(Calculator(), memory_service)
    statistics_service = StatisticsService(memory_service)
    import_export_service = ImportExportService(memory_service)
    return calculator_service, memory_service, statistics_service, import_export_service


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo,sin,cos,tan,log,ln,exp} A B] [--show-history]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo | sin | cos | tan | log | ln | exp)",
    )
    parser.add_argument(
        "--show-history",
        action="store_true",
        help="Display all calculation history",
    )
    parser.add_argument(
        "--filter-operation",
        metavar="OPS",
        help="Filter history by operation(s) (comma-separated names: add,subtract,multiply,etc.)",
    )
    parser.add_argument(
        "--filter-state",
        metavar="STATE",
        choices=["success", "error", "both"],
        help="Filter history by result state: success (no error), error (failed), or both",
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Display calculation statistics",
    )
    parser.add_argument(
        "--export",
        metavar="FILEPATH",
        help="Export calculation history to a JSON file",
    )
    parser.add_argument(
        "--import",
        metavar="FILEPATH",
        dest="import_file",
        help="Import calculation history from a JSON file (appends by default)",
    )
    parser.add_argument(
        "--import-mode",
        choices=["merge", "replace"],
        default="merge",
        help="When importing: 'merge' (append to existing) or 'replace' (overwrite all)",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )

    args = parser.parse_args()
    calculator_service, memory_service, statistics_service, import_export_service = _build_services()
    cli = CalculatorCLI(calculator_service, statistics_service, import_export_service, memory_service)

    # Handle --export flag
    if args.export:
        cmd = ExportCommand(import_export_service, args.export)
        cmd.execute()
        sys.exit(0)

    # Handle --import flag
    if args.import_file:
        cmd = ImportCommand(import_export_service, args.import_file, mode=args.import_mode)
        cmd.execute()
        sys.exit(0)

    # Handle --statistics flag
    if args.statistics:
        cmd = StatisticsCommand(statistics_service)
        cmd.execute()
        sys.exit(0)

    # Handle --show-history (with optional filters)
    if args.show_history or args.filter_operation or args.filter_state:
        # If no filters, use HistoryCommand
        if not args.filter_operation and not args.filter_state:
            cmd = HistoryCommand(memory_service, formatter=MemoryEntryListFormatter())
            cmd.execute()
            sys.exit(0)

        # Parse and validate filters
        filters: list = []

        # Parse filter-operation if provided
        if args.filter_operation:
            operations = [op.strip() for op in args.filter_operation.split(",")]
            # Validate operation names
            for op_name in operations:
                try:
                    Operation.from_string(op_name)
                except ValueError as exc:
                    parser.error(str(exc))
            filters.append(OperationFilter(operations))

        # Use filter-state if provided
        if args.filter_state:
            filters.append(StateFilter(args.filter_state))

        # Display filtered history using FilterCommand
        cmd = FilterCommand(memory_service, filters, formatter=MemoryEntryListFormatter())
        cmd.execute()
        sys.exit(0)

    if args.operation:
        if len(args.operands) != 2:
            parser.error("Exactly two operands are required when using --operation")
        try:
            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1])
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cmd = CalculateCommand(calculator_service, args.operation, a, b)
        cmd.execute()
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
