import argparse
import sys
from pathlib import Path
from typing import Optional

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
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


def _as_bool(value: str) -> bool:
    """Parse a string to boolean."""
    normalized = value.lower()
    if normalized in ("true", "1", "yes", "y"):
        return True
    elif normalized in ("false", "0", "no", "n"):
        return False
    else:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid boolean (use: true/false)")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively, perform calculations, or query memory",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A B | --query [--operation OP] [--success true|false]]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo)",
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="Query memory entries instead of running calculations",
    )
    parser.add_argument(
        "--success",
        metavar="true|false",
        type=_as_bool,
        help="Filter query results by success state (true for successful, false for failed)",
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
    cli = CalculatorCLI(service, memory_service)

    if args.query:
        # Query mode
        operation_filter: Optional[str] = getattr(args, 'operation', None)
        cli.run_query(operation=operation_filter, success=args.success)
    elif args.operation:
        # Calculate mode
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
