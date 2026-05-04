import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from datetime import datetime

from .models.workflow_run import WorkflowRun
from .models.workflow_status import WorkflowStatus
from .models.workflow_conclusion import WorkflowConclusion
from .services.workflow_run_service import WorkflowRunService
from .services.attempt_service import AttemptService


class FilterModel:
    """Model for managing filter state and applying filters to runs."""

    def __init__(self):
        """Initialize filter model with default filter values."""
        self.status_filter: Optional[WorkflowStatus] = None
        self.conclusion_filter: Optional[WorkflowConclusion] = None

    def set_status(self, status_str: str) -> None:
        """Set status filter from string value.

        Args:
            status_str: Status string value or "All" to clear filter.
        """
        self.status_filter = None if status_str == "All" else WorkflowStatus(status_str)

    def set_conclusion(self, conclusion_str: str) -> None:
        """Set conclusion filter from string value.

        Args:
            conclusion_str: Conclusion string value or "All" to clear filter.
        """
        self.conclusion_filter = None if conclusion_str == "All" else WorkflowConclusion(conclusion_str)

    def apply(self, runs: List[WorkflowRun], attempt_service: AttemptService) -> List[WorkflowRun]:
        """Apply filters to workflow runs.

        Args:
            runs: List of workflow runs to filter.
            attempt_service: Service for querying attempt counts.

        Returns:
            Filtered list of runs.
        """
        return self._get_service().filter_runs(
            status=self.status_filter,
            conclusion=self.conclusion_filter,
        )

    def _get_service(self) -> WorkflowRunService:
        """Get service instance for filtering (placeholder for DI)."""
        # This is filled in by the view during initialization
        pass

    def reset(self) -> None:
        """Reset all filters to default."""
        self.status_filter = None
        self.conclusion_filter = None


