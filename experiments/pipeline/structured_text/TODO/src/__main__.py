import sys

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI
from .container import Container


def main() -> None:
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
