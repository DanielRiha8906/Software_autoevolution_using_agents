import tkinter as tk

from .main_window import MainWindow


def launch_gui() -> None:
    """Initialize and launch the tkinter GUI main window."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
