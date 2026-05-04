"""Input panel for calculator operands and operation selection."""

import tkinter as tk
from tkinter import ttk

from .constants import (
    FONT_LABEL, FONT_BUTTON, PADDING_STANDARD,
    COLOR_PANEL_BACKGROUND, COLOR_BUTTON_BACKGROUND,
    STANDARD_OPS, SCIENTIFIC_OPS
)


class InputPanel(tk.Frame):
    """Panel for operation selection and operand entry.

    Provides:
    - Operation dropdown selector
    - Operand A entry field
    - Operand B entry field (disabled for unary operations)
    - Calculate button
    - Clear button
    - Error message display
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the input panel.

        Args:
            parent: Parent tkinter widget.
        """
        super().__init__(parent, bg=COLOR_PANEL_BACKGROUND)
        self.current_mode = "scientific"  # Default to scientific
        self.calculate_callback = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Operation selection
        operation_frame = tk.Frame(self, bg=COLOR_PANEL_BACKGROUND)
        operation_frame.pack(fill=tk.X, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        tk.Label(operation_frame, text="Operation:", font=FONT_LABEL, bg=COLOR_PANEL_BACKGROUND).pack(side=tk.LEFT)
        self.operation_var = tk.StringVar(value="add")
        self.operation_dropdown = ttk.Combobox(
            operation_frame,
            textvariable=self.operation_var,
            values=SCIENTIFIC_OPS,
            state="readonly",
            width=20
        )
        self.operation_dropdown.pack(side=tk.LEFT, padx=PADDING_STANDARD)
        self.operation_dropdown.bind("<<ComboboxSelected>>", self._on_operation_changed)

        # Operand A entry
        operand_a_frame = tk.Frame(self, bg=COLOR_PANEL_BACKGROUND)
        operand_a_frame.pack(fill=tk.X, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        tk.Label(operand_a_frame, text="Operand A:", font=FONT_LABEL, bg=COLOR_PANEL_BACKGROUND).pack(side=tk.LEFT)
        self.operand_a_var = tk.StringVar(value="0")
        self.operand_a_entry = tk.Entry(operand_a_frame, textvariable=self.operand_a_var, width=20)
        self.operand_a_entry.pack(side=tk.LEFT, padx=PADDING_STANDARD)

        # Operand B entry
        operand_b_frame = tk.Frame(self, bg=COLOR_PANEL_BACKGROUND)
        operand_b_frame.pack(fill=tk.X, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        tk.Label(operand_b_frame, text="Operand B:", font=FONT_LABEL, bg=COLOR_PANEL_BACKGROUND).pack(side=tk.LEFT)
        self.operand_b_var = tk.StringVar(value="0")
        self.operand_b_entry = tk.Entry(operand_b_frame, textvariable=self.operand_b_var, width=20)
        self.operand_b_entry.pack(side=tk.LEFT, padx=PADDING_STANDARD)

        # Buttons frame
        button_frame = tk.Frame(self, bg=COLOR_PANEL_BACKGROUND)
        button_frame.pack(fill=tk.X, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        self.calculate_button = tk.Button(
            button_frame,
            text="Calculate",
            font=FONT_BUTTON,
            bg=COLOR_BUTTON_BACKGROUND,
            command=self._on_calculate
        )
        self.calculate_button.pack(side=tk.LEFT, padx=PADDING_STANDARD)

        self.clear_button = tk.Button(
            button_frame,
            text="Clear",
            font=FONT_BUTTON,
            bg=COLOR_BUTTON_BACKGROUND,
            command=self._on_clear
        )
        self.clear_button.pack(side=tk.LEFT, padx=PADDING_STANDARD)

        # Error message display
        self.error_label = tk.Label(
            self,
            text="",
            font=FONT_LABEL,
            bg=COLOR_PANEL_BACKGROUND,
            fg="#d32f2f",
            wraplength=400
        )
        self.error_label.pack(fill=tk.X, padx=PADDING_STANDARD)

    def set_calculate_callback(self, callback) -> None:
        """Set the callback to invoke when Calculate is clicked.

        Args:
            callback: Function to call with (operation_str, a, b).
        """
        self.calculate_callback = callback

    def _on_operation_changed(self, event=None) -> None:
        """Handle operation selection change."""
        operation = self.operation_var.get()
        # Disable operand_b for unary operations
        unary_ops = ["square", "sqrt", "sin", "cos", "tan", "log", "ln", "exp"]
        if operation in unary_ops:
            self.operand_b_entry.config(state=tk.DISABLED)
        else:
            self.operand_b_entry.config(state=tk.NORMAL)

    def _on_calculate(self) -> None:
        """Handle Calculate button click."""
        self.error_label.config(text="")

        try:
            operation = self.operation_var.get()
            a = float(self.operand_a_var.get())
            b = float(self.operand_b_var.get())

            if self.calculate_callback:
                self.calculate_callback(operation, a, b)
        except ValueError as e:
            self.error_label.config(text=f"Error: Invalid input — {str(e)}")

    def _on_clear(self) -> None:
        """Handle Clear button click."""
        self.operand_a_var.set("0")
        self.operand_b_var.set("0")
        self.operation_var.set("add")
        self.error_label.config(text="")
        self._on_operation_changed()

    def set_mode(self, mode: str) -> None:
        """Set the operation mode (standard or scientific).

        Args:
            mode: Either 'standard' or 'scientific'.
        """
        self.current_mode = mode
        operations = STANDARD_OPS if mode == "standard" else SCIENTIFIC_OPS
        self.operation_dropdown.config(values=operations)
        # Reset to first operation if current is not in the list
        if self.operation_var.get() not in operations:
            self.operation_var.set(operations[0])
            self._on_operation_changed()

    def get_operands(self) -> tuple[float, float]:
        """Get the currently entered operands.

        Returns:
            Tuple of (operand_a, operand_b) as floats.

        Raises:
            ValueError: If operands cannot be parsed as floats.
        """
        return float(self.operand_a_var.get()), float(self.operand_b_var.get())

    def get_operation(self) -> str:
        """Get the currently selected operation.

        Returns:
            Operation name as string.
        """
        return self.operation_var.get()

    def set_error_message(self, message: str) -> None:
        """Set an error message to display.

        Args:
            message: Error message text.
        """
        self.error_label.config(text=message)

    def clear_error_message(self) -> None:
        """Clear the error message."""
        self.error_label.config(text="")
