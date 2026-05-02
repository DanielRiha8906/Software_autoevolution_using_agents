import argparse
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
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
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A [B]]",
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
        help="Operands: one for unary ops (square, sqrt) or two for binary ops",
    )

    args = parser.parse_args()
    service = _build_service()
    cli = CalculatorCLI(service)

    if args.operation:
        # Determine expected operand count based on operation
        unary_ops = {"square", "sqrt"}
        binary_ops = {"add", "subtract", "multiply", "divide", "power", "modulo"}

        if args.operation in unary_ops:
            if len(args.operands) != 1:
                parser.error(f"Operation '{args.operation}' requires exactly one operand")
            try:
                a = _as_number(args.operands[0])
                b = 0.0  # Placeholder for unary operations
            except argparse.ArgumentTypeError as exc:
                parser.error(str(exc))
        elif args.operation in binary_ops:
            if len(args.operands) != 2:
                parser.error(f"Operation '{args.operation}' requires exactly two operands")
            try:
                a = _as_number(args.operands[0])
                b = _as_number(args.operands[1])
            except argparse.ArgumentTypeError as exc:
                parser.error(str(exc))
        else:
            parser.error(f"Unknown operation: '{args.operation}'")

        cli.run_command(args.operation, a, b)
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
