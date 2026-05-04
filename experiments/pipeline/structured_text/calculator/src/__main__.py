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
from .gui.calculator_gui import CalculatorGUI


def _build_service() -> CalculatorService:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    return CalculatorService(Calculator(), JsonStorage(storage_path))


def _build_memory_service() -> MemoryService:
    memory_storage_path = Path(__file__).parent.parent / "artifacts" / "memory_entries.json"
    return MemoryService(MemoryJsonStorage(memory_storage_path))


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively, use GUI, or pass flags for one-shot use",
        usage="python -m src [--gui] [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo,sin,cos,tan,log,ln,exp} A B] [--memory] [--statistics] [--memory-filter {operation,status} ...] [--export [FILE]] [--import [FILE]] [--skip-invalid]",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical user interface (GUI) instead of CLI",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo | sin | cos | tan | log | ln | exp)",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Display all stored calculation memory entries and exit",
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Display calculation statistics and exit",
    )
    parser.add_argument(
        "--memory-filter",
        metavar="TYPE",
        choices=["operation", "status"],
        help="Filter memory entries by operation name or success status",
    )
    parser.add_argument(
        "--filter-operation",
        metavar="OPERATION",
        help="Operation name to filter by: add | subtract | multiply | divide | square | sqrt | power | modulo | sin | cos | tan | log | ln | exp (use with --memory-filter operation)",
    )
    parser.add_argument(
        "--filter-status",
        metavar="STATUS",
        choices=["success", "failed"],
        help="Status to filter by: success or failed (use with --memory-filter status)",
    )
    parser.add_argument(
        "--export",
        nargs="?",
        const="__PROMPT__",
        metavar="FILE",
        help="Export memory entries to a JSON file (prompts for path if FILE not provided)",
    )
    parser.add_argument(
        "--import",
        dest="import_file",
        nargs="?",
        const="__PROMPT__",
        metavar="FILE",
        help="Import memory entries from a JSON file (prompts for path if FILE not provided)",
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="When importing, skip malformed entries instead of failing on the first error",
    )
    parser.add_argument(
        "operands",
        nargs="*",
        metavar="NUMBER",
        help="Two operands (required when --operation is given)",
    )

    args = parser.parse_args()
    service = _build_service()
    memory_service = _build_memory_service()

    # Handle GUI flag (takes precedence)
    if args.gui:
        gui = CalculatorGUI(service, memory_service)
        gui.run()
        return

    cli = CalculatorCLI(service, memory_service)

    # Handle export flag
    if args.export is not None:
        # args.export will be filepath, or "__PROMPT__" if flag used without path
        filepath = None if args.export == "__PROMPT__" else args.export
        cli.export_memory(filepath)
        return

    # Handle import flag
    if args.import_file is not None:
        # args.import_file will be filepath, or "__PROMPT__" if flag used without path
        filepath = None if args.import_file == "__PROMPT__" else args.import_file
        cli.import_memory(filepath, skip_invalid=args.skip_invalid)
        return

    if args.memory_filter:
        if args.memory_filter == "operation":
            if not args.filter_operation:
                parser.error("--filter-operation is required when using --memory-filter operation")
            entries = memory_service.filter_by_operation(args.filter_operation)
            if not entries:
                print(f"No entries match the filter criteria.")
            else:
                print()
                for i, entry in enumerate(entries, 1):
                    print(f"  {i}. {entry}")
                print()
        elif args.memory_filter == "status":
            if not args.filter_status:
                parser.error("--filter-status is required when using --memory-filter status")
            success = args.filter_status == "success"
            entries = memory_service.filter_by_success(success)
            if not entries:
                print(f"No entries match the filter criteria.")
            else:
                print()
                for i, entry in enumerate(entries, 1):
                    print(f"  {i}. {entry}")
                print()
    elif args.statistics:
        cli.show_statistics()
    elif args.memory:
        cli.show_memory()
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
