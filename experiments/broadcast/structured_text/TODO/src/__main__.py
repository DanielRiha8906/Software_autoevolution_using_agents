import sys
import argparse

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src", description="TODO task manager")
    parser.add_argument("--gui", action="store_true", help="Launch graphical user interface")
    parser.add_argument("--storage", type=str, help="Path to storage file")

    # Check if --gui flag is present
    if "--gui" in sys.argv:
        from .gui.todo_gui import TodoGUI
        args = parser.parse_args()
        app = TodoGUI(storage_path=args.storage)
        app.run()
        sys.exit(0)

    # Otherwise, use CLI mode
    if len(sys.argv) > 1 and not any(arg in sys.argv for arg in ["--help", "-h"]):
        sys.exit(TodoCLI().run())

    # Show help if --help requested
    if any(arg in sys.argv for arg in ["--help", "-h"]):
        parser.print_help()
        sys.exit(0)

    menu = InteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
