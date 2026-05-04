import tkinter as tk
from tkinter import messagebox

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService


class CalculatorGUI:
    """GUI for calculator using tkinter, orchestrates via CalculatorService."""

    def __init__(self, service: CalculatorService) -> None:
        """Initialize the GUI with a CalculatorService instance.

        Args:
            service: CalculatorService instance for calculations
        """
        self.service = service
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.geometry("500x400")

        # Entry fields for operands
        self.operand_a_var = tk.StringVar()
        self.operand_b_var = tk.StringVar()

        # Result display
        self.result_var = tk.StringVar(value="")

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface with entry fields, buttons, and display."""
        # Frame for operand inputs
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(fill=tk.X)

        # Operand A
        tk.Label(input_frame, text="Operand A:").pack(anchor=tk.W)
        tk.Entry(input_frame, textvariable=self.operand_a_var, width=40).pack(fill=tk.X)

        # Operand B
        tk.Label(input_frame, text="Operand B:").pack(anchor=tk.W)
        tk.Entry(input_frame, textvariable=self.operand_b_var, width=40).pack(fill=tk.X)

        # Result display
        tk.Label(self.root, text="Result:", padx=10, pady=5).pack(anchor=tk.W)
        result_label = tk.Label(
            self.root,
            textvariable=self.result_var,
            bg="lightgray",
            height=2,
            padx=10,
            pady=5
        )
        result_label.pack(fill=tk.X, padx=10)

        # Frame for operation buttons
        button_frame = tk.Frame(self.root, padx=10, pady=10)
        button_frame.pack(fill=tk.BOTH, expand=True)

        self._create_operation_buttons(button_frame)

        # Clear button
        clear_frame = tk.Frame(self.root, padx=10, pady=5)
        clear_frame.pack(fill=tk.X)
        tk.Button(clear_frame, text="Clear", command=self._on_clear, width=20).pack()

    def _create_operation_buttons(self, parent: tk.Widget) -> None:
        """Create buttons for all operations from the Operation enum.

        Args:
            parent: Parent widget to place operation buttons in
        """
        operations = list(Operation)
        rows = (len(operations) + 3) // 4  # 4 columns

        for i, operation in enumerate(operations):
            row = i // 4
            col = i % 4

            btn = tk.Button(
                parent,
                text=operation.display_name(),
                command=lambda op=operation: self._on_operation_selected(op),
                width=10,
                height=2
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Configure grid weights for proper sizing
        for i in range(4):
            parent.columnconfigure(i, weight=1)
        for i in range(rows):
            parent.rowconfigure(i, weight=1)

    def _on_operation_selected(self, operation: Operation) -> None:
        """Handle operation button click.

        Args:
            operation: The Operation enum value selected
        """
        try:
            a = float(self.operand_a_var.get())
            b = float(self.operand_b_var.get())
            result = self.service.perform(operation, a, b)
            self._display_result(result)
        except ValueError:
            messagebox.showerror(
                "Input Error",
                "Please enter valid numbers for both operands"
            )
        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    def _on_equals_pressed(self) -> None:
        """Handle equals button press (reserved for future use)."""
        pass

    def _display_result(self, result) -> None:
        """Display the calculation result.

        Args:
            result: CalculationResult object to display
        """
        self.result_var.set(str(result))

    def _on_clear(self) -> None:
        """Clear all input fields and result display."""
        self.operand_a_var.set("")
        self.operand_b_var.set("")
        self.result_var.set("")

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()
