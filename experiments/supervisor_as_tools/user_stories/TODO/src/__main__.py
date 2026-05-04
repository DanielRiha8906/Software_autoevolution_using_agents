import sys

from .cli.interactive_menu import InteractiveMenu
from .cli.todo_cli import TodoCLI


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        from .gui import gui_main
        gui_main.launch_gui()
    elif len(sys.argv) > 1:
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
