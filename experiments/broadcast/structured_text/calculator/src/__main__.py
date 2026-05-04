import argparse
import json
import sys
from pathlib import Path

from .models.operation import Operation
from .services.calculator import Calculator
from .services.calculator_service import CalculatorService
from .services.history_manager import HistoryManager
from .services.memory_service import MemoryService
from .services.query_service import QueryService
from .services.statistics_service import StatisticsService
from .storage.json_storage import JsonStorage
from .storage.memory_storage import MemoryStorage
from .cli.calculator_cli import CalculatorCLI
from .gui.calculator_gui import CalculatorGUI


def _build_service() -> tuple[CalculatorService, QueryService, StatisticsService, HistoryManager]:
    """Build and return CalculatorService, QueryService, StatisticsService, and HistoryManager."""
    calc_storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    memory_storage_path = Path(__file__).parent.parent / "artifacts" / "memory.json"

    calc_storage = JsonStorage(calc_storage_path)
    memory_storage = MemoryStorage(memory_storage_path)
    memory_service = MemoryService(memory_storage)
    history_manager = HistoryManager(memory_storage)

    calc_service = CalculatorService(Calculator(), calc_storage, memory_service)
    query_service = QueryService(memory_service)
    statistics_service = StatisticsService(memory_service)
    return calc_service, query_service, statistics_service, history_manager


def _as_number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid number")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="OOP Calculator — run interactively or pass --operation for one-shot use",
        usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo,sin,cos,tan,log,ln,exp} A B] [--scientific] [--gui] [--query-by-operation OP] [--query-by-state STATE] [--stats] [--export-history FILE] [--import-history FILE] [--append|--replace]",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical user interface",
    )
    parser.add_argument(
        "--scientific",
        action="store_true",
        help="Enable scientific mode with trigonometric and logarithmic operations",
    )
    parser.add_argument(
        "--operation",
        metavar="OP",
        choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo", "sin", "cos", "tan", "log", "ln", "exp"],
        help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo | sin | cos | tan | log | ln | exp)",
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
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display calculation statistics (operation counts, error rates, execution times)",
    )
    parser.add_argument(
        "--export-history",
        metavar="FILE",
        help="Export calculation history to a JSON file",
    )
    parser.add_argument(
        "--import-history",
        metavar="FILE",
        help="Import calculation history from a JSON file",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append imported history to existing records (use with --import-history)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing records with imported history (use with --import-history)",
    )

    args = parser.parse_args()
    calc_service, query_service, statistics_service, history_manager = _build_service()

    # GUI mode (GUI flag)
    if args.gui:
        memory_storage_path = Path(__file__).parent.parent / "artifacts" / "memory.json"
        memory_storage = MemoryStorage(memory_storage_path)
        memory_service = MemoryService(memory_storage)
        gui = CalculatorGUI(
            calc_service,
            query_service,
            statistics_service,
            memory_service,
            scientific_mode=args.scientific,
        )
        gui.run_interactive()
        return

    cli = CalculatorCLI(calc_service, query_service, statistics_service, history_manager, scientific_mode=args.scientific)

    # Export history mode (CLI flag)
    if args.export_history:
        try:
            count, errors = history_manager.export_to_file(args.export_history)
            if errors:
                print(f"Warning: {len(errors)} entries could not be exported:")
                for err in errors:
                    print(f"  - {err}", file=sys.stderr)
            print(f"Exported {count} entries to {args.export_history}")
        except IOError as exc:
            print(f"Error exporting history: {exc}", file=sys.stderr)
            sys.exit(1)
    # Import history mode (CLI flag)
    elif args.import_history:
        try:
            choice = "append" if args.append else "replace"
            count, errors = history_manager.import_from_file(args.import_history, choice=choice)

            if errors:
                print(f"Warning: {len(errors)} entries could not be imported:")
                for err in errors:
                    print(f"  - {err}", file=sys.stderr)

            if choice == "replace":
                print(f"Replaced history with {count} imported entries")
            else:
                print(f"Appended {count} entries to history")
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as exc:
            print(f"Error: Invalid JSON in file — {exc}", file=sys.stderr)
            sys.exit(1)
        except (IOError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    # Statistics mode (CLI flag)
    elif args.stats:
        report = statistics_service.compute_statistics()
        print("=== Calculation Statistics ===")
        print(f"Total operations: {report.total_operations}")
        print(f"Operations by type: {report.operation_count}")
        print(f"Total errors: {report.total_errors}")
        print(f"Error frequency: {report.error_frequency}")
        print(f"Error rate: {report.error_rate:.2%}")
        print(f"Average execution time: {report.average_execution_time_ms:.2f}ms")
        print(f"Min execution time: {report.min_execution_time_ms:.2f}ms")
        print(f"Max execution time: {report.max_execution_time_ms:.2f}ms")
    # Query mode (CLI flags)
    elif args.query_by_operation or args.query_by_state:
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
        scientific_ops = {"sin", "cos", "tan", "log", "ln", "exp"}
        required_operands = 1 if args.operation in scientific_ops else 2
        if len(args.operands) != required_operands:
            parser.error(f"Operation '{args.operation}' requires {required_operands} operand(s)")
        try:
            a = _as_number(args.operands[0])
            b = _as_number(args.operands[1]) if len(args.operands) > 1 else 0.0
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        cli.run_command(args.operation, a, b)
    else:
        # Interactive mode
        cli.run_interactive()


if __name__ == "__main__":
    main()
