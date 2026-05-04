import tkinter as tk
from tkinter import ttk, messagebox
import sys
from typing import TYPE_CHECKING, Optional

from ..models.operation import Operation
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService
from ..protocols import CalculatorUI

if TYPE_CHECKING:
    from ..services.query_service import QueryService
    from ..services.statistics_service import StatisticsService


class CalculatorGUI(CalculatorUI):
    """Graphical user interface for the calculator using tkinter.

    Provides a GUI for performing calculations with buttons for operations,
    a display area, and a scrollable history list.
    """

    _STANDARD_OPERATIONS: list[tuple[Operation, str]] = [
        (Operation.ADD, "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE, "Divide"),
        (Operation.SQUARE, "Square"),
        (Operation.SQRT, "Square root"),
        (Operation.POWER, "Power"),
        (Operation.MODULO, "Modulo"),
    ]

    _SCIENTIFIC_OPERATIONS: list[tuple[Operation, str]] = [
        (Operation.ADD, "Add"),
        (Operation.SUBTRACT, "Subtract"),
        (Operation.MULTIPLY, "Multiply"),
        (Operation.DIVIDE, "Divide"),
        (Operation.SQUARE, "Square"),
        (Operation.SQRT, "Square root"),
        (Operation.POWER, "Power"),
        (Operation.MODULO, "Modulo"),
        (Operation.SIN, "Sine"),
        (Operation.COS, "Cosine"),
        (Operation.TAN, "Tangent"),
        (Operation.LOG, "Logarithm (base 10)"),
        (Operation.LN, "Natural logarithm"),
        (Operation.EXP, "Exponential (e^x)"),
    ]

    def __init__(
        self,
        service: CalculatorService,
        query_service: Optional["QueryService"] = None,
        statistics_service: Optional["StatisticsService"] = None,
        memory_service: Optional[MemoryService] = None,
        scientific_mode: bool = False,
    ) -> None:
        self.service = service
        self.query_service = query_service
        self.statistics_service = statistics_service
        self.memory_service = memory_service
        self.scientific_mode = scientific_mode

        self.root: Optional[tk.Tk] = None
        self.display: Optional[ttk.Entry] = None
        self.display_var: Optional[tk.StringVar] = None
        self.input_var: Optional[tk.StringVar] = None
        self.history_listbox: Optional[tk.Listbox] = None

        # Variables to store input state
        self.operand_a = 0.0
        self.operand_b = 0.0
        self.selected_operation: Optional[Operation] = None
        self.input_buffer = ""
        self.operation_complete = False

    def _setup_ui(self) -> None:
        """Set up the GUI components."""
        if self.root is None:
            return

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Display area
        display_frame = ttk.LabelFrame(main_frame, text="Display", padding="5")
        display_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        display_frame.columnconfigure(0, weight=1)

        self.display_var = tk.StringVar(value="0")
        self.display = ttk.Entry(
            display_frame,
            textvariable=self.display_var,
            font=("Arial", 20),
            state="readonly",
            justify="right",
        )
        self.display.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Operations frame
        operations = (
            self._SCIENTIFIC_OPERATIONS
            if self.scientific_mode
            else self._STANDARD_OPERATIONS
        )
        ops_frame = ttk.LabelFrame(main_frame, text="Operations", padding="5")
        ops_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        cols = 4
        for idx, (operation, label) in enumerate(operations):
            row = idx // cols
            col = idx % cols
            btn = ttk.Button(
                ops_frame,
                text=label,
                command=lambda op=operation: self._on_operation(op),
            )
            btn.grid(row=row, column=col, sticky=(tk.W, tk.E), padx=2, pady=2)
            ops_frame.columnconfigure(col, weight=1)

        # Input area with number buttons
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="5")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(1, weight=1)

        # Number input entry
        input_subframe = ttk.Frame(input_frame)
        input_subframe.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        input_subframe.columnconfigure(1, weight=1)

        ttk.Label(input_subframe, text="Number:").grid(row=0, column=0, padx=5)
        self.input_var = tk.StringVar(value="")
        input_entry = ttk.Entry(input_subframe, textvariable=self.input_var, font=("Arial", 14))
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # Button area
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        button_frame.columnconfigure(0, weight=1)
        button_frame.rowconfigure(0, weight=1)

        # Number pad
        number_pad_frame = ttk.Frame(button_frame)
        number_pad_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 0-9 buttons
        for i in range(10):
            row = (9 - i) // 3
            col = (9 - i) % 3
            btn = ttk.Button(
                number_pad_frame,
                text=str(i),
                command=lambda digit=i: self._on_digit(digit),
                width=3,
            )
            btn.grid(row=row, column=col, padx=2, pady=2)

        # Decimal point
        decimal_btn = ttk.Button(
            number_pad_frame,
            text=".",
            command=self._on_decimal,
            width=3,
        )
        decimal_btn.grid(row=3, column=0, padx=2, pady=2)

        # Clear and Delete buttons
        clear_btn = ttk.Button(number_pad_frame, text="Clear", command=self._on_clear)
        clear_btn.grid(row=3, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))

        delete_btn = ttk.Button(number_pad_frame, text="Del", command=self._on_delete)
        delete_btn.grid(row=3, column=2, padx=2, pady=2, sticky=(tk.W, tk.E))

        # Calculate button
        calc_btn = ttk.Button(
            button_frame,
            text="Calculate",
            command=self._on_calculate,
        )
        calc_btn.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # History area
        history_frame = ttk.LabelFrame(main_frame, text="History", padding="5")
        history_frame.grid(
            row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        # Scrollable history list
        scrollbar = ttk.Scrollbar(history_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.history_listbox = tk.Listbox(
            history_frame,
            yscrollcommand=scrollbar.set,
            font=("Courier", 9),
            height=8,
        )
        self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.history_listbox.yview)

        # Refresh history button
        refresh_btn = ttk.Button(
            history_frame,
            text="Refresh History",
            command=self._refresh_history,
        )
        refresh_btn.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def _on_digit(self, digit: int) -> None:
        """Handle digit button press."""
        self.input_buffer += str(digit)
        if self.input_var:
            self.input_var.set(self.input_buffer)

    def _on_decimal(self) -> None:
        """Handle decimal point button press."""
        if "." not in self.input_buffer:
            self.input_buffer += "."
            if self.input_var:
                self.input_var.set(self.input_buffer)

    def _on_clear(self) -> None:
        """Clear the input buffer."""
        self.input_buffer = ""
        if self.input_var:
            self.input_var.set("")
        self.operand_a = 0.0
        self.operand_b = 0.0
        self.selected_operation = None
        self.operation_complete = False
        if self.display_var:
            self.display_var.set("0")

    def _on_delete(self) -> None:
        """Delete the last character from input buffer."""
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]
            if self.input_var:
                self.input_var.set(self.input_buffer)

    def _on_operation(self, operation: Operation) -> None:
        """Handle operation button press."""
        # Scientific operations need only one operand
        scientific_ops = {
            Operation.SIN,
            Operation.COS,
            Operation.TAN,
            Operation.LOG,
            Operation.LN,
            Operation.EXP,
        }

        try:
            # If we have a selected operation and new input, calculate intermediate result
            if (
                self.selected_operation is not None
                and self.input_buffer
                and not self.operation_complete
            ):
                self.operand_b = float(self.input_buffer)
                result = self.service.perform(self.selected_operation, self.operand_a, self.operand_b)
                self.operand_a = result.result
                if self.display_var:
                    self.display_var.set(str(result.result))
                self.input_buffer = ""
                if self.input_var:
                    self.input_var.set("")
            elif self.input_buffer:
                # Store first operand
                self.operand_a = float(self.input_buffer)
                self.input_buffer = ""
                if self.input_var:
                    self.input_var.set("")
            elif self.operation_complete and self.selected_operation != operation:
                # Switch operation without recalculating
                pass

            self.selected_operation = operation

            # For scientific operations, calculate immediately
            if operation in scientific_ops:
                if self.operand_a == 0.0:
                    messagebox.showerror(
                        "Error", "Please enter a number first"
                    )
                    self.selected_operation = None
                    return

                try:
                    result = self.service.perform(operation, self.operand_a, 0.0)
                    self.operand_a = result.result
                    if self.display_var:
                        self.display_var.set(str(result.result))
                    self.input_buffer = ""
                    if self.input_var:
                        self.input_var.set("")
                    self.operation_complete = True
                    self._refresh_history()
                except ValueError as exc:
                    messagebox.showerror("Error", str(exc))
                    self.selected_operation = None
                    self.operation_complete = False

        except ValueError as exc:
            messagebox.showerror("Error", f"Invalid input: {exc}")
            self.selected_operation = None

    def _on_calculate(self) -> None:
        """Handle calculate button press."""
        if self.selected_operation is None:
            messagebox.showwarning("Warning", "Please select an operation first")
            return

        scientific_ops = {
            Operation.SIN,
            Operation.COS,
            Operation.TAN,
            Operation.LOG,
            Operation.LN,
            Operation.EXP,
        }

        if self.selected_operation in scientific_ops:
            # Already calculated when operation was selected
            return

        if not self.input_buffer:
            messagebox.showwarning("Warning", "Please enter a number")
            return

        try:
            self.operand_b = float(self.input_buffer)
            result = self.service.perform(
                self.selected_operation, self.operand_a, self.operand_b
            )
            if self.display_var:
                self.display_var.set(str(result.result))
            self.operand_a = result.result
            self.input_buffer = ""
            if self.input_var:
                self.input_var.set("")
            self.selected_operation = None
            self.operation_complete = True
            self._refresh_history()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))

    def _refresh_history(self) -> None:
        """Refresh the history list with latest calculations."""
        if self.history_listbox is None:
            return

        self.history_listbox.delete(0, tk.END)

        if self.memory_service is None:
            return

        try:
            entries = self.memory_service.retrieve()
            for entry in entries:
                if entry.success:
                    display_text = (
                        f"{entry.operation_name.upper()} "
                        f"{entry.operand_a} {entry.operand_b} = {entry.result}"
                    )
                else:
                    display_text = (
                        f"{entry.operation_name.upper()} "
                        f"{entry.operand_a} {entry.operand_b} "
                        f"[ERROR: {entry.error_message}]"
                    )
                self.history_listbox.insert(tk.END, display_text)
        except Exception as exc:
            messagebox.showerror("Error loading history", str(exc))

    def run_interactive(self) -> None:
        """Run the GUI in interactive mode."""
        if self.root is None:
            self.root = tk.Tk()
            self.root.title("Calculator")
            self.root.geometry("700x600")
            self._setup_ui()
        self._refresh_history()
        self.root.mainloop()

    def run_command(self, operation_str: str, a: float, b: float) -> None:
        """Run a single calculation command.

        For GUI, this starts the interactive mode and pre-fills the operation.
        """
        # GUI is inherently interactive, so just run it normally
        self.run_interactive()
