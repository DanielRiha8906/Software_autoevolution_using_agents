"""Mode selector for standard/scientific operation mode."""

import tkinter as tk

from .constants import FONT_MODE, PADDING_STANDARD, COLOR_PANEL_BACKGROUND


class ModeSelector(tk.Frame):
    """Panel for toggling between standard and scientific operation modes.

    Standard mode shows only basic 6 operations: add, subtract, multiply, divide, square, sqrt
    Scientific mode shows all 14 operations including trigonometric and logarithmic functions.

    This is a GUI-only feature; no backend changes are required.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the mode selector.

        Args:
            parent: Parent tkinter widget.
        """
        super().__init__(parent, bg=COLOR_PANEL_BACKGROUND)
        self.mode_changed_callback = None
        self.current_mode = "scientific"  # Default to scientific
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tk.Label(
            self,
            text="Mode:",
            font=FONT_MODE,
            bg=COLOR_PANEL_BACKGROUND
        ).pack(side=tk.LEFT, padx=PADDING_STANDARD)

        self.mode_var = tk.StringVar(value="scientific")

        standard_button = tk.Radiobutton(
            self,
            text="Standard",
            variable=self.mode_var,
            value="standard",
            font=FONT_MODE,
            bg=COLOR_PANEL_BACKGROUND,
            command=self._on_mode_changed
        )
        standard_button.pack(side=tk.LEFT, padx=PADDING_STANDARD)

        scientific_button = tk.Radiobutton(
            self,
            text="Scientific",
            variable=self.mode_var,
            value="scientific",
            font=FONT_MODE,
            bg=COLOR_PANEL_BACKGROUND,
            command=self._on_mode_changed
        )
        scientific_button.pack(side=tk.LEFT, padx=PADDING_STANDARD)

    def set_mode_changed_callback(self, callback) -> None:
        """Set the callback to invoke when mode changes.

        Args:
            callback: Function to call with (mode: str).
        """
        self.mode_changed_callback = callback

    def _on_mode_changed(self) -> None:
        """Handle mode change."""
        mode = self.mode_var.get()
        self.current_mode = mode
        if self.mode_changed_callback:
            self.mode_changed_callback(mode)

    def get_mode(self) -> str:
        """Get the currently selected mode.

        Returns:
            Either 'standard' or 'scientific'.
        """
        return self.current_mode
