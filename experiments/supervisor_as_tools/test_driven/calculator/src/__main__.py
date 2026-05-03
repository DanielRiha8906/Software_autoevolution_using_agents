import argparse
import sys
from pathlib import Path
from typing import Optional

from .models.operation import Operation
from .services.calculator import Calculator
from .services.scientific_calculator import ScientificCalculator
from .services.calculator_service import CalculatorService
from .services.memory_service import MemoryService
from .services.statistics_service import StatisticsService
from .services.import_export_service import ImportExportService
from .storage.json_storage import JsonStorage
from .cli.calculator_cli import CalculatorCLI


def _build_service() -> CalculatorService:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    return CalculatorService(ScientificCalculator(), JsonStorage(storage_path))


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


def _is_single_arg_operation(op_str: str) -> bool:
    """Check if an operation requires only one argument."""
    return op_str in ("sin", "cos", "tan", "log", "ln", "exp")


def _is_unary_operation(op_str: str) -> bool:
    """Check if an operation is unary (single argument)."""
    return op_str in ("square", "sqrt", "sin", "cos", "tan", "log", "ln", "exp")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively, perform calculations, or query memory",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo,sin,cos,tan,log,ln,exp} OPERANDS | --query [--operation OP] [--success true|false] | --export FILE | --import FILE]",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Operation to perform (standard: add | subtract | multiply | divide | square | sqrt | power | modulo; scientific: sin | cos | tan | log | ln | exp)",
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
        "--statistics",
        action="store_true",
        help="Display statistics about calculations",
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
        help="Operands (1 for unary: square, sqrt, sin, cos, tan, log, ln, exp; 2 for binary operations)",
    )

    args = parser.parse_args()
    service = _build_service()
    memory_service = MemoryService()
    cli = CalculatorCLI(service, memory_service)
    import_export_service = ImportExportService()

    if args.export:
        # Export mode
        try:
            count = import_export_service.export(memory_service, args.export)
            print(f"Exported {count} entries to {args.export}")
        except Exception as exc:
            print(f"Error exporting: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.import_file:
        # Import mode
        try:
            count = import_export_service.import_from(memory_service, args.import_file)
            print(f"Imported {count} entries from {args.import_file}")
        except Exception as exc:
            print(f"Error importing: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.statistics:
        # Statistics mode
        stats_service = StatisticsService(memory_service)
        report = stats_service.compute()
        cli.show_statistics(report)
    elif args.query:
        # Query mode
        operation_filter: Optional[str] = getattr(args, 'operation', None)
        cli.run_query(operation=operation_filter, success=args.success)
    elif args.operation:
        # Calculate mode
        is_unary = _is_unary_operation(args.operation)
        required_operands = 1 if is_unary else 2
        if len(args.operands) != required_operands:
            parser.error(f"{args.operation} requires exactly {required_operands} operand(s)")
        try:
            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1]) if required_operands == 2 else 0.0
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    else:
        # Interactive mode
        cli.run_interactive()


if __name__ == "__main__":
    main()
