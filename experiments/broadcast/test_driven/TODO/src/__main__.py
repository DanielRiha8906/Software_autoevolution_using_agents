import sys

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI
from .services.todo_service import TodoService
from .gui.todo_gui import TodoGUI


def main() -> None:
    if len(sys.argv) > 1:
        if sys.argv[1] == "--gui":
            service = TodoService()
            gui = TodoGUI(service)
            gui.run()
        else:
            sys.exit(TodoCLI().run())
    else:
        menu = InteractiveMenu()
        try:
            menu.run()
        except KeyboardInterrupt:
            print()
            sys.exit(0)


if __name__ == "__main__":
    main()
