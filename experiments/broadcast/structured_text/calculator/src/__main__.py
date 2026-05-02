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
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} OPERANDS]",
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
        help="Operands (1 for unary ops [square, sqrt]; 2 for binary ops)",
    )

    args = parser.parse_args()
    service = _build_service()
    cli = CalculatorCLI(service)

    if args.operation:
        operation = Operation.from_string(args.operation)
        expected_count = 1 if operation.is_unary() else 2
        if len(args.operands) != expected_count:
            op_type = "unary (1 operand)" if operation.is_unary() else "binary (2 operands)"
            parser.error(f"{args.operation} is a {op_type}, got {len(args.operands)}")
        try:
            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1]) if len(args.operands) > 1 else 0.0
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
