import argparse
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
from .storage.json_storage import JsonStorage
from .storage.memory_json_storage import MemoryJsonStorage
from .cli.calculator_cli import CalculatorCLI


def _build_service() -> tuple[CalculatorService, MemoryService]:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    memory_storage_path = Path(__file__).parent.parent / "artifacts" / "memory.json"
    memory_storage = MemoryJsonStorage(memory_storage_path)
    memory_service = MemoryService(memory_storage)
    calc_service = CalculatorService(
        Calculator(), JsonStorage(storage_path), memory_service
    )
    return calc_service, memory_service


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def _parse_status(status_str: str | None) -> bool | None:
    if status_str == "success":
        return True
    elif status_str == "failure":
        return False
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A [B]] [--memory {list,detail,failures,summary,stats,clear} [ID]]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo) or filter memory by operation type (use with --memory list)",
    )
    parser.add_argument(
        "--memory",
        metavar="ACTION",
        choices=["list", "detail", "failures", "summary", "stats", "clear"],
        help="Memory action (list | detail | failures | summary | stats | clear)",
    )
    parser.add_argument(
        "--status",
        metavar="STATUS",
        choices=["success", "failure"],
        help="Filter memory by execution status (use with --memory list)",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="ARG",
        help="Operands for operation or memory ID for detail action",
    )

    args = parser.parse_args()
    service, memory_service = _build_service()
    cli = CalculatorCLI(service, memory_service)

    # Handle memory commands
    if args.memory:
        if args.memory == "list":
            cli.show_memory_filtered_list(
                operation=args.operation,
                status=_parse_status(args.status)
            )
        elif args.memory == "detail":
            if not args.operands:
                parser.error("Memory detail requires an entry ID")
            cli.show_memory_detail(args.operands[0])
        elif args.memory == "failures":
            cli.show_memory_failures()
        elif args.memory == "summary":
            cli.show_memory_summary()
        elif args.memory == "stats":
            cli.show_memory_statistics(operation=args.operation)
        elif args.memory == "clear":
            cli.clear_memory_confirm()
        return

    if args.operation:
        # Unary operations need 1 operand, binary operations need 2
        unary_ops = {"square", "sqrt"}
        is_unary = args.operation in unary_ops
        required_operands = 1 if is_unary else 2

        if len(args.operands) != required_operands:
            if is_unary:
                parser.error("Exactly one operand is required for this operation")
            else:
                parser.error("Exactly two operands are required for this operation")

        try:
            a = _as_number(args.operands[0])
            # For unary operations, pass dummy second operand (0)
            b = _as_number(args.operands[1]) if not is_unary else 0
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
