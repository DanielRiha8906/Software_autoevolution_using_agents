"""GUI application for the calculator using tkinter."""

import tkinter as tk
from tkinter import ttk, messagebox
import math
from datetime import datetime

from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from ..services.calculator_service import CalculatorService
from ..services.memory_store import MemoryStore


class GUIApplication:
    """Tkinter-based GUI for the calculator with tabbed interface."""

    def __init__(
        self, service: CalculatorService, memory_store: MemoryStore
    ) -> None:
        """Initialize the GUI application.

        Args:
            service: CalculatorService instance for calculations
            memory_store: MemoryStore instance for history management
        """
        self.service = service
        self.memory_store = memory_store

        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.geometry("800x600")

        # Display variable for the result (must be before tab setup)
        self.display_var = tk.StringVar(value="0")

        # Track the current operand and operation
        self.current_operand = None
        self.current_operation = None
        self.last_was_operation = False

        # Create the main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(side="top", fill="both", expand=True)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Create tabbed interface
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Standard mode tab
        self.standard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.standard_frame, text="Standard")
        self._setup_standard_tab()

        # Scientific mode tab
        self.scientific_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scientific_frame, text="Scientific")
        self._setup_scientific_tab()

        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History")
        self._setup_history_tab()

    def _setup_standard_tab(self) -> None:
        """Set up the standard calculator tab."""
        # Display
        display_frame = ttk.Frame(self.standard_frame)
        display_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(display_frame, text="Result:").pack(side="left")
        display_label = ttk.Label(
            display_frame,
            textvariable=self.display_var,
            font=("Arial", 16),
            background="white",
            relief="sunken",
        )
        display_label.pack(side="left", fill="x", expand=True, padx=5)

        # Button grid
        button_frame = ttk.Frame(self.standard_frame)
        button_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Standard operations
        standard_ops = [
            (Operation.ADD, "Add", "+"),
            (Operation.SUBTRACT, "Subtract", "−"),
            (Operation.MULTIPLY, "Multiply", "×"),
            (Operation.DIVIDE, "Divide", "÷"),
            (Operation.SQUARE, "Square", "x²"),
            (Operation.SQRT, "Sqrt", "√"),
            (Operation.POWER, "Power", "x^y"),
            (Operation.MODULO, "Modulo", "%"),
        ]

        for row, (op, label, symbol) in enumerate(standard_ops):
            col = row % 4
            actual_row = row // 4
            btn = tk.Button(
                button_frame,
                text=symbol,
                font=("Arial", 12),
                width=8,
                command=lambda operation=op: self._on_operation_click(operation),
            )
            btn.grid(row=actual_row, column=col, padx=2, pady=2, sticky="nsew")

        # Number buttons and equals
        control_frame = ttk.Frame(self.standard_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        number_frame = tk.Frame(control_frame)
        number_frame.pack(side="left", fill="x", expand=True)

        # Number pad 0-9
        for i in range(10):
            btn = tk.Button(
                number_frame,
                text=str(i),
                font=("Arial", 12),
                width=4,
                command=lambda num=i: self._on_number_click(num),
            )
            if i == 0:
                btn.grid(row=3, column=0, padx=2, pady=2, sticky="nsew")
            else:
                row = (i - 1) // 3
                col = (i - 1) % 3
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        # Decimal point
        decimal_btn = tk.Button(
            number_frame,
            text=".",
            font=("Arial", 12),
            width=4,
            command=self._on_decimal_click,
        )
        decimal_btn.grid(row=3, column=1, padx=2, pady=2, sticky="nsew")

        # Clear button
        clear_btn = tk.Button(
            number_frame,
            text="C",
            font=("Arial", 12),
            width=4,
            command=self._on_clear_click,
        )
        clear_btn.grid(row=3, column=2, padx=2, pady=2, sticky="nsew")

        # Equals button
        equals_btn = tk.Button(
            control_frame,
            text="=",
            font=("Arial", 12),
            width=8,
            command=self._on_equals_click,
        )
        equals_btn.pack(side="right", padx=2)

    def _setup_scientific_tab(self) -> None:
        """Set up the scientific calculator tab."""
        # Display
        display_frame = ttk.Frame(self.scientific_frame)
        display_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(display_frame, text="Result:").pack(side="left")
        display_label = ttk.Label(
            display_frame,
            textvariable=self.display_var,
            font=("Arial", 16),
            background="white",
            relief="sunken",
        )
        display_label.pack(side="left", fill="x", expand=True, padx=5)

        # Button grid
        button_frame = ttk.Frame(self.scientific_frame)
        button_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # All operations (standard + scientific)
        all_ops = [
            (Operation.ADD, "+"),
            (Operation.SUBTRACT, "−"),
            (Operation.MULTIPLY, "×"),
            (Operation.DIVIDE, "÷"),
            (Operation.SQUARE, "x²"),
            (Operation.SQRT, "√"),
            (Operation.POWER, "x^y"),
            (Operation.MODULO, "%"),
            (Operation.SIN, "sin"),
            (Operation.COS, "cos"),
            (Operation.TAN, "tan"),
            (Operation.LOG, "log"),
            (Operation.LN, "ln"),
            (Operation.EXP, "e^x"),
        ]

        for row, (op, symbol) in enumerate(all_ops):
            col = row % 4
            actual_row = row // 4
            btn = tk.Button(
                button_frame,
                text=symbol,
                font=("Arial", 11),
                width=8,
                command=lambda operation=op: self._on_operation_click(operation),
            )
            btn.grid(row=actual_row, column=col, padx=2, pady=2, sticky="nsew")

        # Number buttons and equals
        control_frame = ttk.Frame(self.scientific_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        number_frame = tk.Frame(control_frame)
        number_frame.pack(side="left", fill="x", expand=True)

        # Number pad 0-9
        for i in range(10):
            btn = tk.Button(
                number_frame,
                text=str(i),
                font=("Arial", 12),
                width=4,
                command=lambda num=i: self._on_number_click(num),
            )
            if i == 0:
                btn.grid(row=3, column=0, padx=2, pady=2, sticky="nsew")
            else:
                row = (i - 1) // 3
                col = (i - 1) % 3
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        # Decimal point
        decimal_btn = tk.Button(
            number_frame,
            text=".",
            font=("Arial", 12),
            width=4,
            command=self._on_decimal_click,
        )
        decimal_btn.grid(row=3, column=1, padx=2, pady=2, sticky="nsew")

        # Clear button
        clear_btn = tk.Button(
            number_frame,
            text="C",
            font=("Arial", 12),
            width=4,
            command=self._on_clear_click,
        )
        clear_btn.grid(row=3, column=2, padx=2, pady=2, sticky="nsew")

        # Equals button
        equals_btn = tk.Button(
            control_frame,
            text="=",
            font=("Arial", 12),
            width=8,
            command=self._on_equals_click,
        )
        equals_btn.pack(side="right", padx=2)

    def _setup_history_tab(self) -> None:
        """Set up the history tab with scrollable list."""
        # Frame for buttons
        button_frame = ttk.Frame(self.history_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        refresh_btn = tk.Button(
            button_frame,
            text="Refresh",
            command=self._refresh_history,
        )
        refresh_btn.pack(side="left", padx=2)

        clear_history_btn = tk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history,
        )
        clear_history_btn.pack(side="left", padx=2)

        # Scrollable frame for history
        scroll_frame = ttk.Frame(self.history_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")

        self.history_listbox = tk.Listbox(
            scroll_frame,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
            height=15,
        )
        self.history_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        # Load initial history
        self._refresh_history()

    def _on_number_click(self, num: int) -> None:
        """Handle number button click."""
        current = self.display_var.get()

        if current == "0" and num == 0:
            return

        if current == "0":
            self.display_var.set(str(num))
        else:
            self.display_var.set(current + str(num))

        self.last_was_operation = False

    def _on_decimal_click(self) -> None:
        """Handle decimal point button click."""
        current = self.display_var.get()

        if "." not in current:
            self.display_var.set(current + ".")
        self.last_was_operation = False

    def _on_clear_click(self) -> None:
        """Handle clear button click."""
        self.display_var.set("0")
        self.current_operand = None
        self.current_operation = None
        self.last_was_operation = False

    def _on_operation_click(self, operation: Operation) -> None:
        """Handle operation button click."""
        current_display = self.display_var.get()

        # Check if it's a unary operation
        if operation.is_unary():
            self._execute_unary_operation(operation)
        else:
            # Binary operation
            if self.current_operation is not None and not self.last_was_operation:
                # Execute the previous operation first
                self._execute_operation()

            self.current_operand = float(current_display)
            self.current_operation = operation
            self.last_was_operation = True

    def _on_equals_click(self) -> None:
        """Handle equals button click."""
        if self.current_operation is not None:
            self._execute_operation()

    def _execute_unary_operation(self, operation: Operation) -> None:
        """Execute a unary operation."""
        try:
            current_value = float(self.display_var.get())
            result = self.service.perform(operation, current_value)
            self.display_var.set(str(result.result))
            self.last_was_operation = False
        except (ValueError, ZeroDivisionError) as e:
            self.display_var.set("Error")
            self.last_was_operation = False

    def _execute_operation(self) -> None:
        """Execute the current operation."""
        if self.current_operation is None or self.current_operand is None:
            return

        try:
            b = float(self.display_var.get())
            result = self.service.perform(
                self.current_operation, self.current_operand, b
            )
            self.display_var.set(str(result.result))
            self.current_operand = None
            self.current_operation = None
            self.last_was_operation = False
        except (ValueError, ZeroDivisionError) as e:
            self.display_var.set("Error")
            self.current_operand = None
            self.current_operation = None
            self.last_was_operation = False

    def _refresh_history(self) -> None:
        """Refresh the history list."""
        self.history_listbox.delete(0, tk.END)

        entries = self.memory_store.retrieve()

        for entry in entries:
            line = self._format_history_entry(entry)
            self.history_listbox.insert(tk.END, line)

            # Highlight errors in red
            if entry.is_error():
                idx = self.history_listbox.size() - 1
                self.history_listbox.itemconfig(idx, {"bg": "lightcoral"})

    def _clear_history(self) -> None:
        """Clear the entire history."""
        if messagebox.askyesno(
            "Confirm",
            "Are you sure you want to clear all history?",
        ):
            # Clear storage by loading all entries and not storing them back
            # This is a limitation of the current storage model
            # For now, we just clear the display
            self.history_listbox.delete(0, tk.END)

    def _format_history_entry(self, entry: MemoryEntry) -> str:
        """Format a history entry for display."""
        if entry.is_error():
            return (
                f"ID {entry.entry_id} | {entry.operation.upper()} | "
                f"Error: {entry.error_message}"
            )
        else:
            operands_str = " ".join(str(o) for o in entry.operands)
            return (
                f"ID {entry.entry_id} | {entry.operation.upper()} {operands_str} "
                f"= {entry.result}"
            )

    def run(self) -> None:
        """Start the GUI application."""
        self.root.mainloop()
