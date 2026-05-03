import argparse
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
from .services.statistics_service import StatisticsService
from .services.import_export_service import ImportExportService
from .storage.json_storage import JsonStorage
from .cli.calculator_cli import CalculatorCLI


def _build_service() -> CalculatorService:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    return CalculatorService(Calculator(), JsonStorage(storage_path))


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass --operation, --statistics, --import, or --export",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A B] [--statistics] [--import FILE] [--export FILE]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo)",
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Display statistics from memory entries",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export memory entries to a JSON file",
    )
    parser.add_argument(
        "--import",
        metavar="FILE",
        dest="import_file",
        help="Import memory entries from a JSON file",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )

    args = parser.parse_args()
    service = _build_service()
    memory_service = MemoryService()
    cli = CalculatorCLI(service)
    import_export = ImportExportService(memory_service)

    if args.import_file:
        try:
            import_export.import_from(args.import_file)
            print(f"Successfully imported entries from {args.import_file}")
        except FileNotFoundError:
            print(f"Error: File not found: {args.import_file}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.export:
        try:
            import_export.export(args.export)
            print(f"Successfully exported entries to {args.export}")
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.statistics:
        stats_service = StatisticsService(memory_service)
        report = stats_service.compute()

        if not memory_service.retrieve():
            print("No entries to analyze yet.")
        else:
            print("=== Statistics ===")
            print(f"Operations count:")
            for operation, count in sorted(report.count_per_operation.items()):
                print(f"  {operation}: {count}")
            print(f"Total errors: {report.total_errors}")
            print(f"Error rate: {report.error_rate:.2f}%")
            print(f"Average execution time: {report.avg_execution_time_ms:.2f}ms")
    elif args.operation:
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
