"""Calculator GUI - tkinter-based graphical user interface.

This module provides a tkinter GUI for the calculator that delegates
all calculations to the service layer.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService


class CalculatorGUI:
    """Tkinter-based graphical user interface for the calculator.

    Implements a GUI that accepts a CalculatorService instance and
    delegates all calculations to it. Contains no arithmetic logic.

    Layer responsibilities:
    - Interface: GUI rendering and user interactions
    - Service: Calculation orchestration (CalculatorService)
    - Core: Pure calculation logic (accessed via CalculatorService)
    """

    def __init__(self, service: CalculatorService) -> None:
        """Initialize the GUI with a CalculatorService.

        Args:
            service: The CalculatorService that performs calculations
        """
        self.service = service
        self.root: Optional[tk.Tk] = None
        self.display_var: Optional[tk.StringVar] = None
        self.operand_a: Optional[float] = None
        self.pending_operation: Optional[Operation] = None

    def run(self) -> None:
        """Launch the tkinter GUI window."""
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.geometry("400x500")

        self.display_var = tk.StringVar(value="0")

        self._create_display()
        self._create_buttons()

        self.root.mainloop()

    def _create_display(self) -> None:
        """Create the display area."""
        display_frame = tk.Frame(self.root)
        display_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        display = tk.Entry(
            display_frame,
            textvar=self.display_var,
            font=("Arial", 20),
            justify=tk.RIGHT,
            state="readonly",
        )
        display.pack(fill=tk.BOTH, ipady=10)

    def _create_buttons(self) -> None:
        """Create the button grid."""
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Define button layout: (label, callback)
        buttons = [
            ("7", lambda: self._append_digit("7")),
            ("8", lambda: self._append_digit("8")),
            ("9", lambda: self._append_digit("9")),
            ("÷", lambda: self._set_operation(Operation.DIVIDE)),
            ("4", lambda: self._append_digit("4")),
            ("5", lambda: self._append_digit("5")),
            ("6", lambda: self._append_digit("6")),
            ("×", lambda: self._set_operation(Operation.MULTIPLY)),
            ("1", lambda: self._append_digit("1")),
            ("2", lambda: self._append_digit("2")),
            ("3", lambda: self._append_digit("3")),
            ("−", lambda: self._set_operation(Operation.SUBTRACT)),
            ("0", lambda: self._append_digit("0")),
            (".", lambda: self._append_digit(".")),
            ("=", lambda: self._calculate()),
            ("+", lambda: self._set_operation(Operation.ADD)),
            ("√", lambda: self._calculate_unary(Operation.SQRT)),
            ("x²", lambda: self._calculate_unary(Operation.SQUARE)),
            ("x^y", lambda: self._set_operation(Operation.POWER)),
            ("mod", lambda: self._set_operation(Operation.MODULO)),
            ("C", lambda: self._clear()),
        ]

        # Layout buttons in a grid
        row = 0
        col = 0
        for label, callback in buttons:
            btn = tk.Button(
                button_frame,
                text=label,
                command=callback,
                font=("Arial", 14),
                padx=10,
                pady=10,
            )
            btn.grid(row=row, column=col, sticky="nsew")
            col += 1
            if col >= 4:
                col = 0
                row += 1

        # Configure grid weights for resizing
        for i in range(row + 1):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

    def _append_digit(self, digit: str) -> None:
        """Append a digit to the display.

        Args:
            digit: The digit or decimal point to append
        """
        current = self.display_var.get()
        if current == "0":
            self.display_var.set(digit)
        else:
            self.display_var.set(current + digit)

    def _set_operation(self, operation: Operation) -> None:
        """Set the pending operation and store the first operand.

        Args:
            operation: The operation to perform
        """
        try:
            self.operand_a = float(self.display_var.get())
            self.pending_operation = operation
            self.display_var.set("0")
        except ValueError:
            messagebox.showerror("Error", "Invalid number")

    def _calculate_unary(self, operation: Operation) -> None:
        """Perform a unary operation (sqrt, square).

        Args:
            operation: The unary operation to perform
        """
        try:
            operand = float(self.display_var.get())
            # For unary operations, b is typically 0 or 1 depending on the operation
            result_obj = self.service.perform(operation, operand, 0)
            self.display_var.set(str(result_obj.result))
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _calculate(self) -> None:
        """Perform the pending operation."""
        if self.pending_operation is None or self.operand_a is None:
            return

        try:
            operand_b = float(self.display_var.get())
            result_obj = self.service.perform(
                self.pending_operation, self.operand_a, operand_b
            )
            self.display_var.set(str(result_obj.result))
            self.pending_operation = None
            self.operand_a = None
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _clear(self) -> None:
        """Clear the display and reset state."""
        self.display_var.set("0")
        self.operand_a = None
        self.pending_operation = None
