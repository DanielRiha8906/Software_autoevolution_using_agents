import sys
import argparse

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI
from .gui.todo_gui import TodoGUI


def main() -> None:
    # Handle --gui flag early, before CLI parsing
    if "--gui" in sys.argv:
        gui = TodoGUI()
        gui.run()
        sys.exit(0)

    if len(sys.argv) > 1:
        sys.exit(TodoCLI().run())

    menu = InteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
