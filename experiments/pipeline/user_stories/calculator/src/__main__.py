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


def _build_services() -> tuple[CalculatorService, StatisticsService]:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    storage = JsonStorage(storage_path)
    memory_service = MemoryService(storage)
    calculator_service = CalculatorService(Calculator(), memory_service)
    statistics_service = StatisticsService(memory_service)
    return calculator_service, statistics_service


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A B] [--show-history]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo)",
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
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )

    args = parser.parse_args()
    calculator_service, statistics_service = _build_services()
    cli = CalculatorCLI(calculator_service, statistics_service)

    # Handle --statistics flag first
    if args.statistics:
        cli._show_statistics()
        sys.exit(0)

    # Handle --show-history (with optional filters)
    if args.show_history or args.filter_operation or args.filter_state:
        # If no filters, use the simple _show_history method
        if not args.filter_operation and not args.filter_state:
            cli._show_history()
            sys.exit(0)

        # Parse and validate filters
        operations = None
        state = None

        # Parse filter-operation if provided
        if args.filter_operation:
            operations = [op.strip() for op in args.filter_operation.split(",")]
            # Validate operation names
            for op_name in operations:
                try:
                    Operation.from_string(op_name)
                except ValueError as exc:
                    parser.error(str(exc))

        # Use filter-state if provided, otherwise default to None (which means 'both')
        if args.filter_state:
            state = args.filter_state

        # Display filtered history
        cli._show_filtered_history(operations, state)
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
