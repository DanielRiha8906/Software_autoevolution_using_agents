import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService
from .dialogs import WorkflowRunDetailsDialog, WorkflowRunEditDialog


class WorkflowRunMainWindow:
    """Main GUI window for displaying and managing workflow runs."""

    def __init__(
        self,
        root: tk.Tk,
        service: WorkflowRunService,
        attempt_service: WorkflowRunAttemptService,
    ):
        """Initialize the main GUI window.

        Args:
            root: The tkinter root window
            service: WorkflowRunService instance for accessing runs
            attempt_service: WorkflowRunAttemptService instance for accessing attempts
        """
        self.root = root
        self.service = service
        self.attempt_service = attempt_service
        self.root.title("GitHub Workflow Manager - GUI")
        self.root.geometry("1200x600")

        # Filter state
        self._current_status_filter: Optional[WorkflowStatus] = None
        self._current_conclusion_filter: Optional[WorkflowConclusion] = None

        # Create UI components
        self._create_widgets()
        self._load_runs()

    def _create_widgets(self) -> None:
        """Create and layout all GUI components."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="Workflow Runs", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Filter section
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self._status_var = tk.StringVar(value="(All)")
        status_options = ["(All)"] + [s.value for s in WorkflowStatus]
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self._status_var,
            values=status_options,
            state="readonly",
            width=15,
        )
        status_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Conclusion:").pack(side=tk.LEFT, padx=5)
        self._conclusion_var = tk.StringVar(value="(All)")
        conclusion_options = ["(All)"] + [c.value for c in WorkflowConclusion]
        conclusion_combo = ttk.Combobox(
            filter_frame,
            textvariable=self._conclusion_var,
            values=conclusion_options,
            state="readonly",
            width=15,
        )
        conclusion_combo.pack(side=tk.LEFT, padx=5)

        apply_btn = ttk.Button(filter_frame, text="Apply Filters", command=self._apply_filters)
        apply_btn.pack(side=tk.LEFT, padx=5)

        # Treeview section
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scrollbars
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        columns = ("ID", "Workflow Name", "Branch", "Status", "Conclusion", "Duration (s)", "Attempts", "Created At")
        self._tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=tree_scroll.set,
            height=15,
        )
        tree_scroll.config(command=self._tree.yview)

        # Define column headings and widths
        self._tree.column("ID", width=80)
        self._tree.column("Workflow Name", width=150)
        self._tree.column("Branch", width=100)
        self._tree.column("Status", width=100)
        self._tree.column("Conclusion", width=120)
        self._tree.column("Duration (s)", width=100)
        self._tree.column("Attempts", width=80)
        self._tree.column("Created At", width=150)

        for col in columns:
            self._tree.heading(col, text=col)

        self._tree.pack(fill=tk.BOTH, expand=True)

        # Define tag for failed runs
        self._tree.tag_configure("failed", foreground="red")

        # Button section
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        view_btn = ttk.Button(button_frame, text="View Details", command=self._view_details)
        view_btn.pack(side=tk.LEFT, padx=5)

        edit_btn = ttk.Button(button_frame, text="Edit", command=self._edit_run)
        edit_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(button_frame, text="Delete", command=self._delete_run)
        delete_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = ttk.Button(button_frame, text="Refresh", command=self._refresh)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="Close", command=self.root.quit)
        close_btn.pack(side=tk.LEFT, padx=5)

        # Status bar
        self._status_label = ttk.Label(main_frame, text="", relief=tk.SUNKEN, anchor=tk.W)
        self._status_label.pack(fill=tk.X, pady=(10, 0))

    def _load_runs(self) -> None:
        """Load runs from service and populate treeview."""
        runs = self.service.list_runs()
        self._populate_treeview(runs)

    def _populate_treeview(self, runs: List[WorkflowRun]) -> None:
        """Populate treeview with runs and update status bar.

        Args:
            runs: List of WorkflowRun objects to display
        """
        # Clear existing items
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Populate with runs
        total_runs = len(self.service.list_runs())
        for run in runs:
            attempt_count = self._get_attempt_count(run)
            tags = ("failed",) if run.is_failed() else ()
            self._tree.insert(
                "",
                tk.END,
                values=(
                    run.id,
                    run.workflow_name,
                    run.branch,
                    run.status.value,
                    run.conclusion.value if run.conclusion else "-",
                    f"{run.duration_seconds:.2f}",
                    attempt_count,
                    run.created_at.isoformat(),
                ),
                tags=tags,
            )

        # Update status bar
        displayed = len(runs)
        filter_text = ""
        if self._current_status_filter or self._current_conclusion_filter:
            filters = []
            if self._current_status_filter:
                filters.append(f"status={self._current_status_filter.value}")
            if self._current_conclusion_filter:
                filters.append(f"conclusion={self._current_conclusion_filter.value}")
            filter_text = f" (Filtered by {', '.join(filters)})"

        self._status_label.config(text=f"Showing {displayed} of {total_runs} runs{filter_text}")

    def _get_attempt_count(self, run: WorkflowRun) -> int:
        """Get the number of attempts for a run.

        Args:
            run: The WorkflowRun to count attempts for

        Returns:
            The number of associated attempts, or 0 if the run ID cannot be converted to int
        """
        try:
            run_id_int = int(run.id)
            return len(self.attempt_service.get_attempts_for_run(run_id_int))
        except (ValueError, TypeError):
            return 0

    def _apply_filters(self) -> None:
        """Apply selected filters and refresh display."""
        status_value = self._status_var.get()
        conclusion_value = self._conclusion_var.get()

        # Parse status filter
        self._current_status_filter = None
        if status_value != "(All)":
            try:
                self._current_status_filter = WorkflowStatus(status_value)
            except ValueError:
                pass

        # Parse conclusion filter
        self._current_conclusion_filter = None
        if conclusion_value != "(All)":
            try:
                self._current_conclusion_filter = WorkflowConclusion(conclusion_value)
            except ValueError:
                pass

        # Apply filters using service
        runs = self.service.query(
            status=self._current_status_filter,
            conclusion=self._current_conclusion_filter,
        )

        self._populate_treeview(runs)

    def _refresh(self) -> None:
        """Reload runs from storage and reapply current filters."""
        # Reload from storage
        self.service = WorkflowRunService(self.service._storage)
        self.attempt_service = WorkflowRunAttemptService(self.attempt_service._storage)

        # Reapply filters
        self._apply_filters()

    def _get_selected_run(self) -> Optional[WorkflowRun]:
        """Get the currently selected run from treeview.

        Returns:
            The selected WorkflowRun, or None if no run is selected
        """
        selection = self._tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a workflow run")
            return None

        item = selection[0]
        values = self._tree.item(item, "values")
        run_id = values[0]

        return self.service.get_run_detail(run_id)

    def _view_details(self) -> None:
        """Show details dialog for selected run."""
        run = self._get_selected_run()
        if run:
            dialog = WorkflowRunDetailsDialog(self.root, run, self.attempt_service)
            self.root.wait_window(dialog.top)

    def _edit_run(self) -> None:
        """Show edit dialog for selected run and save changes."""
        run = self._get_selected_run()
        if run:
            dialog = WorkflowRunEditDialog(self.root, run)
            self.root.wait_window(dialog.top)

            if dialog.result:
                try:
                    self.service.replace_run(dialog.result)
                    messagebox.showinfo("Success", "Run updated successfully")
                    self._refresh()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update run: {e}")

    def _delete_run(self) -> None:
        """Delete the selected run after confirmation."""
        run = self._get_selected_run()
        if run:
            if messagebox.askyesno("Confirm Delete", f"Delete run {run.id}?"):
                if self.service.delete_run(run.id):
                    messagebox.showinfo("Success", "Run deleted successfully")
                    self._refresh()
                else:
                    messagebox.showerror("Error", "Failed to delete run")

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()
