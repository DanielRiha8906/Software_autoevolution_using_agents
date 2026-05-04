import tkinter as tk
from tkinter import messagebox
from typing import Optional

from ..models.workflow_run import WorkflowRun
from ..services.workflow_run_service import WorkflowRunService
from .frames import DetailFrame, FilterFrame, ListFrame, EditFrame


class MainWindow:
    """Main window orchestration for GUI."""

    def __init__(self, root: tk.Tk, service: WorkflowRunService) -> None:
        self._root = root
        self._service = service
        self._root.title("GitHub Workflow Manager")
        self._root.geometry("1000x700")

        # Main container
        main_frame = tk.Frame(self._root)
        main_frame.pack(fill="both", expand=True)

        # Left panel: filters and list
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Filter frame
        self._filter_frame = FilterFrame(left_frame, self._on_filter_change)
        self._filter_frame.pack(fill="x")

        # List frame
        self._list_frame = ListFrame(left_frame, self._on_run_select)
        self._list_frame.pack(fill="both", expand=True, padx=0, pady=5)

        # Right panel: details and edit
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Detail frame
        self._detail_frame = DetailFrame(right_frame)
        self._detail_frame.pack(fill="both", expand=True)

        # Edit frame (overlay)
        self._edit_frame = EditFrame(right_frame, self._on_edit_save, self._on_edit_cancel)
        self._edit_frame.pack(fill="both", expand=True)

        # Initially hide edit frame
        self._edit_frame.pack_forget()

        # Button frame at bottom
        button_frame = tk.Frame(self._root)
        button_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(button_frame, text="Edit Selected", command=self._edit_selected).pack(side="left", padx=5)
        tk.Button(button_frame, text="Refresh", command=self._refresh).pack(side="left", padx=5)
        tk.Button(button_frame, text="Exit", command=self._root.quit).pack(side="right", padx=5)

        # Load initial data
        self._refresh()

    def _refresh(self) -> None:
        """Reload runs from service and apply filters."""
        self._on_filter_change()

    def _on_filter_change(self) -> None:
        """Callback when filters change."""
        try:
            filter_kwargs = self._filter_frame.get_filter_kwargs()
            runs = self._service.filter_runs(**filter_kwargs)
            self._list_frame.set_runs(runs)
            self._detail_frame.set_run(None)
        except Exception as e:
            messagebox.showerror("Filter Error", f"Error applying filters: {e}")

    def _on_run_select(self, run: WorkflowRun) -> None:
        """Callback when a run is selected from the list."""
        self._detail_frame.set_run(run)

    def _edit_selected(self) -> None:
        """Show the edit frame for the currently selected run."""
        run = self._detail_frame._run
        if run is None:
            messagebox.showwarning("No Selection", "Please select a run from the list.")
            return

        # Show edit frame and load run
        self._detail_frame.pack_forget()
        self._edit_frame.pack(fill="both", expand=True)
        self._edit_frame.set_run(run)

    def _on_edit_save(self, run: WorkflowRun) -> None:
        """Callback when edit is saved."""
        try:
            self._service.update_workflow_run(run)
            self._on_edit_cancel()
            self._refresh()
        except ValueError as e:
            # Error message is displayed in the EditFrame's status label
            messagebox.showerror("Save Error", f"Error updating run: {e}")

    def _on_edit_cancel(self) -> None:
        """Callback when edit is cancelled."""
        self._edit_frame.pack_forget()
        self._detail_frame.pack(fill="both", expand=True)
        self._detail_frame.set_run(self._detail_frame._run)

    def run(self) -> None:
        """Start the GUI event loop."""
        self._root.mainloop()
