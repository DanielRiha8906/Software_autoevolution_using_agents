import sys

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI


def main() -> None:
    if len(sys.argv) > 1:
        # Check for --gui flag
        if "--gui" in sys.argv:
            from .gui.todo_gui import TodoGUI
            TodoGUI().run()
            sys.exit(0)

        # Otherwise run CLI
        sys.exit(TodoCLI().run())

    # No arguments: run interactive menu
    menu = InteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
