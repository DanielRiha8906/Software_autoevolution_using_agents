import argparse
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
from .services.query_service import QueryService
from .storage.json_storage import JsonStorage
from .storage.memory_storage import MemoryStorage
from .cli.calculator_cli import CalculatorCLI


def _build_service() -> tuple[CalculatorService, QueryService]:
    """Build and return both CalculatorService and QueryService."""
    calc_storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    memory_storage_path = Path(__file__).parent.parent / "artifacts" / "memory.json"

    calc_storage = JsonStorage(calc_storage_path)
    memory_storage = MemoryStorage(memory_storage_path)
    memory_service = MemoryService(memory_storage)

    calc_service = CalculatorService(Calculator(), calc_storage, memory_service)
    query_service = QueryService(memory_service)
    return calc_service, query_service


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A B] [--query-by-operation OP] [--query-by-state STATE]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo)",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )
    parser.add_argument(
        "--query-by-operation",
        metavar="OP",
        help="Query calculations by operation type (e.g., add, subtract, multiply)",
    )
    parser.add_argument(
        "--query-by-state",
        metavar="STATE",
        choices=["success", "failed", "all"],
        help="Query calculations by result state (success | failed | all)",
    )

    args = parser.parse_args()
    calc_service, query_service = _build_service()
    cli = CalculatorCLI(calc_service, query_service)

    # Query mode (CLI flags)
    if args.query_by_operation or args.query_by_state:
        try:
            result_state = args.query_by_state if args.query_by_state else "all"
            results = query_service.query(
                operation_type=args.query_by_operation,
                result_state=result_state,
            )
            print(query_service.format_results(results))
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.operation:
        # Operation mode (CLI flag)
        if len(args.operands) != 2:
            parser.error("Exactly two operands are required when using --operation")
        try:
            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1])
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    else:
        # Interactive mode
        cli.run_interactive()


if __name__ == "__main__":
    main()
