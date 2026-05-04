import sys

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI


def main() -> None:
    if len(sys.argv) > 1:
        # Check for GUI flag
        if sys.argv[1] == "--gui":
            from .gui import TodoGUI
            gui = TodoGUI()
            gui.run()
            return
        sys.exit(TodoCLI().run())

    menu = InteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
