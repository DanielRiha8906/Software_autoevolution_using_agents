import tkinter as tk
from tkinter import Listbox, Scrollbar, StringVar

from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from ..services.calculator_service import CalculatorService
from ..services.memory_service import MemoryService


class CalculatorGUI:
    def __init__(
        self,
        service: CalculatorService,
        memory_service: MemoryService | None = None,
    ) -> None:
        self.service = service
        self.memory_service = memory_service
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.geometry("600x700")

        self.operand_a_var = StringVar()
        self.operand_b_var = StringVar()
        self._current_operation: Operation | None = None
        self._unary_operations = {
            Operation.SQUARE,
            Operation.SQRT,
            Operation.SIN,
            Operation.COS,
            Operation.TAN,
            Operation.LOG10,
            Operation.LN,
            Operation.EXP,
        }

        self.result_text = None
        self.history_listbox = None
        self.status_label = None

        self.setup_ui()

    def setup_ui(self) -> None:
        # Input section
        input_frame = tk.Frame(self.root)
        input_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(input_frame, text="Operand A:").pack(anchor="w")
        tk.Entry(input_frame, textvariable=self.operand_a_var).pack(fill="x", pady=5)

        tk.Label(input_frame, text="Operand B:").pack(anchor="w")
        tk.Entry(input_frame, textvariable=self.operand_b_var).pack(fill="x", pady=5)

        # Operations section
        ops_frame = tk.LabelFrame(self.root, text="Operations", padx=10, pady=10)
        ops_frame.pack(padx=10, pady=10, fill="x")

        # Binary operations
        binary_frame = tk.Frame(ops_frame)
        binary_frame.pack(fill="x", pady=5)
        tk.Button(
            binary_frame,
            text="Add",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.ADD),
        ).pack(side="left", padx=2)
        tk.Button(
            binary_frame,
            text="Subtract",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.SUBTRACT),
        ).pack(side="left", padx=2)
        tk.Button(
            binary_frame,
            text="Multiply",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.MULTIPLY),
        ).pack(side="left", padx=2)
        tk.Button(
            binary_frame,
            text="Divide",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.DIVIDE),
        ).pack(side="left", padx=2)

        # Unary operations
        unary_frame = tk.Frame(ops_frame)
        unary_frame.pack(fill="x", pady=5)
        tk.Button(
            unary_frame,
            text="Square",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.SQUARE),
        ).pack(side="left", padx=2)
        tk.Button(
            unary_frame,
            text="Sqrt",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.SQRT),
        ).pack(side="left", padx=2)
        tk.Button(
            unary_frame,
            text="Power",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.POWER),
        ).pack(side="left", padx=2)
        tk.Button(
            unary_frame,
            text="Modulo",
            width=8,
            command=lambda: self._on_operation_button_click(Operation.MODULO),
        ).pack(side="left", padx=2)

        # Result section
        result_frame = tk.LabelFrame(self.root, text="Result", padx=10, pady=10)
        result_frame.pack(padx=10, pady=10, fill="both", expand=False)

        self.result_text = tk.Text(result_frame, height=3, width=50, state="disabled")
        self.result_text.pack(fill="both")

        self.status_label = tk.Label(result_frame, text="", fg="red")
        self.status_label.pack(anchor="w", pady=5)

        # History section
        if self.memory_service is not None:
            history_frame = tk.LabelFrame(self.root, text="History", padx=10, pady=10)
            history_frame.pack(padx=10, pady=10, fill="both", expand=True)

            scrollbar = Scrollbar(history_frame)
            scrollbar.pack(side="right", fill="y")

            self.history_listbox = Listbox(
                history_frame, yscrollcommand=scrollbar.set, height=10
            )
            self.history_listbox.pack(fill="both", expand=True)
            scrollbar.config(command=self.history_listbox.yview)
        else:
            history_frame = tk.LabelFrame(self.root, text="History", padx=10, pady=10)
            history_frame.pack(padx=10, pady=10, fill="both", expand=True)
            tk.Label(
                history_frame, text="(No history: memory service not available)"
            ).pack()

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=10, fill="x")

        tk.Button(button_frame, text="Calculate", command=self.perform_calculation).pack(
            side="left", padx=5
        )
        tk.Button(button_frame, text="Clear", command=self.clear_inputs).pack(
            side="left", padx=5
        )

        self.update_history()

    def _on_operation_button_click(self, operation: Operation) -> None:
        self._current_operation = operation
        self.status_label.config(text=f"Selected: {operation.display_name()}")

    def perform_calculation(self) -> None:
        if self._current_operation is None:
            self._display_error("Please select an operation")
            return

        try:
            operand_a = self._get_float_operand("A")
            if operand_a is None:
                return

            if self._is_unary_operation(self._current_operation):
                operand_b = 0.0
            else:
                operand_b = self._get_float_operand("B")
                if operand_b is None:
                    return

            result = self.service.perform(self._current_operation, operand_a, operand_b)
            self._display_result(result.result)
            self.status_label.config(text="Calculation successful")
            self.update_history()

        except ValueError as exc:
            self._display_error(str(exc))
            self.update_history()

    def _get_float_operand(self, operand_name: str) -> float | None:
        if operand_name == "A":
            value = self.operand_a_var.get().strip()
        else:
            value = self.operand_b_var.get().strip()

        if not value:
            self._display_error(f"Please enter operand {operand_name}")
            return None

        try:
            return float(value)
        except ValueError:
            self._display_error(f"Invalid operand {operand_name}: '{value}' is not a number")
            return None

    def _is_unary_operation(self, operation: Operation) -> bool:
        return operation in self._unary_operations

    def _display_result(self, result: float) -> None:
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", str(result))
        self.result_text.config(state="disabled")

    def _display_error(self, error_message: str) -> None:
        self.status_label.config(text=error_message, fg="red")

    def _format_history_entry(self, entry: MemoryEntry) -> str:
        if entry.success:
            return f"{entry.operation.upper()} ({entry.operand_a}, {entry.operand_b}) = {entry.result}"
        else:
            return f"ERROR: {entry.error_message}"

    def update_history(self) -> None:
        if self.history_listbox is None or self.memory_service is None:
            return

        self.history_listbox.delete(0, "end")
        entries = self.memory_service.retrieve_all()

        for entry in entries:
            self.history_listbox.insert("end", self._format_history_entry(entry))

        # Apply color-coding
        for i, entry in enumerate(entries):
            if entry.success:
                self.history_listbox.itemconfig(i, {"bg": "white"})
            else:
                self.history_listbox.itemconfig(i, {"bg": "#ffcccc"})

    def clear_inputs(self) -> None:
        self.operand_a_var.set("")
        self.operand_b_var.set("")
        self._current_operation = None
        self.status_label.config(text="")
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.config(state="disabled")

    def run(self) -> None:
        self.root.mainloop()
