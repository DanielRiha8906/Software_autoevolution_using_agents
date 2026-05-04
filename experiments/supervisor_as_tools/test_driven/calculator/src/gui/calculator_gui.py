import tkinter as tk
from tkinter import messagebox
from typing import Optional

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService


class CalculatorGUI:
    """Tkinter-based GUI for the calculator application.

    Provides a windowed interface with number buttons, operation buttons,
    display output, and calculation history.
    """

    def __init__(self, service: CalculatorService) -> None:
        """Initialize the CalculatorGUI with a calculator service.

        Args:
            service: The CalculatorService instance to perform calculations.
        """
        self.service = service
        self.root: Optional[tk.Tk] = None
        self.display: Optional[tk.Label] = None
        self.history_text: Optional[tk.Text] = None

        # GUI state machine
        self.current_input: str = ""
        self.pending_operation: Optional[Operation] = None
        self.operand_a: float = 0.0
        self.result_shown: bool = False

    def run(self) -> None:
        """Launch the tkinter GUI main loop."""
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.geometry("500x700")

        self._create_widgets()
        self._refresh_history()

        self.root.mainloop()

    def _create_widgets(self) -> None:
        """Build the UI layout with display, buttons, and history."""
        if not self.root:
            return

        # Display frame
        display_frame = tk.Frame(self.root, bg="lightgray", height=80)
        display_frame.pack(fill=tk.X, padx=10, pady=10)
        display_frame.pack_propagate(False)

        self.display = tk.Label(
            display_frame,
            text="0",
            font=("Arial", 24, "bold"),
            bg="lightgray",
            anchor="e",
            padx=10,
            pady=10
        )
        self.display.pack(fill=tk.BOTH, expand=True)

        # Buttons frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Row 0: 7, 8, 9, /, Clear
        row0 = tk.Frame(buttons_frame)
        row0.pack(fill=tk.BOTH, expand=True, pady=2)
        self._create_button(row0, "7", lambda: self._on_number_click("7"))
        self._create_button(row0, "8", lambda: self._on_number_click("8"))
        self._create_button(row0, "9", lambda: self._on_number_click("9"))
        self._create_button(row0, "÷", lambda: self._on_operation_click(Operation.DIVIDE))
        self._create_button(row0, "Clear", self._on_clear_click)

        # Row 1: 4, 5, 6, *, Del
        row1 = tk.Frame(buttons_frame)
        row1.pack(fill=tk.BOTH, expand=True, pady=2)
        self._create_button(row1, "4", lambda: self._on_number_click("4"))
        self._create_button(row1, "5", lambda: self._on_number_click("5"))
        self._create_button(row1, "6", lambda: self._on_number_click("6"))
        self._create_button(row1, "×", lambda: self._on_operation_click(Operation.MULTIPLY))
        self._create_button(row1, "Del", self._on_backspace_click)

        # Row 2: 1, 2, 3, -, Sqrt
        row2 = tk.Frame(buttons_frame)
        row2.pack(fill=tk.BOTH, expand=True, pady=2)
        self._create_button(row2, "1", lambda: self._on_number_click("1"))
        self._create_button(row2, "2", lambda: self._on_number_click("2"))
        self._create_button(row2, "3", lambda: self._on_number_click("3"))
        self._create_button(row2, "−", lambda: self._on_operation_click(Operation.SUBTRACT))
        self._create_button(row2, "√", lambda: self._on_unary_operation_click(Operation.SQRT))

        # Row 3: 0, ., +, =, ^
        row3 = tk.Frame(buttons_frame)
        row3.pack(fill=tk.BOTH, expand=True, pady=2)
        self._create_button(row3, "0", lambda: self._on_number_click("0"))
        self._create_button(row3, ".", lambda: self._on_number_click("."))
        self._create_button(row3, "+", lambda: self._on_operation_click(Operation.ADD))
        self._create_button(row3, "=", self._on_equals_click)
        self._create_button(row3, "^", lambda: self._on_operation_click(Operation.POWER))

        # Row 4: Sin, Cos, Tan, Log, Ln
        row4 = tk.Frame(buttons_frame)
        row4.pack(fill=tk.BOTH, expand=True, pady=2)
        self._create_button(row4, "Sin", lambda: self._on_unary_operation_click(Operation.SIN))
        self._create_button(row4, "Cos", lambda: self._on_unary_operation_click(Operation.COS))
        self._create_button(row4, "Tan", lambda: self._on_unary_operation_click(Operation.TAN))
        self._create_button(row4, "Log", lambda: self._on_unary_operation_click(Operation.LOG))
        self._create_button(row4, "Ln", lambda: self._on_unary_operation_click(Operation.LN))

        # Row 5: Exp, Sq, Mod
        row5 = tk.Frame(buttons_frame)
        row5.pack(fill=tk.BOTH, expand=True, pady=2)
        self._create_button(row5, "Exp", lambda: self._on_unary_operation_click(Operation.EXP))
        self._create_button(row5, "Sq", lambda: self._on_unary_operation_click(Operation.SQUARE))
        self._create_button(row5, "Mod", lambda: self._on_operation_click(Operation.MODULO))

        # History frame
        history_label = tk.Label(self.root, text="History:", font=("Arial", 10, "bold"))
        history_label.pack(fill=tk.X, padx=10, pady=(10, 0))

        history_scroll = tk.Scrollbar(self.root)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.history_text = tk.Text(
            self.root,
            height=6,
            yscrollcommand=history_scroll.set,
            font=("Arial", 9),
            state=tk.DISABLED
        )
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        history_scroll.config(command=self.history_text.yview)

    def _create_button(self, parent: tk.Frame, text: str, command) -> tk.Button:
        """Create a button and add it to the parent frame.

        Args:
            parent: The parent frame.
            text: Button label text.
            command: The callback function.

        Returns:
            The created button widget.
        """
        btn = tk.Button(
            parent,
            text=text,
            font=("Arial", 12, "bold"),
            height=2,
            command=command
        )
        btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        return btn

    def _on_number_click(self, digit: str) -> None:
        """Handle number and decimal point input.

        Args:
            digit: The digit or '.' character.
        """
        if self.result_shown:
            self.current_input = ""
            self.result_shown = False

        if digit == ".":
            if "." not in self.current_input:
                if not self.current_input:
                    self.current_input = "0."
                else:
                    self.current_input += "."
        else:
            self.current_input += digit

        self._update_display()

    def _on_operation_click(self, operation: Operation) -> None:
        """Handle binary operation button click.

        Args:
            operation: The operation to perform.
        """
        if not self.current_input and self.pending_operation is None:
            return

        if self.current_input:
            self.operand_a = float(self.current_input)
            self.current_input = ""

        self.pending_operation = operation
        self.result_shown = False
        self._update_display()

    def _on_unary_operation_click(self, operation: Operation) -> None:
        """Handle unary operation button click.

        Args:
            operation: The unary operation to perform.
        """
        if not self.current_input:
            return

        try:
            operand = float(self.current_input)
            result = self.service.perform(operation, operand, 0.0)
            self.current_input = str(result.result)
            self.pending_operation = None
            self.result_shown = True
            self._update_display()
            self._refresh_history()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            self._on_clear_click()

    def _on_equals_click(self) -> None:
        """Trigger calculation when equals button is clicked."""
        if not self.pending_operation or not self.current_input:
            return

        try:
            operand_b = float(self.current_input)
            result = self.service.perform(self.pending_operation, self.operand_a, operand_b)
            self.current_input = str(result.result)
            self.pending_operation = None
            self.result_shown = True
            self._update_display()
            self._refresh_history()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            self._on_clear_click()

    def _on_clear_click(self) -> None:
        """Reset the calculator state."""
        self.current_input = ""
        self.pending_operation = None
        self.operand_a = 0.0
        self.result_shown = False
        self._update_display()

    def _on_backspace_click(self) -> None:
        """Delete the last character from the current input."""
        if self.current_input:
            self.current_input = self.current_input[:-1]
            self._update_display()

    def _update_display(self) -> None:
        """Update the display label with current input or pending operation."""
        if not self.display:
            return

        if self.current_input:
            self.display.config(text=self.current_input)
        elif self.pending_operation:
            self.display.config(text=self.pending_operation.display_name())
        else:
            self.display.config(text="0")

    def _show_history(self) -> None:
        """Display results from service.get_history() in the history widget."""
        self._refresh_history()

    def _refresh_history(self) -> None:
        """Refresh the history display with recent calculations."""
        if not self.history_text:
            return

        history = self.service.get_history()

        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)

        if not history:
            self.history_text.insert(tk.END, "No calculations yet.")
        else:
            for entry in reversed(history[-10:]):  # Show last 10 entries
                self.history_text.insert(tk.END, f"{entry}\n")

        self.history_text.config(state=tk.DISABLED)
