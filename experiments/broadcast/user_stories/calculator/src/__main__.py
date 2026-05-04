import argparse
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.memory_store_impl import MemoryStoreImpl
from .storage.json_storage import JsonStorage
from .cli.calculator_cli import CalculatorCLI


def _build_service() -> CalculatorService:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    return CalculatorService(Calculator(), JsonStorage(storage_path))


def _build_memory_store() -> MemoryStoreImpl:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    return MemoryStoreImpl(JsonStorage(storage_path))


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass flags for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo,sin,cos,tan,log,ln,exp} A [B]] [--memory-history] [--history] [--memory-retrieve] [--memory-store OP OPERANDS... [--result R] | [--error MSG]] [--filter-op OP] [--filter-state STATE] [--export-history FILE] [--import-history FILE]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Operation to perform (standard: add | subtract | multiply | divide | square | sqrt | power | modulo; scientific: sin | cos | tan | log | ln | exp)",
    )
    parser.add_argument(
        "--memory-history",
        action="store_true",
        help="Display memory entry history (includes results and errors)",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Display calculation history",
    )
    parser.add_argument(
        "--memory-retrieve",
        action="store_true",
        help="Retrieve and display all stored memory entries",
    )
    parser.add_argument(
        "--memory-store",
        metavar="OP",
        help="Store a memory entry with given operation",
    )
    parser.add_argument(
        "--result",
        type=float,
        help="Result value for a successful memory entry (use with --memory-store)",
    )
    parser.add_argument(
        "--error",
        type=str,
        help="Error message for a failed memory entry (use with --memory-store)",
    )
    parser.add_argument(
        "--filter-op",
        metavar="OP",
        help="Filter entries by operation type (e.g., add, subtract)",
    )
    parser.add_argument(
        "--filter-state",
        metavar="STATE",
        choices=["success", "error"],
        help="Filter entries by result state (success | error)",
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Display statistics from stored calculations",
    )
    parser.add_argument(
        "--export-history",
        metavar="FILE",
        help="Export history to a JSON file",
    )
    parser.add_argument(
        "--import-history",
        metavar="FILE",
        help="Import history from a JSON file",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="When importing, overwrite existing entries with same ID (use with --import-history)",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given) or operands for --memory-store",
    )

    args = parser.parse_args()
    service = _build_service()
    memory_store = _build_memory_store()
    cli = CalculatorCLI(service, memory_store)

    if args.operation:
        try:
            operation = Operation.from_string(args.operation)
            required_arity = operation.arity()
            if len(args.operands) != required_arity:
                parser.error(f"Operation '{args.operation}' requires {required_arity} operand(s), but {len(args.operands)} provided")

            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1]) if len(args.operands) > 1 else None
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        except ValueError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    elif args.memory_retrieve:
        cli.memory_retrieve_command()
    elif args.memory_store:
        if len(args.operands) == 0:
            parser.error("--memory-store requires at least one operand")
        try:
            operands = [_as_number(op) for op in args.operands]
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.memory_store_command(args.memory_store, operands, result=args.result, error=args.error)
    elif args.filter_op or args.filter_state:
        cli.filter_command(operation=args.filter_op, state=args.filter_state)
    elif args.statistics:
        cli.statistics_command()
    elif args.export_history:
        cli.export_command(args.export_history)
    elif args.import_history:
        cli.import_command(args.import_history, overwrite=args.overwrite)
    elif args.memory_history:
        cli.show_memory_history_command()
    elif args.history:
        cli.show_history_command()
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
