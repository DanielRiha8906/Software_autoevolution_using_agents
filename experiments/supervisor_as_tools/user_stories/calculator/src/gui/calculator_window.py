"""Main calculator window and GUI application."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import TYPE_CHECKING

from ..models.memory_entry import MemoryEntry
from .constants import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    MIN_WIDTH,
    MIN_HEIGHT,
    WINDOW_TITLE,
    COLOR_BG,
    COLOR_FG,
    COLOR_DISPLAY_BG,
    COLOR_ERROR_BG,
    COLOR_ERROR_FG,
    COLOR_SUCCESS_BG,
    FONT_FAMILY,
    BUTTON_FONT_SIZE,
    DISPLAY_FONT_SIZE,
    PADDING_STANDARD,
    PADDING_SMALL,
    STANDARD_OPERATIONS,
    SCIENTIFIC_OPERATIONS,
    ALL_OPERATIONS,
    OPERATION_DISPLAY,
)
from .components import NumberInput, OperationSelector, HistoryEntry, FilterPanel

if TYPE_CHECKING:
    from ..services.memory_service import MemoryService


class CalculatorWindow:
    """Main tkinter calculator GUI application."""

    def __init__(self, memory_service: "MemoryService") -> None:
        self.memory_service = memory_service
        self.scientific_mode = False
        self.current_entries: list[MemoryEntry] = []

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.config(bg=COLOR_BG)

        self._build_menu()
        self._build_ui()
        self._load_history()

    def _build_menu(self) -> None:
        """Build the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Memory", command=self._on_export_memory)
        file_menu.add_command(label="Import Memory", command=self._on_import_memory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        self.mode_var = tk.StringVar(value="Standard")
        view_menu.add_radiobutton(
            label="Standard Mode",
            variable=self.mode_var,
            value="Standard",
            command=self._on_mode_changed,
        )
        view_menu.add_radiobutton(
            label="Scientific Mode",
            variable=self.mode_var,
            value="Scientific",
            command=self._on_mode_changed,
        )

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        # Calculator frame (left side)
        calc_frame = ttk.LabelFrame(main_frame, text="Calculator", padding=PADDING_STANDARD)
        calc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=PADDING_SMALL)

        # Operation selector
        operations = STANDARD_OPERATIONS if not self.scientific_mode else ALL_OPERATIONS
        self.operation_selector = OperationSelector(calc_frame, operations)
        self.operation_selector.pack(fill=tk.X, pady=PADDING_SMALL)

        # Number inputs
        self.operand_a_input = NumberInput(calc_frame, "Number A:")
        self.operand_a_input.pack(fill=tk.X, pady=PADDING_SMALL)

        self.operand_b_input = NumberInput(calc_frame, "Number B:")
        self.operand_b_input.pack(fill=tk.X, pady=PADDING_SMALL)

        # Calculate button
        calc_button = tk.Button(
            calc_frame,
            text="Calculate",
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            bg=COLOR_BG,
            fg=COLOR_FG,
            command=self._on_calculate,
            width=20,
        )
        calc_button.pack(pady=PADDING_STANDARD)

        # Result display
        result_frame = ttk.Frame(calc_frame)
        result_frame.pack(fill=tk.X, pady=PADDING_SMALL)

        tk.Label(
            result_frame,
            text="Result:",
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
        ).pack(side=tk.LEFT, padx=PADDING_SMALL)

        self.result_display = tk.Label(
            result_frame,
            text="",
            font=(FONT_FAMILY, DISPLAY_FONT_SIZE),
            bg=COLOR_DISPLAY_BG,
            fg=COLOR_FG,
            anchor="w",
            justify=tk.LEFT,
            width=25,
        )
        self.result_display.pack(side=tk.LEFT, padx=PADDING_SMALL)

        # Clear button
        clear_button = tk.Button(
            calc_frame,
            text="Clear",
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            bg=COLOR_BG,
            fg=COLOR_FG,
            command=self._on_clear,
            width=20,
        )
        clear_button.pack(pady=PADDING_SMALL)

        # History frame (right side)
        history_frame = ttk.LabelFrame(main_frame, text="History", padding=PADDING_STANDARD)
        history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=PADDING_SMALL)

        # Filter panel
        self.filter_panel = FilterPanel(
            history_frame,
            ALL_OPERATIONS,
            on_filter_changed=self._on_filter_changed,
        )
        self.filter_panel.pack(fill=tk.X, pady=PADDING_SMALL)

        # History listbox with scrollbar
        history_container = ttk.Frame(history_frame)
        history_container.pack(fill=tk.BOTH, expand=True, pady=PADDING_SMALL)

        scrollbar = ttk.Scrollbar(history_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(
            history_container,
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            yscrollcommand=scrollbar.set,
            height=20,
        )
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        self.history_listbox.bind("<Double-Button-1>", self._on_history_double_click)

        # Clear history button
        clear_history_button = tk.Button(
            history_frame,
            text="Clear All History",
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            bg=COLOR_BG,
            fg=COLOR_FG,
            command=self._on_clear_history_prompt,
        )
        clear_history_button.pack(pady=PADDING_SMALL)

    def _on_calculate(self) -> None:
        """Handle calculate button press."""
        operation = self.operation_selector.get()
        a = self.operand_a_input.get()
        b = self.operand_b_input.get()

        if a is None or b is None:
            messagebox.showerror("Input Error", "Please enter valid numbers for both operands.")
            return

        try:
            entry = self.memory_service.record(operation, a, b)
            self._display_result(entry)
            self._load_history()
        except Exception as exc:
            messagebox.showerror("Calculation Error", str(exc))

    def _display_result(self, entry: MemoryEntry) -> None:
        """Display a calculation result in the result display."""
        if entry.success:
            self.result_display.config(
                text=f"{entry.operation_name}({entry.operand_a}, {entry.operand_b}) = {entry.result}",
                bg=COLOR_DISPLAY_BG,
                fg=COLOR_FG,
            )
        else:
            self.result_display.config(
                text=f"[ERROR] {entry.error_message}",
                bg=COLOR_ERROR_BG,
                fg=COLOR_ERROR_FG,
            )

    def _on_clear(self) -> None:
        """Clear input fields and result display."""
        self.operand_a_input.clear()
        self.operand_b_input.clear()
        self.result_display.config(text="")

    def _load_history(self) -> None:
        """Load history from memory service and update display."""
        operation_filter, success_filter = self.filter_panel.get_filters()
        self.current_entries = self.memory_service.filter(operation_filter, success_filter)
        self._update_history_display()

    def _update_history_display(self) -> None:
        """Update the history listbox with current entries."""
        self.history_listbox.delete(0, tk.END)
        for entry in self.current_entries:
            display_text = self._format_entry_display(entry)
            self.history_listbox.insert(tk.END, display_text)
            # Add background color based on success/error
            index = self.history_listbox.size() - 1
            if entry.success:
                self.history_listbox.itemconfig(index, bg=COLOR_SUCCESS_BG)
            else:
                self.history_listbox.itemconfig(index, {"bg": COLOR_ERROR_BG, "fg": COLOR_ERROR_FG})

    def _format_entry_display(self, entry: MemoryEntry) -> str:
        """Format a MemoryEntry for display in the history list."""
        status_icon = "✓" if entry.success else "✗"
        time_str = f"[{entry.execution_time_ms:.2f}ms]"

        if entry.success:
            return f"{status_icon} {entry.operation_name}({entry.operand_a}, {entry.operand_b}) = {entry.result} {time_str}"
        else:
            return f"{status_icon} {entry.operation_name}({entry.operand_a}, {entry.operand_b}) [ERROR: {entry.error_message}] {time_str}"

    def _on_history_double_click(self, event: tk.Event) -> None:
        """Handle double-click on history entry."""
        selection = self.history_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index >= len(self.current_entries):
            return

        entry = self.current_entries[index]
        self._show_entry_details(entry)

    def _show_entry_details(self, entry: MemoryEntry) -> None:
        """Show detailed information about an entry in a popup."""
        details_window = tk.Toplevel(self.root)
        details_window.title("Entry Details")
        details_window.geometry("400x300")
        details_window.resizable(False, False)

        # Create text with entry details
        details_text = f"""Operation: {entry.operation_name}
Operand A: {entry.operand_a}
Operand B: {entry.operand_b}
Result: {entry.result if entry.success else "N/A"}
Status: {"Success" if entry.success else "Error"}
Error Message: {entry.error_message or "None"}
Execution Time: {entry.execution_time_ms:.4f} ms
Timestamp: {entry.timestamp}
Entry ID: {entry.entry_id}"""

        details_label = tk.Label(
            details_window,
            text=details_text,
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
            justify=tk.LEFT,
            anchor="nw",
        )
        details_label.pack(fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        close_button = tk.Button(
            details_window,
            text="Close",
            command=details_window.destroy,
            font=(FONT_FAMILY, BUTTON_FONT_SIZE),
        )
        close_button.pack(pady=PADDING_SMALL)

    def _on_filter_changed(self, operation: str | None, success: bool | None) -> None:
        """Handle filter panel changes."""
        self._load_history()

    def _on_mode_changed(self) -> None:
        """Handle mode change (Standard/Scientific)."""
        self.scientific_mode = self.mode_var.get() == "Scientific"
        operations = ALL_OPERATIONS if self.scientific_mode else STANDARD_OPERATIONS

        # Rebuild operation selector
        self.operation_selector.destroy()
        self.operation_selector = OperationSelector(
            self.operation_selector.master,
            operations,
        )
        self.operation_selector.pack(fill=tk.X, pady=PADDING_SMALL)
        self.operation_selector.tkraise()

    def _on_export_memory(self) -> None:
        """Handle export memory action."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            count = self.memory_service.export_memory_entries(file_path)
            messagebox.showinfo("Export Successful", f"Exported {count} entries to {file_path}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _on_import_memory(self) -> None:
        """Handle import memory action."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            # Ask if user wants to overwrite existing entries
            overwrite = messagebox.askyesno(
                "Import Options",
                "Overwrite existing entries with matching IDs?",
            )
            imported, skipped = self.memory_service.import_memory_entries(
                file_path, overwrite=overwrite
            )
            self._load_history()
            messagebox.showinfo(
                "Import Successful",
                f"Imported {imported} entries (skipped {skipped} invalid entries)",
            )
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc))

    def _on_clear_history_prompt(self) -> None:
        """Prompt user before clearing all history."""
        # This feature is intentionally limited - we only clear the display,
        # not the underlying storage, to preserve data integrity
        result = messagebox.askyesno(
            "Clear History Display",
            "Clear the history filters (reset to showing all entries)?",
        )
        if result:
            self.filter_panel.operation_var.set("All")
            self.filter_panel.success_var.set(False)
            self.filter_panel.error_var.set(False)
            self._load_history()

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()