class WorkflowRunViewerGUI:
    """GUI viewer for GitHub workflow runs using tkinter with sidebar filtering."""

    def __init__(self, root: tk.Tk, service: WorkflowRunService, attempt_service: AttemptService):
        """Initialize the GUI viewer.

        Args:
            root: The tkinter root window.
            service: WorkflowRunService instance.
            attempt_service: AttemptService instance.
        """
        self.root = root
        self.service = service
        self.attempt_service = attempt_service
        self.filter_model = FilterModel()

        self.root.title("Workflow Run Viewer")
        self.root.geometry("1400x700")
        self.root.minsize(1000, 500)

        # Initialize StringVar after root is properly set up
        self.status_var = tk.StringVar(value="All")
        self.conclusion_var = tk.StringVar(value="All")

        self._setup_ui()
        self._refresh_data()

    def _setup_ui(self) -> None:
        """Set up the user interface components with a sidebar layout."""
        # Create main container with sidebar and content area
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Create left sidebar for filters
        sidebar = ttk.LabelFrame(main_container, text="Filters", padding=12)
        sidebar.pack(side=tk.LEFT, fill=tk.BOTH, padx=8, pady=8, ipadx=5, ipady=5)

        # Status filter section
        ttk.Label(sidebar, text="Status", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        status_options = ["All"] + [s.value for s in WorkflowStatus]
        self.status_dropdown = ttk.Combobox(
            sidebar, textvariable=self.status_var, values=status_options, state="readonly", width=20
        )
        self.status_dropdown.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))
        self.status_dropdown.bind("<<ComboboxSelected>>", self._on_filter_change)

        # Conclusion filter section
        ttk.Label(sidebar, text="Conclusion", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        conclusion_options = ["All"] + [c.value for c in WorkflowConclusion]
        self.conclusion_dropdown = ttk.Combobox(
            sidebar, textvariable=self.conclusion_var, values=conclusion_options, state="readonly", width=20
        )
        self.conclusion_dropdown.pack(anchor=tk.W, fill=tk.X, pady=(0, 15))
        self.conclusion_dropdown.bind("<<ComboboxSelected>>", self._on_filter_change)

        # Buttons
        button_frame = ttk.Frame(sidebar)
        button_frame.pack(anchor=tk.W, fill=tk.X)
        ttk.Button(button_frame, text="Refresh", command=self._refresh_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Reset", command=self._reset_filters).pack(side=tk.LEFT)

        # Create right content area
        content = ttk.Frame(main_container)
        content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Create table frame
        table_frame = ttk.LabelFrame(content, text="Workflow Runs", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

        # Create treeview (table)
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Workflow", "Branch", "Status", "Conclusion", "Duration", "Attempts"),
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=25,
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Define column headings and widths
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("ID", anchor=tk.W, width=80)
        self.tree.column("Workflow", anchor=tk.W, width=150)
        self.tree.column("Branch", anchor=tk.W, width=90)
        self.tree.column("Status", anchor=tk.CENTER, width=100)
        self.tree.column("Conclusion", anchor=tk.CENTER, width=100)
        self.tree.column("Duration", anchor=tk.CENTER, width=90)
        self.tree.column("Attempts", anchor=tk.CENTER, width=70)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("ID", text="ID", anchor=tk.W)
        self.tree.heading("Workflow", text="Workflow", anchor=tk.W)
        self.tree.heading("Branch", text="Branch", anchor=tk.W)
        self.tree.heading("Status", text="Status", anchor=tk.CENTER)
        self.tree.heading("Conclusion", text="Conclusion", anchor=tk.CENTER)
        self.tree.heading("Duration", text="Duration (s)", anchor=tk.CENTER)
        self.tree.heading("Attempts", text="Attempts", anchor=tk.CENTER)

        # Configure tag for failed runs
        self.tree.tag_configure("failed", background="#ffcccc", foreground="black")
        self.tree.tag_configure("success", background="#ccffcc", foreground="black")
        self.tree.tag_configure("in_progress", background="#ffffcc", foreground="black")

        # Layout the scrollbars and tree
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    def _on_filter_change(self, event=None) -> None:
        """Handle filter change events."""
        self._refresh_data()

    def _reset_filters(self) -> None:
        """Reset all filters to 'All'."""
        self.status_var.set("All")
        self.conclusion_var.set("All")
        self.filter_model.reset()
        self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh the table with current data and applied filters."""
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get filter values
        status_filter = self.status_var.get()
        conclusion_filter = self.conclusion_var.get()

        # Update filter model
        self.filter_model.set_status(status_filter)
        self.filter_model.set_conclusion(conclusion_filter)

        # Apply filters using service
        runs = self.service.filter_runs(status=self.filter_model.status_filter, conclusion=self.filter_model.conclusion_filter)

        # Populate table
        for run in runs:
            # Get attempt count
            attempt_count = len(self.attempt_service.get_attempts_by_run_id(int(run.id) if run.id.isdigit() else run.id))

            # Format duration
            duration_str = f"{run.duration_seconds:.2f}"

            # Format conclusion
            conclusion_str = run.conclusion.value if run.conclusion else "—"

            # Determine tags for styling
            tags = self._get_row_tags(run)

            # Insert row into tree
            self.tree.insert(
                "",
                tk.END,
                values=(
                    run.id,
                    run.workflow_name,
                    run.branch,
                    run.status.value,
                    conclusion_str,
                    duration_str,
                    attempt_count,
                ),
                tags=tags,
            )

    def _get_row_tags(self, run: WorkflowRun) -> tuple:
        """Determine tags (styling) for a row based on run state.

        Args:
            run: WorkflowRun to evaluate.

        Returns:
            Tuple of tag strings to apply to the row.
        """
        if run.is_failed():
            return ("failed",)
        elif run.is_successful():
            return ("success",)
        elif run.is_running():
            return ("in_progress",)
        return ()


def run_gui(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    """Launch the GUI viewer for workflow runs.

    Args:
        service: WorkflowRunService instance.
        attempt_service: AttemptService instance.
    """
    root = tk.Tk()
    viewer = WorkflowRunViewerGUI(root, service, attempt_service)
    root.mainloop()
