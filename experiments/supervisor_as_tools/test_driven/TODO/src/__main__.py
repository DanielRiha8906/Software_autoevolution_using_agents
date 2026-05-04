import sys

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI
from .gui.todo_gui import TodoGUI
from .services.todo_service import TodoService


def main() -> None:
    if len(sys.argv) > 1:
        if "--gui" in sys.argv:
            service = TodoService()
            gui = TodoGUI(service)
            gui.run()
            sys.exit(0)
        sys.exit(TodoCLI().run())

    menu = InteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
