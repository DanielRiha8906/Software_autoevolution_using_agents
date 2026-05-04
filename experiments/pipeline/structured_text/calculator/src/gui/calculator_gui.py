"""
Main graphical user interface for the OOP Calculator.

Provides tkinter-based window with tabs for standard and scientific modes,
input fields for operands, operation buttons, and displays for results,
memory entries, and statistics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from ..models.operation import Operation
from ..models.memory_entry import MemoryEntry
from ..protocols import CalculationService, MemoryService


class CalculatorGUI(tk.Tk):
    """
    Main GUI window for the calculator.

    Provides tabs for Standard and Scientific modes, input fields for operands,
    buttons for operations, and displays for memory entries and statistics.
    """

    # Standard mode operations
    _STANDARD_OPS = [
        Operation.ADD,
        Operation.SUBTRACT,
        Operation.MULTIPLY,
        Operation.DIVIDE,
        Operation.SQUARE,
        Operation.SQRT,
        Operation.POWER,
        Operation.MODULO,
    ]

    # Scientific mode operations
    _SCIENTIFIC_OPS = [
        Operation.SIN,
        Operation.COS,
        Operation.TAN,
        Operation.LOG,
        Operation.LN,
        Operation.EXP,
    ]

    def __init__(
        self,
        service: CalculationService,
        memory_service: Optional[MemoryService] = None,
    ) -> None:
        """
        Initialize the calculator GUI window.

        Args:
            service: CalculationService instance for performing calculations.
            memory_service: Optional MemoryService instance for storing and retrieving
                          memory entries. If not provided, memory features are disabled.
        """
        super().__init__()
        self.title("OOP Calculator - GUI")
        self.geometry("800x650")

        self.service = service
        self.memory_service = memory_service

        # Store reference to current operation for button click handling
        self._current_operation: Optional[Operation] = None

        # Create widgets
        self._create_widgets()

        # Initial display refresh
        if self.memory_service:
            self._refresh_memory_display()
            self._refresh_statistics_display()

    def _create_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for responsiveness
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="OOP Calculator",
            font=("Helvetica", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Create notebook (tabs) for Standard and Scientific modes
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        standard_tab = self._create_standard_mode_tab(notebook)
        scientific_tab = self._create_scientific_mode_tab(notebook)

        notebook.add(standard_tab, text="Standard")
        notebook.add(scientific_tab, text="Scientific")

        # Input fields for operands
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="5")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Operand A:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self._operand_a_var = tk.StringVar()
        self._operand_a_entry = ttk.Entry(input_frame, textvariable=self._operand_a_var, width=20)
        self._operand_a_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Label(input_frame, text="Operand B:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self._operand_b_var = tk.StringVar()
        self._operand_b_entry = ttk.Entry(input_frame, textvariable=self._operand_b_var, width=20)
        self._operand_b_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))

        # Calculate button
        calculate_btn = ttk.Button(
            input_frame,
            text="Calculate",
            command=self._on_calculate_button_click,
        )
        calculate_btn.grid(row=0, column=4, padx=(10, 0))

        # Result display
        result_frame = ttk.LabelFrame(main_frame, text="Result", padding="5")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)

        self._result_var = tk.StringVar(value="Enter operands and select an operation")
        result_label = ttk.Label(result_frame, textvariable=self._result_var, relief=tk.SUNKEN, padding="5")
        result_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Memory display
        memory_frame = ttk.LabelFrame(main_frame, text="Memory Entries", padding="5")
        memory_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        memory_frame.columnconfigure(0, weight=1)
        memory_frame.rowconfigure(0, weight=1)

        # Scrollbar for memory list
        scrollbar = ttk.Scrollbar(memory_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self._memory_listbox = tk.Listbox(
            memory_frame,
            height=8,
            yscrollcommand=scrollbar.set,
            font=("Courier", 9),
        )
        self._memory_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self._memory_listbox.yview)

        # Statistics display
        if self.memory_service:
            stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="5")
            stats_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            stats_frame.columnconfigure(0, weight=1)

            self._stats_text = tk.Text(
                stats_frame,
                height=4,
                width=80,
                state=tk.DISABLED,
                font=("Courier", 9),
            )
            self._stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))

        ttk.Button(button_frame, text="Clear Fields", command=self._on_clear_fields).pack(side=tk.LEFT, padx=5)

        if self.memory_service:
            ttk.Button(button_frame, text="Clear Memory", command=self._on_clear_memory).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Exit", command=self.quit).pack(side=tk.RIGHT, padx=5)

    def _create_standard_mode_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        """Create tab for standard operations."""
        frame = ttk.Frame(parent, padding="10")
        frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="button_col")

        # Create buttons for standard operations
        button_configs = [
            (0, 0, Operation.ADD),
            (0, 1, Operation.SUBTRACT),
            (0, 2, Operation.MULTIPLY),
            (0, 3, Operation.DIVIDE),
            (1, 0, Operation.SQUARE),
            (1, 1, Operation.SQRT),
            (1, 2, Operation.POWER),
            (1, 3, Operation.MODULO),
        ]

        for row, col, operation in button_configs:
            btn = ttk.Button(
                frame,
                text=operation.display_name(),
                command=lambda op=operation: self._on_operation_button_click(op),
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        return frame

    def _create_scientific_mode_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        """Create tab for scientific operations."""
        frame = ttk.Frame(parent, padding="10")
        frame.columnconfigure((0, 1, 2), weight=1, uniform="button_col")

        # Create buttons for scientific operations
        button_configs = [
            (0, 0, Operation.SIN),
            (0, 1, Operation.COS),
            (0, 2, Operation.TAN),
            (1, 0, Operation.LOG),
            (1, 1, Operation.LN),
            (1, 2, Operation.EXP),
        ]

        for row, col, operation in button_configs:
            btn = ttk.Button(
                frame,
                text=operation.display_name(),
                command=lambda op=operation: self._on_operation_button_click(op),
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        return frame

    def _on_operation_button_click(self, operation: Operation) -> None:
        """
        Handle operation button click.

        Args:
            operation: The Operation enum value selected.
        """
        self._current_operation = operation
        # Set result display to indicate selection
        op_name = operation.display_name()
        self._result_var.set(f"{op_name} selected - click Calculate")

    def _on_calculate_button_click(self) -> None:
        """Handle Calculate button click."""
        if self._current_operation is None:
            messagebox.showwarning("No Operation", "Please select an operation first")
            return

        # Get operands from input fields
        try:
            a = float(self._operand_a_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Operand A must be a number")
            return

        try:
            b = float(self._operand_b_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Operand B must be a number")
            return

        # Execute calculation
        self._execute_calculation(self._current_operation, a, b)

    def _execute_calculation(self, operation: Operation, a: float, b: float) -> None:
        """
        Execute a calculation and record to memory.

        Args:
            operation: The operation to perform.
            a: First operand.
            b: Second operand.
        """
        try:
            # Perform calculation
            result = self.service.perform(operation, a, b)

            # Display result
            self._display_result(result)

            # Record to memory if service is available
            if self.memory_service:
                entry = MemoryEntry(
                    operation=operation.value,
                    operand_a=a,
                    operand_b=b,
                    result=result.result,
                    success=True,
                    error_message=None,
                    execution_timestamp="",
                    execution_time_ms=result.execution_time_ms,
                    memory_entry_id=None,
                )
                self.memory_service.store(entry)

                # Refresh memory and statistics displays
                self._refresh_memory_display()
                self._refresh_statistics_display()

        except ValueError as e:
            self._show_error(str(e))

    def _display_result(self, result) -> None:
        """
        Display calculation result.

        Args:
            result: CalculationResult object to display.
        """
        # Format result for display
        a = int(result.operand_a) if result.operand_a == int(result.operand_a) else result.operand_a
        b = int(result.operand_b) if result.operand_b == int(result.operand_b) else result.operand_b
        r = int(result.result) if result.result == int(result.result) else result.result

        result_text = f"{result.operation.upper()}: {a}, {b} → {r} ({result.execution_time_ms:.2f}ms)"
        self._result_var.set(result_text)

    def _refresh_memory_display(self) -> None:
        """Refresh memory entries list."""
        if not self.memory_service:
            return

        # Clear listbox
        self._memory_listbox.delete(0, tk.END)

        # Retrieve all entries
        entries = self.memory_service.retrieve_all()

        # Populate listbox
        for i, entry in enumerate(entries, 1):
            display_text = f"{i}. {entry}"
            self._memory_listbox.insert(tk.END, display_text)

        # Scroll to bottom to show latest entry
        if entries:
            self._memory_listbox.see(tk.END)

    def _refresh_statistics_display(self) -> None:
        """Refresh statistics display."""
        if not self.memory_service:
            return

        # Compute statistics
        stats = self.memory_service.compute_statistics()

        # Format statistics for display
        stats_text = (
            f"Total: {stats.total_calculations} | "
            f"Errors: {stats.error_count} ({stats.error_percentage:.2f}%) | "
            f"Avg Time: {stats.average_execution_time_ms:.2f}ms | "
            f"Min: {stats.min_execution_time_ms:.2f}ms | "
            f"Max: {stats.max_execution_time_ms:.2f}ms"
        )

        # Update text widget
        self._stats_text.config(state=tk.NORMAL)
        self._stats_text.delete("1.0", tk.END)
        self._stats_text.insert("1.0", stats_text)
        self._stats_text.config(state=tk.DISABLED)

    def _show_error(self, message: str) -> None:
        """
        Display error dialog.

        Args:
            message: Error message to display.
        """
        messagebox.showerror("Calculation Error", message)
        self._result_var.set("Error in calculation. See message box above.")

    def _on_clear_fields(self) -> None:
        """Clear input fields and result display."""
        self._operand_a_var.set("")
        self._operand_b_var.set("")
        self._result_var.set("Enter operands and select an operation")
        self._current_operation = None
        self._operand_a_entry.focus()

    def _on_clear_memory(self) -> None:
        """Clear all memory entries (requires confirmation)."""
        if not self.memory_service:
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Clear Memory",
            "Are you sure you want to clear all memory entries? This cannot be undone.",
        )

        if response:
            # Note: Memory service doesn't have a clear method, so this would require
            # a new method to be added. For now, just show a message.
            messagebox.showinfo(
                "Not Implemented",
                "Memory clearing not yet implemented. Export memory to backup, then delete the file manually.",
            )

    def run(self) -> None:
        """Start the GUI event loop."""
        self.mainloop()
