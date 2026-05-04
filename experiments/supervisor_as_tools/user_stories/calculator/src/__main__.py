import argparse
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
from .services.statistics_service import StatisticsService
from .storage.json_storage import JsonStorage
from .cli.calculator_cli import CalculatorCLI
from .gui.calculator_window import CalculatorWindow


def _build_service() -> tuple[CalculatorService, MemoryService, StatisticsService]:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    calculator_service = CalculatorService(Calculator(), JsonStorage(storage_path))
    memory_service = MemoryService(calculator_service, JsonStorage(storage_path))
    statistics_service = StatisticsService(memory_service)
    return calculator_service, memory_service, statistics_service


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively, pass --operation for one-shot use, or use --gui for graphical interface",
        usage="python -m src [--gui] [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo,sin,cos,tan,log,ln,exp} A B]",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical user interface",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo | sin | cos | tan | log | ln | exp)",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Display all recorded memory entries",
    )
    parser.add_argument(
        "--filter-operation",
        metavar="OPERATION",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Filter memory entries by operation name",
    )
    parser.add_argument(
        "--filter-success",
        action="store_true",
        help="Filter to show only successful memory entries",
    )
    parser.add_argument(
        "--filter-error",
        action="store_true",
        help="Filter to show only failed memory entries",
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Display calculation statistics",
    )
    parser.add_argument(
        "--export-memory",
        metavar="FILE",
        help="Export memory entries to a JSON file",
    )
    parser.add_argument(
        "--import-memory",
        metavar="FILE",
        help="Import memory entries from a JSON file",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing entries when importing (use with --import-memory)",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )

    args = parser.parse_args()
    calculator_service, memory_service, statistics_service = _build_service()
    cli = CalculatorCLI(calculator_service, memory_service, statistics_service)

    # Handle GUI mode
    if args.gui:
        gui = CalculatorWindow(memory_service)
        gui.run()
        sys.exit(0)

    if args.filter_success and args.filter_error:
        parser.error("Cannot use both --filter-success and --filter-error")

    # Handle export flag
    if args.export_memory:
        try:
            count = memory_service.export_memory_entries(args.export_memory)
            print(f"Exported {count} memory entries to {args.export_memory}")
            sys.exit(0)
        except (FileNotFoundError, IOError, OSError) as exc:
            print(f"Error exporting memory entries: {exc}", file=sys.stderr)
            sys.exit(1)

    # Handle import flag
    if args.import_memory:
        try:
            imported, skipped = memory_service.import_memory_entries(
                args.import_memory, overwrite=args.overwrite
            )
            print(f"Imported {imported} memory entries (skipped {skipped} invalid entries)")
            sys.exit(0)
        except (FileNotFoundError, IOError, OSError) as exc:
            print(f"Error importing memory entries: {exc}", file=sys.stderr)
            sys.exit(1)

    if args.statistics:
        stats = statistics_service.generate()
        print("=== Calculation Statistics ===\n")
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
        print(f"Average execution time: {stats.avg_execution_time_ms:.2f} ms")
        sys.exit(0)

    if args.filter_operation or args.filter_success or args.filter_error:
        success_filter = None
        if args.filter_success:
            success_filter = True
        elif args.filter_error:
            success_filter = False
        cli.show_filtered_memory_cli(args.filter_operation, success_filter)
        sys.exit(0)

    if args.memory:
        cli.show_memory_cli()
        sys.exit(0)

    if args.operation:
        if len(args.operands) != 2:
            parser.error("Exactly two operands are required when using --operation")
        try:
            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1])
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
