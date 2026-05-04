import tkinter as tk
from tkinter import ttk
from typing import List, Optional
from datetime import datetime

from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_attempt_service import WorkflowAttemptService
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun


class WorkflowRunsGUIViewer:
    def __init__(
        self,
        run_service: WorkflowRunService,
        attempt_service: WorkflowAttemptService,
        root: Optional[tk.Tk] = None,
    ) -> None:
        self._run_service = run_service
        self._attempt_service = attempt_service
        self._root = root if root is not None else tk.Tk()
        self._treeview: Optional[ttk.Treeview] = None
        self._status_filter: Optional[ttk.Combobox] = None
        self._conclusion_filter: Optional[ttk.Combobox] = None
        self._current_runs: List[WorkflowRun] = []

    def run(self) -> None:
        """Launch the GUI window."""
        self._setup_window()
        self._create_widgets()
        self._populate_treeview(self._run_service.list_runs())
        self._root.mainloop()

    def _setup_window(self) -> None:
        """Initialize the tkinter window."""
        self._root.title("Workflow Runs Viewer")
        self._root.geometry("1200x600")

        # Configure style for failed run highlighting
        style = ttk.Style()
        style.configure("failed_run.Treeview", background="#ffcccc")

    def _create_widgets(self) -> None:
        """Build the GUI widgets."""
        # Filter frame
        filter_frame = ttk.Frame(self._root)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        # Status filter
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        status_options = ["All"] + [s.value for s in WorkflowStatus]
        self._status_filter = ttk.Combobox(
            filter_frame,
            values=status_options,
            state="readonly",
            width=15,
        )
        self._status_filter.set("All")
        self._status_filter.pack(side=tk.LEFT, padx=5)
        self._status_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Conclusion filter
        ttk.Label(filter_frame, text="Conclusion:").pack(side=tk.LEFT, padx=5)
        conclusion_options = ["All"] + [c.value for c in WorkflowConclusion]
        self._conclusion_filter = ttk.Combobox(
            filter_frame,
            values=conclusion_options,
            state="readonly",
            width=15,
        )
        self._conclusion_filter.set("All")
        self._conclusion_filter.pack(side=tk.LEFT, padx=5)
        self._conclusion_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Clear filters button
        clear_button = ttk.Button(
            filter_frame,
            text="Clear Filters",
            command=self._clear_filters,
        )
        clear_button.pack(side=tk.LEFT, padx=10)

        # Treeview frame with scrollbar
        tree_frame = ttk.Frame(self._root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        # Treeview
        columns = ("ID", "Workflow", "Branch", "Status", "Conclusion", "Duration", "Attempts", "Created")
        self._treeview = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        # Configure scrollbars
        vsb.config(command=self._treeview.yview)
        hsb.config(command=self._treeview.xview)

        # Define column headings and widths
        self._treeview.heading("#0", text="")
        self._treeview.column("#0", width=0, stretch=tk.NO)

        column_widths = {
            "ID": 120,
            "Workflow": 150,
            "Branch": 120,
            "Status": 100,
            "Conclusion": 120,
            "Duration": 100,
            "Attempts": 80,
            "Created": 150,
        }

        for col in columns:
            self._treeview.heading(col, text=col)
            self._treeview.column(col, width=column_widths.get(col, 100), anchor=tk.W)

        # Configure tags for failed runs
        self._treeview.tag_configure("failed_run", background="#ffcccc")

        # Pack treeview and scrollbars
        self._treeview.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _populate_treeview(self, runs: List[WorkflowRun]) -> None:
        """Fill treeview with data."""
        if self._treeview is None:
            return

        # Clear existing items
        for item in self._treeview.get_children():
            self._treeview.delete(item)

        self._current_runs = runs

        for run in runs:
            attempt_count = self._get_attempt_count(run.id)
            tags = ()
            if run.is_failed():
                tags = ("failed_run",)

            self._treeview.insert(
                "",
                tk.END,
                values=(
                    run.id[:8],
                    run.workflow_name,
                    run.branch,
                    run.status.value,
                    self._format_conclusion(run.conclusion),
                    self._format_duration(run.duration_seconds),
                    str(attempt_count),
                    self._format_timestamp(run.created_at),
                ),
                tags=tags,
            )

    def _get_attempt_count(self, run_id: str) -> int:
        """Get the number of attempts for a run."""
        attempts = self._attempt_service.filter_by_run_id(run_id)
        return len(attempts)

    def _apply_filters(self) -> None:
        """Filter runs by status and/or conclusion."""
        if self._status_filter is None or self._conclusion_filter is None:
            return

        status_filter = self._status_filter.get()
        conclusion_filter = self._conclusion_filter.get()

        filtered_runs = self._run_service.list_runs()

        # Filter by status
        if status_filter != "All":
            filtered_runs = [
                r for r in filtered_runs
                if r.status.value == status_filter
            ]

        # Filter by conclusion
        if conclusion_filter != "All":
            filtered_runs = [
                r for r in filtered_runs
                if r.conclusion and r.conclusion.value == conclusion_filter
            ]

        self._populate_treeview(filtered_runs)

    def _clear_filters(self) -> None:
        """Reset filter dropdowns to 'All'."""
        if self._status_filter is not None:
            self._status_filter.set("All")
        if self._conclusion_filter is not None:
            self._conclusion_filter.set("All")
        self._populate_treeview(self._run_service.list_runs())

    def _on_filter_changed(self, event: Optional[tk.Event] = None) -> None:
        """Callback for filter dropdown changes."""
        self._apply_filters()

    def _format_duration(self, seconds: float) -> str:
        """Format duration as decimal string."""
        return f"{seconds:.2f}s"

    def _format_conclusion(self, conclusion: Optional[WorkflowConclusion]) -> str:
        """Format conclusion value or return dash for None."""
        if conclusion is None:
            return "—"
        return conclusion.value

    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime as ISO string."""
        return dt.isoformat()

    def _highlight_failed_rows(self) -> None:
        """Mark failed runs with a tag for highlighting."""
        if self._treeview is None:
            return

        for item in self._treeview.get_children():
            # Get the run from current_runs by matching values
            values = self._treeview.item(item, "values")
            if not values:
                continue

            # Find the corresponding run
            run_id = values[0]
            run = next(
                (r for r in self._current_runs if r.id.startswith(run_id)),
                None,
            )

            if run and run.is_failed():
                self._treeview.item(item, tags=("failed_run",))


def run_gui(
    run_service: WorkflowRunService,
    attempt_service: WorkflowAttemptService,
) -> None:
    """Entry point for launching the GUI viewer."""
    viewer = WorkflowRunsGUIViewer(run_service, attempt_service)
    viewer.run()
