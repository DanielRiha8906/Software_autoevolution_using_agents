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
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A B]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo)",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Display all recorded memory entries",
    )
    parser.add_argument(
        "--filter-operation",
        metavar="OPERATION",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
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
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )

    args = parser.parse_args()
    calculator_service, memory_service, statistics_service = _build_service()
    cli = CalculatorCLI(calculator_service, memory_service, statistics_service)

    if args.filter_success and args.filter_error:
        parser.error("Cannot use both --filter-success and --filter-error")

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
